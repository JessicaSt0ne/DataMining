# src/parser.py

import re
import logging
from typing import List, Dict, Any, Optional

from src.config import CONTEXT_WINDOW_SIZE

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Regex 匹配 URL
URL_REGEX = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
)


def _clean_url(url: str) -> str:
    """
    清理 URL，去掉尾部标点及括号语法残留。
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


def extract_enhanced_context_from_text(full_text: str, match) -> Dict[str, Any]:
    """
    从纯文本中提取 URL 周边上下文与额外信息，包括：
      - standard_context: 前后固定 window 字符
      - full_sentence: 扩展到完整一句
      - paragraph: 若句子短，则扩展到段落（双换行分隔）
      - section_title: 匹配“Section X: 标题”或“第X节：标题”
      - reference_pattern: 匹配“available at”之类短语
      - page_hint: 匹配“page 12”之类
    """
    match_start, match_end = match.span()

    # —— 1. Extract complete sentence —— 
    sentence_start = match_start
    for i in range(match_start - 1, max(0, match_start - 500), -1):
        ch = full_text[i]
        if ch in ['.', '!', '?'] or (i > 0 and full_text[i-1:i+1] == "\n\n"):
            sentence_start = i + 1
            break
        if i == 0:
            sentence_start = 0

    sentence_end = match_end
    for i in range(match_end, min(len(full_text), match_end + 500)):
        ch = full_text[i]
        if ch in ['.', '!', '?'] or (i+1 < len(full_text) and full_text[i:i+2] == "\n\n"):
            sentence_end = i + 1
            break
        if i == len(full_text) - 1:
            sentence_end = len(full_text)

    full_sentence = full_text[sentence_start:sentence_end].strip()

    # —— 2. Extract paragraph —— 
    paragraph = full_sentence
    if len(full_sentence) < 100:
        para_start = sentence_start
        for i in range(sentence_start - 1, max(0, sentence_start - 1000), -1):
            if full_text[i:i+2] == "\n\n" or i == 0:
                para_start = i + (2 if full_text[i:i+2] == "\n\n" else 0)
                break

        para_end = sentence_end
        for i in range(sentence_end, min(len(full_text), sentence_end + 1000)):
            if full_text[i:i+2] == "\n\n" or i == len(full_text) - 1:
                para_end = i
                break

        paragraph = full_text[para_start:para_end].strip()

    # —— 3. Extract section title —— 
    section_title = None
    fragment_start = max(0, match_start - 2000)
    heading_search = re.search(
        r'(?:Section|SECTION|第\s?\d+\s?节)[\s\:：]+(.+?)(?:\n|$)',
        full_text[fragment_start:match_start]
    )
    if heading_search:
        section_title = heading_search.group(1).strip()

    # —— 4. Detect reference pattern —— 
    reference_pattern = None
    patterns = [
        r"(code|dataset|implementation|source code).*available at",
        r"(code|dataset|implementation|source code).*can be found at",
        r"we (release|publish|provide).*at",
        r"(available|accessible) (at|from|via|through)"
    ]
    for p in patterns:
        pm = re.search(p, paragraph, re.IGNORECASE)
        if pm:
            reference_pattern = pm.group(0)
            break

    # —— 5. Identify page hint —— 
    page_hint = None
    page_fragment = full_text[max(0, match_start - 200):min(len(full_text), match_end + 200)]
    page_matches = re.findall(r'(?:page|pg\.?)\s*(\d+)', page_fragment, flags=re.IGNORECASE)
    if page_matches:
        try:
            page_hint = int(page_matches[0])
        except ValueError:
            page_hint = None

    # —— 6. Standard context —— 
    standard_start = max(0, match_start - CONTEXT_WINDOW_SIZE)
    standard_end = min(len(full_text), match_end + CONTEXT_WINDOW_SIZE)
    standard_context = full_text[standard_start:standard_end].strip()

    return {
        "standard_context": standard_context,
        "full_sentence": full_sentence,
        "paragraph": paragraph,
        "section_title": section_title,
        "reference_pattern": reference_pattern,
        "page_hint": page_hint
    }


def score_domain(url: str) -> int:
    """
    根据域名给 URL 打分，判断是否可能是数据集/代码仓库链接。
    """
    score = 0
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if not domain_match:
        return score

    domain = domain_match.group(1).lower()
    high_prob_domains = [
        "github.com", "gitlab.com",
        "zenodo.org", "figshare.com",
        "huggingface.co", "kaggle.com",
        "dataverse.harvard.edu",
        "paperswithcode.com",
        "data.mendeley.com",
        "osf.io"
    ]
    medium_prob_domains = [
        ".edu", ".ac.", "archive.org",
        "dropbox.com", "drive.google.com",
        "dspace.", "figshare.", "arxiv.org",
        "bitbucket.org"
    ]
    low_prob_domains = [
        "twitter.com", "facebook.com",
        "linkedin.com", "instagram.com",
        "youtube.com", "vimeo.com",
        "news.", "blog.", "wordpress.com",
        "acm.org", "ieee.org", "springer.com"
    ]

    if any(d in domain for d in high_prob_domains):
        score += 20
    if any(d in domain for d in medium_prob_domains):
        score += 10
    if any(d in domain for d in low_prob_domains):
        score -= 15

    return score


def score_path(url: str) -> int:
    """
    根据 URL 路径给分，判断是否可能是数据集/代码相关。
    """
    score = 0
    path_match = re.search(r'https?://(?:www\.)?[^/]+(/[^?#]*)', url)
    if not path_match:
        return score
    path = path_match.group(1).lower()

    high_relevance_paths = [
        "/dataset", "/data", "/code",
        "/repository", "/repo/", "/benchmark",
        "/download", "/release", "/model",
        "/github", "/gitlab", "/files"
    ]
    data_extensions = [
        ".zip", ".tar.gz", ".csv", ".json",
        ".h5", ".pkl", ".pt", ".npz", ".md5",
        ".npy", ".jsonl", ".parquet", ".arrow"
    ]
    low_relevance_paths = [
        "/about", "/contact", "/team",
        "/profile", "/user/", "/publications",
        "/citation", "/references"
    ]

    if any(p in path for p in high_relevance_paths):
        score += 15
    if any(path.endswith(ext) for ext in data_extensions):
        score += 15
    if any(p in path for p in low_relevance_paths):
        score -= 10

    return score


def score_context(context: Optional[str]) -> int:
    """
    根据上下文给分，判断是否可能是数据集/代码引用。
    """
    score = 0
    if not context:
        return score
    ctx = context.lower()

    strong_indicators = [
        "our code is available", "our dataset is available",
        "we release", "we provide", "source code:",
        "implementation is at", "data can be downloaded",
        "code is at", "dataset is at", "our implementation",
        "github repository", "available for download",
        "code for this paper", "dataset for this paper"
    ]
    relevant_keywords = [
        "dataset", "数据集", "code", "代码",
        "repository", "benchmark", "基准测试",
        "implementation", "github", "gitlab",
        "available at", "can be found at",
        "download", "资源", "开源"
    ]
    negative_indicators = [
        "cited from", "reference from", "more details in",
        "as described in", "see also", "home page",
        "for more information", "参考文献", "引用"
    ]

    for ind in strong_indicators:
        if ind in ctx:
            score += 25
            break
    for kw in relevant_keywords:
        if kw in ctx:
            score += 15
            break
    for neg in negative_indicators:
        if neg in ctx:
            score -= 15
            break

    return score


def score_section(section_title: Optional[str]) -> int:
    """
    根据章节标题给分，判断是否可能是数据集/代码引用。
    """
    score = 0
    if not section_title:
        return score
    title_lower = section_title.lower()

    relevant_sections = [
        "implementation", "code", "data", "method",
        "experiment", "availability", "resource",
        "open source", "software", "model"
    ]
    irrelevant_sections = [
        "reference", "related work", "citation",
        "introduction", "background", "acknowledgment",
        "prior work", "conclusion"
    ]

    if any(rs in title_lower for rs in relevant_sections):
        score += 15
    if any(irs in title_lower for irs in irrelevant_sections):
        score -= 10

    return score


def is_likely_dataset_url(
    url: str,
    context: Optional[str],
    section_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    综合各项分值，判断一个 URL 是否可能是数据集/代码仓库链接。

    返回字典包含：
      - score: 总分
      - probability: 'high' / 'medium' / 'low'
      - filter: True/False （True 表示过滤掉）
      - domain_score, path_score, context_score, section_score
    """
    domain_score  = score_domain(url)
    path_score    = score_path(url)
    context_score = score_context(context)
    section_score = score_section(section_title)

    total = domain_score + path_score + context_score + section_score

    if total > 30:
        probability    = "high"
        filter_decision = False
    elif total > 10:
        probability    = "medium"
        filter_decision = False
    else:
        probability    = "low"
        filter_decision = True

    return {
        "score": total,
        "probability": probability,
        "filter": filter_decision,
        "domain_score": domain_score,
        "path_score": path_score,
        "context_score": context_score,
        "section_score": section_score
    }


