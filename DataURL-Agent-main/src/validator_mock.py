"""
Mock validator module that simulates API calls for testing purposes.
Keeps track of API call count and generates simulated responses.
"""

import json
import logging
import random
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Global counter for tracking API calls
@dataclass
class APIStats:
    total_calls: int = 0
    batch_calls: int = 0
    single_calls: int = 0
    total_urls_processed: int = 0
    
    def reset(self):
        self.total_calls = 0
        self.batch_calls = 0
        self.single_calls = 0
        self.total_urls_processed = 0
    
    def get_report(self) -> Dict[str, Any]:
        return {
            "total_api_calls": self.total_calls,
            "batch_api_calls": self.batch_calls,
            "single_api_calls": self.single_calls,
            "total_urls_processed": self.total_urls_processed,
            "api_call_reduction_percentage": self._calculate_reduction()
        }
    
    def _calculate_reduction(self) -> float:
        """Calculate percentage reduction in API calls compared to 1:1 calls"""
        if self.total_urls_processed == 0:
            return 0.0
        naive_calls = self.total_urls_processed  # Without batching, 1 call per URL
        actual_calls = self.total_calls
        reduction = (naive_calls - actual_calls) / naive_calls * 100
        return round(reduction, 2)


# Initialize global stats tracker
api_stats = APIStats()


def reset_stats():
    """Reset all API call statistics"""
    api_stats.reset()
    logging.info("API call statistics have been reset")


def get_stats_report() -> Dict[str, Any]:
    """Get a report of all API call statistics"""
    return api_stats.get_report()


def log_stats():
    """Log current API call statistics"""
    stats = get_stats_report()
    logging.info(f"API Call Statistics:")
    logging.info(f"  Total calls: {stats['total_api_calls']}")
    logging.info(f"  Batch calls: {stats['batch_api_calls']}")
    logging.info(f"  Single calls: {stats['single_api_calls']}")
    logging.info(f"  URLs processed: {stats['total_urls_processed']}")
    logging.info(f"  API call reduction: {stats['api_call_reduction_percentage']:.2f}%")


def _simulate_ai_response(url: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulate AI decision for a URL based on heuristics.
    
    Args:
        url: URL to evaluate
        context: Context surrounding the URL
        
    Returns:
        Dictionary with simulated AI decision
    """
    # Simple heuristics to simulate AI decisions
    is_intentional = False
    reason = "This does not appear to be a dataset or code repository link."
    
    # High probability domains
    high_prob_domains = [
        "github.com", "gitlab.com", "zenodo.org", "figshare.com", 
        "huggingface.co", "kaggle.com", "dataverse", "osf.io"
    ]
    
    # Check domain
    if any(domain in url.lower() for domain in high_prob_domains):
        is_intentional = True
        domain = next(d for d in high_prob_domains if d in url.lower())
        reason = f"This URL points to {domain}, which is commonly used for hosting datasets and code repositories."
    
    # Check URL path
    if "/data" in url or "/dataset" in url or "/code" in url or "/repo" in url:
        is_intentional = True
        reason = "This URL path contains keywords indicating it hosts data or code."
    
    # Check context if available
    if context:
        context_lower = context.lower()
        data_indicators = ["dataset", "code", "implementation", "repository", "available at", "download"]
        if any(indicator in context_lower for indicator in data_indicators):
            is_intentional = True
            indicator = next(ind for ind in data_indicators if ind in context_lower)
            reason = f"The context mentions '{indicator}', suggesting this is an intentional data or code link."
    
    # Add some randomness for realism (10% chance to flip the decision)
    if random.random() < 0.1:
        is_intentional = not is_intentional
        reason = "Based on additional factors, this classification differs from the typical pattern."
    
    return {
        "is_intentional_link": is_intentional,
        "reason": reason
    }


def validate_url_with_ai(url: str, context: str = None) -> Dict[str, Any]:
    """
    Mock function that simulates validating a URL using AI.
    Increases the API call counter but doesn't actually make an API call.
    
    Args:
        url: URL to validate
        context: Context surrounding the URL
        
    Returns:
        Dictionary with simulated AI decision
    """
    # Track statistics
    api_stats.total_calls += 1
    api_stats.single_calls += 1
    api_stats.total_urls_processed += 1
    
    logging.debug(f"[MOCK] Validating single URL (API call #{api_stats.total_calls})")
    
    # Simulate a response rather than calling the AI API
    return _simulate_ai_response(url, context)


def send_validation_request(prompt: str) -> str:
    """
    Mock function that simulates sending a validation request to the AI.
    Increases the API call counter but doesn't actually make an API call.
    
    Args:
        prompt: The prompt to send to the AI
        
    Returns:
        String containing simulated AI response
    """
    # Track statistics
    api_stats.total_calls += 1
    api_stats.batch_calls += 1
    
    # Extract URLs from the prompt to count and simulate responses
    url_matches = re.finditer(r'\[(\d+)\] URL: (https?:\/\/[^\n]+)', prompt)
    
    results = []
    count = 0
    
    # Process each URL found in the prompt
    for match in url_matches:
        count += 1
        index = int(match.group(1))
        url = match.group(2)
        
        # Get context for this URL if available
        context_match = re.search(f'\[{index}\] URL: {re.escape(url)}\n上下文: ([^\n]+)', prompt)
        context = context_match.group(1) if context_match else None
        
        # Simulate AI decision
        decision = _simulate_ai_response(url, context)
        
        # Add to results
        results.append({
            "index": index,
            "url": url,
            "is_intentional_link": decision["is_intentional_link"],
            "reason": decision["reason"]
        })
    
    # Update URL count
    api_stats.total_urls_processed += count
    
    logging.debug(f"[MOCK] Validating batch of {count} URLs (API call #{api_stats.total_calls})")
    
    # Return simulated response as JSON string
    return json.dumps(results)