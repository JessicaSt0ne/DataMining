import requests
import logging
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, parse_qs

# Import config
from . import config

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def parse_openreview_url(url: str) -> tuple[str, str, str]:
    """
    从OpenReview完整URL中解析出域名和类别信息。

    Args:
        url: 完整的OpenReview URL，如
            https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral

    Returns:
        tuple: (domain, category, conference_name)
            domain: OpenReview域名，如 "ICLR.cc/2025/Conference"
            category: 论文类别，如 "oral", "spotlight", "poster"
            conference_name: 会议简称和年份，如 "ICLR 2025"
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # 获取domain
    domain = query_params.get('id', [''])[0]
    if not domain:
        logging.error(f"Unable to extract domain from URL: {url}")
        return '', '', ''

    # 获取类别（从fragment中提取）
    fragment = parsed_url.fragment
    category = ''
    if fragment.startswith('tab-accept-'):
        category = fragment.replace('tab-accept-', '')

    # 从domain中提取会议名称和年份
    try:
        conference_abbr = domain.split('.')[0]  # 例如：ICLR, NeurIPS, ICML
        year = domain.split('/')[1]  # 例如：2025, 2024
        conference_name = f"{conference_abbr} {year}"
    except (IndexError, AttributeError):
        logging.error(f"Failed to parse conference info from domain: {domain}")
        conference_name = ""

    return domain, category, conference_name


def fetch_notes_from_url(url: str, limit: int = config.DEFAULT_API_LIMIT_PER_REQUEST, max_total: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    从完整的OpenReview URL获取论文列表。

    Args:
        url: 完整的OpenReview URL，如
            https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral
        limit: 每次API请求获取的论文数量
        max_total: 最大获取的论文总数，None表示获取所有

    Returns:
        论文列表，每个论文为一个字典，包含元数据和构造的pdf_url
    """
    # 解析URL获取必要参数
    domain, category, conference_name = parse_openreview_url(url)

    if not domain:
        logging.error(f"Failed to extract domain from URL: {url}")
        return []

    if not category:
        logging.warning(f"No category found in URL fragment: {url}")
        # 仍然继续，因为可能是主页面而非特定类别

    # 构建venue参数 - 格式为"[会议名称] [类别]"，例如"ICLR 2025 Oral"
    venue = f"{conference_name} {category.capitalize()}" if category else conference_name

    logging.info(
        f"Extracted parameters: Domain={domain}, Category={category}, Venue={venue}")

    # 调用现有API函数获取论文
    return fetch_notes_via_api(venue=venue, domain=domain, limit=limit, max_total=max_total)


