"""
Google Custom Search API reference implementation.
"""

from typing import List, Optional
from .base import BaseReference


class GoogleSearchReference(BaseReference):
    """
    Google Custom Search API reference source.
    
    Uses Google Custom Search JSON API to retrieve search results.
    Requires API key and Custom Search Engine ID.
    """
    
    def __init__(
        self,
        api_key: str,
        cse_id: str,
        search_depth: int = 3,
        name: Optional[str] = None
    ):
        """
        Initialize Google Search reference.
        
        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
            search_depth: Number of results to retrieve per search
            name: Optional name for this reference
        """
        super().__init__(name=name or "GoogleSearch")
        self.api_key = api_key
        self.cse_id = cse_id
        self.search_depth = search_depth
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieve search results from Google.
        
        Args:
            query: Search query
            top_k: Maximum number of results to return
        
        Returns:
            List of result snippets
        """
        try:
            import aiohttp
        except ImportError:
            raise ImportError(
                "aiohttp not installed. Install with: pip install aiohttp"
            )
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(top_k, 10)  # Google API max is 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"Google Search API error {response.status}: {error_text}"
                        )
                    
                    data = await response.json()
                    
                    # Extract snippets from results
                    results = []
                    for item in data.get("items", [])[:top_k]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        
                        # Combine title and snippet
                        result_text = f"{title}\n{snippet}\nSource: {link}"
                        results.append(result_text)
                    
                    return results
        
        except Exception as e:
            raise RuntimeError(f"Google Search failed: {str(e)}")
    
    async def retrieve_with_scores(self, query: str, top_k: int = 5) -> List[tuple[str, float]]:
        """
        Retrieve search results with relevance scores.
        
        Google doesn't provide explicit scores, so we use rank-based scoring.
        
        Args:
            query: Search query
            top_k: Maximum number of results
        
        Returns:
            List of (text, score) tuples
        """
        results = await self.retrieve(query, top_k)
        
        # Assign scores based on rank (higher rank = higher score)
        scored_results = []
        for i, text in enumerate(results):
            score = 1.0 - (i * 0.1)  # Decreasing score by rank
            scored_results.append((text, max(score, 0.1)))
        
        return scored_results

