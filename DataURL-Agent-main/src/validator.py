# src/validator.py

import requests
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import URL_TIMEOUT, MAX_WORKERS

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)


def validate_url(url: str) -> bool:
    """
    只发一次 HEAD 请求检查状态码是否为 200。若 HEAD 不支持则发 GET。
    """
    try:
        resp = requests.head(url, timeout=URL_TIMEOUT, allow_redirects=True)
        if resp.status_code == 200:
            return True
        # 有些站点不支持 HEAD，尝试 GET
        resp = requests.get(url, timeout=URL_TIMEOUT)
        return resp.status_code == 200
    except Exception:
        return False


def validate_single_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    针对单个 parsed 数据 ({'pdf_id','url','context',...}) 做校验，
    并返回加上 'ai_decision' 信息的字典。
    """
    pdf_id = item.get("pdf_id")
    url    = item.get("url")
    context = item.get("context", "")

    ok = validate_url(url)
    if ok:
        ai_decision = {
            "is_intentional_link": True,
            "reason": "Status code 200"
        }
        return {
            "pdf_id": pdf_id,
            "url": url,
            "context": context,
            "ai_decision": ai_decision
        }
    else:
        return {
            "pdf_id": pdf_id,
            "url": url,
            "context": context,
            "ai_decision": {
                "is_intentional_link": False,
                "reason": "Status code !=200 or request failed"
            }
        }


def validate_list(parsed_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    对 parsed_list 中每个 {'pdf_id','url','context'} 做并发校验，
    返回只含“有效链接” 或者将所有链接都保留并把 ai_decision 写进去均可
    （这里保留所有，只不过 ai_decision.is_intentional_link=False 表示无效）。
    """
    results: List[Dict[str, Any]] = []
    seen = set()  # 用于去重 (pdf_id, url)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(validate_single_item, item): item for item in parsed_list
        }
        for fut in as_completed(futures):
            item = futures[fut]
            key = (item.get("pdf_id"), item.get("url"))
            if key in seen:
                continue
            seen.add(key)
            res = fut.result()
            # 只保留 is_intentional_link = True 的，若要保留所有可把下面条件删掉
            # if res["ai_decision"]["is_intentional_link"]:
            results.append(res)

    return results


if __name__ == "__main__":
    # 简单测试
    test_items = [
        {"pdf_id": "paper1", "url": "https://github.com", "context": "some context"},
        {"pdf_id": "paper1", "url": "https://nonexistent.example.com", "context": "x"},
    ]
    validated = validate_list(test_items)
    for v in validated:
        print(v)
