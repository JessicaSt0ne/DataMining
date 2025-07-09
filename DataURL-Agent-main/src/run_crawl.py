# src/run_crawl.py

import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from src.config import (
    ENABLE_AUTO_DOWNLOAD,
    API_URL,
    DEFAULT_API_LIMIT_PER_REQUEST,
    DEFAULT_BASE_OUTPUT_DIR,
    DEFAULT_DOWNLOAD_WORKERS,
    DEFAULT_METADATA_FILENAME
)
from src import crawler      # 假设 crawler.py 完整保留
from src import downloader
from src import output_formatter

log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


def run_phase1(
    url: str,
    limit: int,
    output_dir: Path,
    workers: int,
    paper_ids: List[str] = None
):
    """
    Phase 1: 从 OpenReview 爬取 metadata 并并行下载 PDFs。
    """
    start_time = time.time()
    logger.info("--- Starting Phase 1: Crawl & Download ---")

    if paper_ids:
        logger.info(f"Processing {len(paper_ids)} manually specified paper IDs")
    else:
        logger.info(f"Target URL: '{url}'")
        if limit:
            logger.info(f"Limiting to {limit} papers.")

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Download workers: {workers}")

    if not ENABLE_AUTO_DOWNLOAD:
        logger.warning("ENABLE_AUTO_DOWNLOAD=False，跳过 Phase1 下载。请确保 data/papers/ 下已有 PDF。")
        return

    # --- Step 1: Fetch paper metadata via API ---
    logger.info("Fetching paper metadata from OpenReview API...")
    if paper_ids:
        notes_metadata: List[Dict[str, Any]] = crawler.fetch_notes_by_ids(paper_ids=paper_ids)
    else:
        notes_metadata: List[Dict[str, Any]] = crawler.fetch_notes_from_url(
            url=url, max_total=limit or DEFAULT_API_LIMIT_PER_REQUEST
        )

    if not notes_metadata:
        logger.warning("No paper metadata found. Exiting Phase1.")
        return

    logger.info(f"Fetched metadata for {len(notes_metadata)} papers.")

    # --- Step 2: Download PDFs in Parallel ---
    download_results = downloader.download_pdfs_parallel(
        notes_metadata=notes_metadata,
        base_output_dir=output_dir,
        max_workers=workers
    )

    # --- Step 3: Augment Metadata and Save ---
    logger.info("Augmenting metadata with local_pdf_path...")
    augmented_metadata = []
    for note in notes_metadata:
        note_id = note.get('id')
        if note_id:
            note['local_pdf_path'] = download_results.get(note_id)
            augmented_metadata.append(note)
        else:
            logger.warning(f"Note without ID, skipping: {note}")

    metadata_output_path = output_dir / DEFAULT_METADATA_FILENAME
    logger.info(f"Saving augmented metadata to {metadata_output_path}...")
    output_formatter.saveJson(str(metadata_output_path), augmented_metadata)

    end_time = time.time()
    logger.info(f"--- Phase 1 finished in {end_time - start_time:.2f} seconds ---")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Fetch metadata and PDFs from OpenReview."
    )
    parser.add_argument("--url", help="OpenReview URL", required=not ENABLE_AUTO_DOWNLOAD)
    parser.add_argument("--paper-ids", nargs="+", help="可选 paper ID 列表")
    parser.add_argument("--limit", type=int, default=None, help="最大论文数量")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path(DEFAULT_BASE_OUTPUT_DIR),
        help=f"输出根目录 (存 metadata、pdfs)；默认为 './{DEFAULT_BASE_OUTPUT_DIR}'"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=DEFAULT_DOWNLOAD_WORKERS,
        help=f"并发下载线程数 (默认为 {DEFAULT_DOWNLOAD_WORKERS})"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="开启 DEBUG 日志")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_phase1(
        url=args.url,
        limit=args.limit or DEFAULT_API_LIMIT_PER_REQUEST,
        output_dir=args.output,
        workers=args.workers,
        paper_ids=args.paper_ids
    )


if __name__ == "__main__":
    main()
