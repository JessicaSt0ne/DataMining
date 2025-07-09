import argparse
import logging
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

# Import modules from the src package
from . import config
from . import parser_test as parser
from . import extractor
from . import validator_mock as validator
from . import output_formatter

# Configure logging
log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

def construct_batch_prompt(url_batch, paper_metadata):
    """
    Construct a prompt for batch validation of multiple URLs.
    
    Args:
        url_batch: List of URL entries to validate
        paper_metadata: Dictionary containing paper metadata
        
    Returns:
        String containing the batch validation prompt
    """
    # Paper metadata section
    paper_info = f"""
论文标题: {paper_metadata.get('title', 'Unknown')}
论文摘要: {paper_metadata.get('abstract', 'Not available')}
"""

    # Batch URL list
    url_entries = []
    for i, link in enumerate(url_batch):
        # Prepare context - use the most informative context available
        context = link.get('context', '')
        section_title = link.get('section_title', 'Unknown')
        page_hint = link.get('page_hint', 'Unknown')
        
        entry = f"""
[{i+1}] URL: {link['url']}
上下文: {context}
章节: {section_title}
页码: {page_hint}
"""
        url_entries.append(entry)
    
    urls_text = "\n".join(url_entries)
    
    # Complete prompt
    prompt = f"""分析以下来自研究论文的多个URL及其上下文。

{paper_info}

判断每个URL是否指向数据集、基准测试或代码仓库。

数据集/基准测试/代码URL特征：
- 指向代码仓库（GitHub、GitLab等）
- 指向数据存储服务（Zenodo、HuggingFace等）
- 包含数据集直接下载链接
- 专注于数据集或基准测试的项目页面
- 包含论文实现或评估代码的网站

非数据集/代码URL特征：
- 一般网站主页
- 论文引用链接
- 个人或组织介绍页面
- 社交媒体资料

URL列表及上下文：
{urls_text}

对每个URL进行分析，以JSON数组格式返回结果，每个URL对应一个对象：
[
  {{
    "index": URL索引号,
    "url": URL字符串,
    "is_intentional_link": 布尔值（是否为数据集/代码链接）,
    "reason": 判断理由说明
  }},
  ...
]
"""
    return prompt


def batch_validate_links(candidate_links, paper_metadata, batch_size=5):
    """
    Batch validate URLs to determine if they are dataset/code repository links.
    
    Args:
        candidate_links: List of candidate URL entries to validate
        paper_metadata: Dictionary containing paper metadata
        batch_size: Maximum number of URLs to validate in a single batch
        
    Returns:
        List of validation result dictionaries
    """
    results = []
    note_id = paper_metadata.get('id', 'UNKNOWN_PDF_ID')
    
    # Sort links by evaluation score (highest first)
    candidate_links.sort(key=lambda x: x.get('evaluation', {}).get('score', 0), reverse=True)
    
    # Process URLs in batches
    for i in range(0, len(candidate_links), batch_size):
        batch = candidate_links[i:i+batch_size]
        
        # Construct batch validation prompt
        prompt = construct_batch_prompt(batch, paper_metadata)
        
        try:
            # Send batch validation request
            logging.debug(f"Validating batch of {len(batch)} URLs for note {note_id} (batch {i//batch_size + 1})")
            ai_response = validator.send_validation_request(prompt)
            
            # Parse batch response
            try:
                parsed_results = json.loads(ai_response)
                
                if isinstance(parsed_results, list):
                    # Map results back to original links
                    for result in parsed_results:
                        index = result.get("index", 0) - 1  # Adjust to 0-based index
                        if 0 <= index < len(batch):
                            url = batch[index]['url']
                            context = batch[index].get('context', '')
                            
                            results.append({
                                'url': url,
                                'context': context,
                                'note_id': note_id,
                                'ai_decision': {
                                    'is_intentional_link': result.get('is_intentional_link', False),
                                    'reason': result.get('reason', 'No reason provided')
                                }
                            })
                        else:
                            logging.warning(f"Invalid index {index+1} in AI response for note {note_id}")
                else:
                    # Not a valid list response, fall back to individual validation
                    logging.warning(f"Invalid batch response format for note {note_id}. Falling back to individual validation.")
                    for link in batch:
                        result = validator.validate_url_with_ai(link['url'], link.get('context', ''))
                        results.append({
                            'url': link['url'],
                            'context': link.get('context', ''),
                            'note_id': note_id,
                            'ai_decision': result
                        })
            except json.JSONDecodeError:
                # Cannot parse JSON, fall back to individual validation
                logging.warning(f"Failed to parse batch AI response as JSON for note {note_id}. Falling back to individual validation.")
                for link in batch:
                    result = validator.validate_url_with_ai(link['url'], link.get('context', ''))
                    results.append({
                        'url': link['url'],
                        'context': link.get('context', ''),
                        'note_id': note_id,
                        'ai_decision': result
                    })
        except Exception as e:
            logging.error(f"Error during batch validation for note {note_id}: {e}")
            # Fall back to individual validation on error
            for link in batch:
                try:
                    result = validator.validate_url_with_ai(link['url'], link.get('context', ''))
                    results.append({
                        'url': link['url'],
                        'context': link.get('context', ''),
                        'note_id': note_id,
                        'ai_decision': result
                    })
                except Exception as e2:
                    logging.error(f"Error validating URL {link['url']} for note {note_id}: {e2}")
    
    # Handle auto-rejected URLs (very low score)
    auto_rejected = []
    for link in candidate_links:
        # Skip URLs that were already processed
        if any(r['url'] == link['url'] for r in results):
            continue
            
        # Auto-reject URLs that were filtered out by the extractor
        evaluation = link.get('evaluation', {})
        if evaluation.get('filter', False):
            auto_rejected.append({
                'url': link['url'],
                'context': link.get('context', ''),
                'note_id': note_id,
                'ai_decision': {
                    'is_intentional_link': False,
                    'reason': f"Automatically filtered: low probability score ({evaluation.get('score', 0)})"
                }
            })
    
    # Add auto-rejected URLs to results
    results.extend(auto_rejected)
    
    return results


