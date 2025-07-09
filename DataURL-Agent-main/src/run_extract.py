# src/run_extract.py

import argparse
import logging
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from src.config import (
    ENABLE_AUTO_DOWNLOAD,
    DEFAULT_METADATA_FILENAME,
    DEFAULT_RESULTS_FILENAME,
    FINAL_JSON_FILENAME,
    OUTPUT_DIR,
    MAX_WORKERS
)
from src.extractor import extract_all
from src.parser import extract_candidate_links_from_text  # 注意 parser.py 中为此函数
from src.validator import validate_list
from src.output_formatter import format_results_to_json

log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


def run_phase2(
    metadata_path: Path,
    output_path: Path,
    workers: int
):
    """
    Phase 2: 从本地 PDF 提取候选 URL, 校验并输出最终 JSON。
    """
    start_time = time.time()
    logger.info("--- Starting Phase 2: Extract & Validate ---")
    logger.info(f"Loading metadata from: {metadata_path}")
    logger.info(f"Final results will be saved to: {output_path}")
    logger.info(f"Processing workers: {workers}")

    # --- Step 1: 如果在 Phase1 未执行下载，跳过 metadata 加载；否则读取 metadata 以获取本地 PDF 路径列表 ---
    pdf_paths: List[Path] = []
    if metadata_path.exists():
        logger.info("Phase1 已执行，尝试从 metadata 中读取 local_pdf_path 列表。")
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                all_metadata: List[Dict[str, Any]] = json.load(f)
            for entry in all_metadata:
                local_pdf = entry.get("local_pdf_path")
                if local_pdf:
                    pdf_paths.append(Path(local_pdf))
            logger.info(f"Found {len(pdf_paths)} PDFs from metadata.")
        except Exception as e:
            logger.error(f"Error reading metadata file: {e}")
            pdf_paths = []
    else:
        logger.info("Phase1 未执行或未生成 metadata，直接遍历 data/papers/ 目录下的 PDF。")
        from src.config import DATA_DIR
        for root, _, files in os.walk(DATA_DIR):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_paths.append(Path(root) / f)
        logger.info(f"Found {len(pdf_paths)} PDFs under data/papers/.")

    if not pdf_paths:
        logger.warning("没有找到任何 PDF 文件，退出 Phase2。")
        return

    # --- Step 2: 对每个 PDF 调用 extract_all() 得到纯文本中的候选 URL ---
    # 由于 extractor.extract_all() 本身会遍历整个 data/papers, 这里可以直接调用它：
    extracted = extract_all()  # 列表里的每条：{pdf_id, page, url, context}
    if not extracted:
        logger.warning("extract_all() 未抽取到任何 URL，退出 Phase2。")
        return

    # --- Step 3: 用 parse 阶段（extract_candidate_links_from_text），根据打分与过滤从纯文本中筛选候选链接 ---
    # 既然 extractor 已经输出了 url + context(前后 window 大小) ，我们可以直接把 extractor 的结果当作“全文抽取”阶段，
    # 但为了利用 parser 中更细粒度的上下文，我们应修改 extractor 或直接重用 parser.extract_candidate_links_from_text
    # 但此处简单做法：直接把 extractor 输出的 context 当作段落级上下文，再做打分过滤：
    parsed_candidates: List[Dict[str, Any]] = []
    logger.info("Running parser (多维度打分过滤) ...")
    for item in extracted:
        full_url = item["url"]
        paragraph = item.get("context", "")
        # 由于 extractor 已经给了 context，这里取 paragraph = context 即可
        evaluation = None
        # 将 parser 中的打分函数单独引入
        from src.parser import is_likely_dataset_url
        eval_dict = is_likely_dataset_url(full_url, paragraph)
        if not eval_dict["filter"]:
            parsed_candidates.append({
                "pdf_id": item["pdf_id"],
                "url": full_url,
                "context": paragraph,
                "page": item.get("page"),
                "evaluation": eval_dict
            })
    logger.info(f"Filtered down to {len(parsed_candidates)} candidate links after parser。")

    # --- 可选：将 parsed_candidates 写入中间文件 ---
    parsed_output_path = OUTPUT_DIR / DEFAULT_RESULTS_FILENAME
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        with open(parsed_output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_candidates, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved parsed candidates to: {parsed_output_path}")
    except Exception as e:
        logger.error(f"Error writing parsed candidates: {e}")

    # --- Step 4: 对候选链接并发校验 (validate_list) ---
    logger.info("Validating candidate URLs ...")
    validated_results = validate_list(parsed_candidates)
    logger.info(f"Validation completed. {len(validated_results)} links considered valid/intended.")

    # --- Step 5: 最终格式化输出 JSON ---
    format_results_to_json(validated_results)

    end_time = time.time()
    logger.info(f"--- Phase 2 finished in {end_time - start_time:.2f} seconds ---")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: Extract URLs from PDFs and validate."
    )
    parser.add_argument(
        "--metadata", type=Path,
        default=Path(DEFAULT_METADATA_FILENAME),
        help=f"Phase1 生成的 metadata 文件，默认: {DEFAULT_METADATA_FILENAME}"
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        default=Path(OUTPUT_DIR) / FINAL_JSON_FILENAME,
        help=f"最终 JSON 输出路径，默认: {OUTPUT_DIR}/{FINAL_JSON_FILENAME}"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=MAX_WORKERS,
        help=f"并发处理 PDF/URL 的线程数，默认: {MAX_WORKERS}"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="开启 DEBUG 日志")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_phase2(
        metadata_path=args.metadata,
        output_path=args.output,
        workers=args.workers
    )


if __name__ == "__main__":
    main()
