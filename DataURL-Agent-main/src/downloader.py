# src/extractor.py

import os
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

import fitz  # PyMuPDF

from src.config import DATA_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

URL_REGEX = re.compile(r'(https?://[^\s\)]+)')


def _clean_url(url: str) -> str:
    """
    Clean a URL string by removing trailing punctuation and parentheses artifacts.
    """
    while url and url[-1] in '.,;:!?\'")]}>':
        url = url[:-1]
    if url.endswith(')'):
        paren_open = url.rfind('(')
        if paren_open > 0:
            candidate = url[paren_open + 1:-1]
            if candidate.startswith("http"):
                url = candidate
    return url.strip()


def extract_urls_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    从单个 PDF 中提取所有形如 http(s)://... 的字符串及其上下文。

    返回格式：
    [
      {
        "pdf_id": "paper1",
        "page": 5,
        "url": "https://example.com/data.csv",
        "context": "URL 前后固定 window 大小的文本"
      },
      ...
    ]
    """
    results: List[Dict[str, Any]] = []
    pdf_id = pdf_path.stem

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.error(f"无法打开 PDF: {pdf_path}: {e}")
        return results

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if not text:
            continue

        for match in URL_REGEX.finditer(text):
            raw_url = match.group(1)
            url = _clean_url(raw_url)
            if not url or len(url) < 10:
                continue

            start, end = match.span()
            # 前后截取 CONTEXT_WINDOW_SIZE 字符
            from src.config import CONTEXT_WINDOW_SIZE
            left = text[max(0, start - CONTEXT_WINDOW_SIZE):start]
            right = text[end:min(len(text), end + CONTEXT_WINDOW_SIZE)]
            context = f"{left}{url}{right}".strip()

            results.append({
                "pdf_id": pdf_id,
                "page": page_num + 1,
                "url": url,
                "context": context
            })

    return results


def extract_all(data_dir: Path = DATA_DIR) -> List[Dict[str, Any]]:
    """
    遍历 data_dir 下的所有 .pdf 文件，调用 extract_urls_from_pdf 并合并结果。
    """
    all_results: List[Dict[str, Any]] = []
    for root, _, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_path = Path(root) / f
                logger.info(f"Extracting URLs from PDF: {pdf_path.name}")
                page_links = extract_urls_from_pdf(pdf_path)
                all_results.extend(page_links)
    logger.info(f"总计抽取到 {len(all_results)} 条候选 URL。")
    return all_results


if __name__ == "__main__":
    # 本地测试
    samples = extract_all()
    for item in samples[:10]:
        print(item)