def process_single_pdf(note_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Worker function to process a single downloaded PDF: 
    parse to Markdown, extract URLs with context, and validate using AI.

    Args:
        note_metadata: Dictionary containing metadata for one paper, including 'id' and 'local_pdf_path'.

    Returns:
        A list of validation result dictionaries for this PDF. Each dictionary contains
        URL info, context, and AI decision. Returns empty list on failure.
    """
    note_id = note_metadata.get('id', 'UNKNOWN_PDF_ID') # Use a default if ID is missing
    local_pdf_path_str = note_metadata.get('local_pdf_path')

    if not local_pdf_path_str:
        logging.debug(f"Skipping processing for note {note_id}: No local PDF path provided in metadata.")
        return []

    local_pdf_path = Path(local_pdf_path_str)
    if not local_pdf_path.is_file():
        logging.warning(f"Skipping processing for note {note_id}: PDF file not found at {local_pdf_path}")
        return []

    logging.debug(f"Processing PDF for note {note_id}: {local_pdf_path.name}")

    try:
        # 1. Parse PDF to Markdown using pymupdf4llm
        markdown_text = parser.parse_pdf_file(local_pdf_path)
        if markdown_text is None or len(markdown_text) < 100:
            # If parsing fails completely, we cannot proceed
            logging.error(f"Failed to parse PDF to Markdown for note {note_id} from {local_pdf_path.name}. Cannot extract/validate links.")
            return []
        logging.debug(f"Successfully parsed PDF to Markdown ({len(markdown_text)} characters) for note {note_id}.")

        # 2. Extract Candidate Links with context from Markdown
        candidate_links_data = extractor.extract_candidate_links(markdown_text)
        if not candidate_links_data:
            logging.info(f"No candidate URLs extracted for note {note_id}.")
            return []
        logging.debug(f"Extracted {len(candidate_links_data)} candidate links for note {note_id}.")

        # 3. Validate Links using batch processing
        validation_results = batch_validate_links(candidate_links_data, note_metadata, 
                                                  batch_size=config.BATCH_VALIDATION_SIZE)

        num_intentional = sum(1 for r in validation_results if r.get('ai_decision', {}).get('is_intentional_link') is True)
        if num_intentional > 0:
            logging.info(f"AI validation completed for note {note_id}. Found {num_intentional} likely intentional links.")
        else:
            logging.debug(f"AI validation completed for note {note_id}. No likely intentional links identified.")

        # Return the detailed validation results for this PDF
        return validation_results

    except Exception as e:
        logging.error(f"Error processing PDF for note {note_id} ({local_pdf_path.name}): {e}", exc_info=True)
        return []


def run_phase2(metadata_path: Path, output_path: Path, workers: int):
    """
    Executes Phase 2: Extracting and validating links from downloaded PDFs.

    Args:
        metadata_path: Path to the augmented metadata JSON file (from Phase 1).
        output_path: Path to save the final results JSON file.
        workers: Number of parallel workers for processing PDFs.
    """
    start_time = time.time()
    logging.info("--- Starting Phase 2: Extract & Validate ---")
    logging.info(f"Loading metadata from: {metadata_path}")
    logging.info(f"Final results will be saved to: {output_path}")
    logging.info(f"Processing workers: {workers}")

    # --- Step 1: Load Augmented Metadata ---
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            all_metadata: List[Dict[str, Any]] = json.load(f)
        logging.info(f"Loaded metadata for {len(all_metadata)} entries.")
    except FileNotFoundError:
        logging.error(f"Metadata file not found: {metadata_path}. Cannot proceed.")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from metadata file {metadata_path}: {e}")
        return
    except Exception as e:
        logging.error(f"Error loading metadata file {metadata_path}: {e}")
        return

    # Filter for entries with a valid local PDF path
    notes_to_process = [note for note in all_metadata if note.get('local_pdf_path')]
    if not notes_to_process:
        logging.warning("No entries with local PDF paths found in metadata. Nothing to process.")
        # Save an empty dictionary as the result instead of an empty list
        output_formatter.format_results_to_json([], output_path)
        return
    logging.info(f"Found {len(notes_to_process)} entries with PDF paths to process.")

    # --- Step 2: Process PDFs in Parallel ---
    logging.info(f"Processing PDFs using up to {workers} workers...")
    all_validation_results: List[Dict[str, Any]] = [] # Store detailed results from each PDF
    processed_count = 0
    total_to_process = len(notes_to_process)

    # Track API call statistics
    total_urls_processed = 0
    total_api_calls = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_note_id = {
            # Submit process_single_pdf for each note
            executor.submit(process_single_pdf, note): note.get('id', 'N/A')
            for note in notes_to_process
        }

        for future in as_completed(future_to_note_id):
            note_id = future_to_note_id[future]
            processed_count += 1
            try:
                # Result is now a list of validation result dictionaries for one PDF
                pdf_results = future.result()
                
                # Update statistics
                urls_in_pdf = len(pdf_results)
                total_urls_processed += urls_in_pdf
                
                # Estimate API calls (each batch = 1 call)
                batch_size = config.BATCH_VALIDATION_SIZE if hasattr(config, 'BATCH_VALIDATION_SIZE') else 5
                api_calls_for_pdf = (urls_in_pdf + batch_size - 1) // batch_size  # Ceiling division
                total_api_calls += api_calls_for_pdf
                
                if pdf_results:
                    all_validation_results.extend(pdf_results) # Add results for this PDF to the main list
                
                logging.info(f"({processed_count}/{total_to_process}) PDF processing completed for note {note_id}. "
                             f"Found {urls_in_pdf} URLs, used ~{api_calls_for_pdf} API calls.")
            except Exception as exc:
                logging.error(f"Note {note_id} generated an exception during processing task: {exc}", exc_info=True)

    api_call_reduction = "Unknown"
    if total_urls_processed > 0:
        api_call_reduction = f"{(1 - total_api_calls / total_urls_processed) * 100:.1f}%"
    
    logging.info(f"Finished processing all PDFs. Processed {total_urls_processed} URLs with ~{total_api_calls} API calls.")
    logging.info(f"Estimated API call reduction: {api_call_reduction}")
    logging.info(f"Collected {len(all_validation_results)} validation results across all processed PDFs.")

    # --- Step 3: Save Aggregated Results ---
    logging.info(f"Formatting and saving all {len(all_validation_results)} validation results to {output_path}...")
    output_formatter.format_results_to_json(all_validation_results, output_path)

    end_time = time.time()
    logging.info(f"--- Phase 2 finished in {end_time - start_time:.2f} seconds ---")
    validator.log_stats()
    logging.info("Detailed API statistics report:")
    stats = validator.get_stats_report()
    for key, value in stats.items():
        logging.info(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: Extract and validate dataset links from downloaded PDFs."
    )
    parser.add_argument("--metadata", type=Path, required=True,
                        help="Path to the augmented metadata JSON file generated by Phase 1 (e.g., data/crawled_metadata.json)")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="Path to save the final results JSON file (e.g., data/results.json)")
    parser.add_argument("-w", "--workers", type=int, default=config.DEFAULT_PROCESSING_WORKERS,
                        help=f"Number of parallel workers for processing PDFs (default: {config.DEFAULT_PROCESSING_WORKERS})")
    parser.add_argument("-b", "--batch-size", type=int, default=5,
                        help="Number of URLs to validate in a single batch (default: 5)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose (DEBUG) logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
             handler.setFormatter(logging.Formatter(log_format)) # Apply detailed format
        logging.debug("Verbose logging enabled.")
    
    # Set batch validation size
    config.BATCH_VALIDATION_SIZE = args.batch_size
    logging.info(f"Using batch size of {config.BATCH_VALIDATION_SIZE} for URL validation")

    # Ensure the directory for the output file exists
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured output directory exists: {args.output.parent}")
    except OSError as e:
        logging.error(f"Failed to create output directory {args.output.parent}: {e}. Exiting.")
        return

    run_phase2(
        metadata_path=args.metadata,
        output_path=args.output,
        workers=args.workers
    )

if __name__ == "__main__":
    main()