def extract_candidate_links_from_text(full_text: Optional[str]) -> List[Dict[str, Any]]:
    """
    从纯文本中抽取 URL 并结合上下文 & 打分逻辑筛选“可能是数据集/代码仓库”的链接。

    返回列表，每个元素包含：
      - url: URL
      - context: 段落上下文
      - full_sentence: 整句上下文
      - section_title: 章节标题或 None
      - reference_pattern: 引用短语或 None
      - page_hint: 页码提示或 None
      - standard_context: 固定 window 前后截取的上下文
      - evaluation: 打分结果字典
    """
    candidate_links: List[Dict[str, Any]] = []

    if not full_text:
        logger.warning("extract_candidate_links_from_text: full_text is empty or None.")
        return candidate_links

    logger.info(f"Extracting URLs from text ({len(full_text)} characters).")

    matches = list(URL_REGEX.finditer(full_text))
    url_count     = 0
    filtered_count = 0

    for match in matches:
        raw_url = match.group(0)
        url = _clean_url(raw_url)
        if not url or len(url) < 10:
            continue

        enhanced = extract_enhanced_context_from_text(full_text, match)
        paragraph     = enhanced["paragraph"]
        section_title = enhanced["section_title"]

        evaluation = is_likely_dataset_url(url, paragraph, section_title)

        link_entry = {
            "url": url,
            "context": paragraph,
            "full_sentence": enhanced["full_sentence"],
            "section_title": section_title,
            "reference_pattern": enhanced["reference_pattern"],
            "page_hint": enhanced["page_hint"],
            "standard_context": enhanced["standard_context"],
            "evaluation": evaluation
        }

        if not evaluation["filter"]:
            candidate_links.append(link_entry)
            url_count += 1
        else:
            filtered_count += 1
            logger.debug(f"Filtered URL: {url} (score={evaluation['score']}).")

    logger.info(f"Found {url_count} candidate URLs (filtered out {filtered_count}).")

    # 去重：保留第一次出现
    deduplicated_links: List[Dict[str, Any]] = []
    seen_urls: set = set()
    for link in candidate_links:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            deduplicated_links.append(link)

    logger.info(f"After deduplication: {len(deduplicated_links)} unique URLs.")
    return deduplicated_links


if __name__ == "__main__":
    # 模拟测试
    test_text = """
    In this paper, we publish our dataset at https://github.com/example/dataset.
    The code can be found at https://gitlab.com/example/code. Project page: https://example.com/project.
    """
    logger.setLevel(logging.DEBUG)
    candidates = extract_candidate_links_from_text(test_text)
    for i, c in enumerate(candidates, 1):
        print(f"{i}. URL: {c['url']}, Score={c['evaluation']['score']}, Section={c['section_title']}")
