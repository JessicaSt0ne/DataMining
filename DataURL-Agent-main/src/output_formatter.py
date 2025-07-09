# src/output_formatter.py

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse
import requests  # 用收费 API 时要用 requests

from src.config import OUTPUT_DIR, FINAL_JSON_FILENAME

# 如果你把 API Key 写在 .env 里，下面这句会帮你读入
from dotenv import load_dotenv

load_dotenv()  # 确保把 .env 加载进来

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def infer_dataset_info(url: str) -> (str, str):
    """
    从 URL 中推断“数据集名称”和“类型”，不变如之前示例。
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if "huggingface.co/datasets/" in url:
        parts = path.split("/")
        dataset_name = parts[-1] if parts[-1] else parts[-2]
        dataset_type = "huggingface"
        return dataset_name, dataset_type

    if "github.com" in domain:
        dataset_name = path.split("/")[-1]
        if dataset_name.endswith(".git"):
            dataset_name = dataset_name[:-4]
        dataset_type = "git"
        return dataset_name, dataset_type

    if "kaggle.com" in domain:
        dataset_name = path.split("/")[-1]
        dataset_type = "kaggle"
        return dataset_name, dataset_type

    if "zenodo.org" in domain:
        dataset_name = f"zenodo_{path.split('/')[-1]}"
        dataset_type = "zenodo"
        return dataset_name, dataset_type

    if "figshare.com" in domain:
        dataset_name = f"figshare_{path.split('/')[-1]}"
        dataset_type = "figshare"
        return dataset_name, dataset_type

    if "dataverse.harvard.edu" in domain:
        dataset_name = path.split("/")[-1] or domain.replace(".", "_")
        dataset_type = "dataverse"
        return dataset_name, dataset_type

    prefix = domain.split(".")[0]
    raw_name = path.strip("/").replace("/", "_")
    if not raw_name:
        raw_name = prefix
    dataset_type = prefix
    dataset_name = raw_name
    return dataset_name, dataset_type


def qwen_by_api(prompt: str, engine_name: str = "chatgpt-4o-latest") -> str:
    """
    使用收费 API （中转地址 https://aigptx.top/v1/chat/completions）来生成一句描述。
    你需要把 API_KEY 填到环境变量里（OPENAI_API_KEY）。
    返回：AI 给出的“中文或英文”描述文本。
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.error("未在环境变量中找到 OPENAI_API_KEY，请先在 .env 写入 API Key。")
        return ""

    # 如果 engine_name 带了“#温度”，例如 "chatgpt-4o-latest#0.7"，就拆分
    if "#" in engine_name:
        temp = engine_name.split("#")
        engine = temp[0]
        temperature = float(temp[1])
        params = {
            "messages": [{"role": "user", "content": prompt}],
            "model": engine,
            "temperature": temperature,
        }
    else:
        params = {
            "messages": [{"role": "user", "content": prompt}],
            "model": engine_name,
        }

    headers = {
        "Authorization": "Bearer " + api_key
    }

    try:
        response = requests.post(
            "https://aigptx.top/v1/chat/completions",  # 中转地址，别改
            headers=headers,
            json=params,
            timeout=30
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"调用收费 API 失败: {e}")
        return ""

    res_json = response.json()
    message = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    # usage = res_json.get("usage", {})  # 如果需要统计 token 用量可以取出来
    return message.strip()


def generate_dataset_description(dataset_name: str, url: str, context: str) -> str:
    """
    调用 qwen_by_api，根据 dataset_name, url, context 三项生成一句话描述。
    也可以先用一个固定 prompt：
      “下面是一段论文摘录，包含一个指向数据集 {dataset_name} 的链接：\n\n{context}\n\n
       请你用一句话描述该数据集 {dataset_name} 的主要用途或特点。”
    如果收费 API 调用失败，就退回到截取 context 前 100 字。
    """
    prompt = (
        f"下面是一段从论文里提取的上下文，包含数据集链接：\n\n"
        f"{context}\n\n"
        f"请你判断这个链接指向的数据集“{dataset_name}”大致是干什么的，"
        f"并用一句话简要描述它。"
    )
    desc = qwen_by_api(prompt, engine_name="chatgpt-4o-latest#0.7")
    if not desc:
        # 如果 API 调用失败，就 fallback
        return (context[:100] + "…") if len(context) > 100 else context
    return desc


def format_results_to_json(validation_results: List[Dict[str, Any]]) -> None:
    """
    将校验后的所有结果按照 paper_id 分组，并输出题目要求的 JSON 文件。
    输出结构：
    {
      "paper1": {
        "HumanEval": ["huggingface", "openai/human-eval", "一句话描述"],
        "AlfWorld":  ["git",       "https://github.com/alfworld/alfworld.git", "一句话描述"]
      },
      "paper2": { … }
    }
    """
    final_json: Dict[str, Dict[str, List[str]]] = {}

    for result in validation_results:
        paper_id = result.get("pdf_id", "unknown")
        url = result.get("url", "")
        context = result.get("context", "")

        # 1. 推断数据集名称 和 类型
        dataset_name, dataset_type = infer_dataset_info(url)

        # 2. 用收费 API（qwen_by_api）生成一句话描述
        dataset_description = generate_dataset_description(dataset_name, url, context)

        # 3. 插入 final_json
        if paper_id not in final_json:
            final_json[paper_id] = {}

        # 如果同名数据集出现多次，只取第一次
        if dataset_name not in final_json[paper_id]:
            final_json[paper_id][dataset_name] = [
                dataset_type,
                url,
                dataset_description
            ]

    # 4. 写文件
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = OUTPUT_DIR / FINAL_JSON_FILENAME
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, ensure_ascii=False, indent=4)
        logger.info(f"最终的 formatted_results.json 已保存到: {output_path}")
    except IOError as e:
        logger.error(f"写入 JSON 文件 {output_path} 失败: {e}")