def fetch_notes_from_urls(urls: List[str], limit: int = config.DEFAULT_API_LIMIT_PER_REQUEST, max_total: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    从多个OpenReview URL获取论文列表。

    Args:
        urls: OpenReview URL列表
        limit: 每次API请求获取的论文数量
        max_total: 每个URL最大获取的论文总数，None表示获取所有

    Returns:
        所有URL中的论文列表，已去重
    """
    all_notes = []
    seen_ids = set()

    for url in urls:
        logging.info(f"Processing URL: {url}")
        notes = fetch_notes_from_url(url, limit, max_total)

        # 去重添加
        for note in notes:
            note_id = note.get('id')
            if note_id and note_id not in seen_ids:
                seen_ids.add(note_id)
                all_notes.append(note)

    logging.info(
        f"Finished processing all URLs. Total unique notes: {len(all_notes)}")
    return all_notes

# 保留原有函数


def fetch_notes_via_api(
    venue: str,
    domain: str,
    limit: int = config.DEFAULT_API_LIMIT_PER_REQUEST,
    max_total: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches notes (papers) from the OpenReview API based on venue and domain.

    Args:
        venue: The content.venue parameter for the API (e.g., "ICLR 2025 Oral").
        domain: The domain parameter for the API (e.g., "ICLR.cc/2025/Conference").
        limit: The number of notes to fetch per API request.
        max_total: The maximum total number of notes to fetch across all requests.
                   If None, fetches all available notes matching the criteria.

    Returns:
        A list of dictionaries, where each dictionary represents a note (paper)
        with its metadata, including a constructed 'pdf_url'. Returns an empty
        list if fetching fails or no notes are found.
    """
    params = {
        "content.venue": venue,
        "details": "replyCount,presentation,writable",  # Keep details as needed
        "domain": domain,
        "limit": limit,
        "offset": 0
    }

    all_notes = []
    fetched_count = 0
    while True:
        # Check if max_total limit is reached before making the request
        if max_total is not None and fetched_count >= max_total:
            logging.info(f"Reached maximum total limit of {max_total} notes.")
            break

        # Adjust limit if the next request would exceed max_total
        remaining_limit = limit
        if max_total is not None:
            remaining_needed = max_total - fetched_count
            if remaining_needed < limit:
                params['limit'] = remaining_needed
                remaining_limit = remaining_needed  # Use adjusted limit for logging

        if remaining_limit <= 0:  # Should be caught by the check above, but safety first
            break

        try:
            logging.info(
                f"Fetching notes from API: offset={params['offset']}, limit={params['limit']}")
            # Use config URL and timeout
            resp = requests.get(config.API_URL, params=params,
                                timeout=config.DOWNLOAD_TIMEOUT)
            resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = resp.json()
            notes = data.get("notes", [])

            if not notes:
                logging.info("No more notes found in API response.")
                break

            current_batch_count = 0
            for note in notes:
                if max_total is not None and fetched_count >= max_total:
                    break  # Stop processing this batch if limit reached mid-batch

                # Construct and add the PDF URL for each note
                note_id = note.get('id')
                if note_id:
                    note['pdf_url'] = f"https://openreview.net/attachment?id={note_id}&name=pdf"
                    all_notes.append(note)
                    fetched_count += 1
                    current_batch_count += 1
                else:
                    logging.warning(
                        f"Note found without an 'id', cannot construct PDF URL: {note.get('number', 'N/A')}")

            logging.info(
                f"Fetched {current_batch_count} notes in this batch (offset {params['offset']}). Total fetched: {fetched_count}")

            # Check again if max_total limit is reached after processing the batch
            if max_total is not None and fetched_count >= max_total:
                logging.info(
                    f"Reached maximum total limit of {max_total} notes after processing batch.")
                break

            # Increment offset by the original request limit
            params['offset'] += limit

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            # Depending on desired robustness, could implement retries here
            break  # Stop fetching on error
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode API JSON response: {e}")
            break  # Stop fetching on error
        except Exception as e:
            logging.error(
                f"An unexpected error occurred during API fetch: {e}")
            break  # Stop fetching on unexpected errors

    logging.info(f"Finished fetching. Total notes collected: {len(all_notes)}")
    return all_notes


def fetch_notes_by_ids(paper_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches notes (papers) from the OpenReview API by specific paper IDs.

    Args:
        paper_ids: A list of paper IDs to fetch.

    Returns:
        A list of dictionaries, where each dictionary represents a note (paper)
        with its metadata, including a constructed 'pdf_url'. Returns an empty
        list if fetching fails or no notes are found.
    """
    all_notes = []
    success_count = 0

    logging.info(f"Fetching {len(paper_ids)} papers by their IDs")

    for note_id in paper_ids:
        try:
            # Construct API request URL for a specific paper
            params = {
                "id": note_id,
                "details": "replyCount,presentation,writable"
            }

            logging.info(f"Fetching note with ID: {note_id}")
            resp = requests.get(config.API_URL, params=params,
                                timeout=config.DOWNLOAD_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            notes = data.get("notes", [])
            if not notes:
                logging.warning(f"No note found with ID: {note_id}")
                continue

            # There should only be one note with the given ID
            note = notes[0]

            # Construct and add the PDF URL
            note['pdf_url'] = f"https://openreview.net/attachment?id={note_id}&name=pdf"
            all_notes.append(note)
            success_count += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for ID {note_id}: {e}")
        except json.JSONDecodeError as e:
            logging.error(
                f"Failed to decode API JSON response for ID {note_id}: {e}")
        except Exception as e:
            logging.error(
                f"An unexpected error occurred during API fetch for ID {note_id}: {e}")

    logging.info(
        f"Finished fetching. Successfully retrieved {success_count} out of {len(paper_ids)} requested papers")
    return all_notes


if __name__ == "__main__":
    test_urls = [
        "https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral",
        "https://openreview.net/group?id=NeurIPS.cc/2024/Conference#tab-accept-spotlight",
        "https://openreview.net/group?id=ICML.cc/2024/Conference#tab-accept-poster"
    ]
    print("Testing fetch_notes_from_urls with sample OpenReview URLs...")
    # Fetch up to 10 papers per URL for quick test
    notes = fetch_notes_from_urls(test_urls, limit=10, max_total=10)
    print(f"Total unique papers fetched: {len(notes)}")
    if notes:
        print("Sample paper:")
        sample = notes[0]
        for k, v in sample.items():
            print(f"  {k}: {v}")
    else:
        print("No papers fetched.")
