# run.py

import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# 确保把 src/ 目录加入到 Python 搜索路径
import sys
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from config import DATA_DIR, OUTPUT_DIR
from extractor import extract_all
from parser import is_likely_dataset_url
from validator import validate_list
from output_formatter import format_results_to_json

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline(workers: int = None):
    """
    一键跑通：对 data/papers/ 下的所有 PDF 提取 URL、打分过滤、校验可访问，
    并自动调用收费 API 生成一句话描述，最终输出题目要求的 JSON 结构。
    """
    # 1. 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"输出目录设为: {OUTPUT_DIR}")

    # 2. Step 1: 提取 PDF 中所有 URL
    logger.info(">> Step 1: 从 PDF 中抽取所有 URL ...")
    extracted: List[Dict[str, Any]] = extract_all(DATA_DIR)
    logger.info(f"  共抽取到 {len(extracted)} 条原始 URL 记录。")

    if not extracted:
        logger.warning("未在 data/papers/ 中抽取到任何 URL，退出。")
        return

    # 3. Step 2: 打分过滤
    logger.info(">> Step 2: 对候选链接进行打分过滤 ...")
    parsed_candidates: List[Dict[str, Any]] = []
    for item in extracted:
        url = item.get("url")
        context = item.get("context", "")
        pdf_id = item.get("pdf_id")
        eval_dict = is_likely_dataset_url(url, context)
        if not eval_dict["filter"]:
            parsed_candidates.append({
                "pdf_id": pdf_id,
                "url": url,
                "context": context
            })
    logger.info(f"  过滤后剩余 {len(parsed_candidates)} 条候选 URL。")

    if not parsed_candidates:
        logger.warning("没有满足打分阈值的候选链接，退出。")
        return

    # 4. Step 3: 并发校验可访问性
    logger.info(">> Step 3: 校验候选链接是否可访问 ...")
    validated: List[Dict[str, Any]] = validate_list(parsed_candidates)
    logger.info(f"  校验完成，共 {len(validated)} 条链接通过可访问性检查。")

    if not validated:
        logger.warning("没有可用的链接，退出。")
        return

    # 5. Step 4: 格式化并输出最终 JSON（含 API 调用生成描述）
    logger.info(">> Step 4: 格式化并输出最终 JSON ...")
    format_results_to_json(validated)
    logger.info(f">> 完成：结果已写入 {OUTPUT_DIR / 'formatted_results.json'}")


def main():
    parser = argparse.ArgumentParser(description="一键跑通：提取并校验 data/papers 下的所有 PDF URL 并生成描述")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="开启 DEBUG 日志"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=None,
        help="并发线程数（实际由 config.MAX_WORKERS 控制，只做日志提示）"
    )

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_pipeline(workers=args.workers)


if __name__ == "__main__":
    main()
