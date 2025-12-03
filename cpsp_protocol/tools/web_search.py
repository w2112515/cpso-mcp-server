"""
Web Search Tool for CPSO-Protocol
Handles web search functionality using DuckDuckGo.
"""

from typing import List, Dict, Optional, Any
from duckduckgo_search import DDGS


def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a web search using DuckDuckGo.
    
    Args:
        query: The search query
        num_results: Number of results to return (default: 5)
        
    Returns:
        List of search results, each containing title, link, and snippet
    """
    results = []
    with DDGS() as ddgs:
        search_results = ddgs.text(query, max_results=num_results)
        for result in search_results:
            results.append({
                'title': result.get('title', ''),
                'link': result.get('href', ''),
                'snippet': result.get('body', '')
            })
    
    return results