"""
Base class for reference sources.

All reference sources must inherit from BaseReference and implement the retrieve method.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseReference(ABC):
    """
    Abstract base class for all reference sources.
    
    Reference sources provide evidence and context for jury members to evaluate claims.
    They can be search engines, knowledge bases, or text documents.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the reference source.
        
        Args:
            name: Optional name for this reference source
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieve relevant information based on the query.
        
        Args:
            query: The search query or claim to find evidence for
            top_k: Maximum number of results to return
        
        Returns:
            List of relevant text snippets/documents
        
        Raises:
            Exception: If retrieval fails
        """
        pass
    
    async def retrieve_with_scores(self, query: str, top_k: int = 5) -> List[tuple[str, float]]:
        """
        Retrieve relevant information with relevance scores.
        
        This is an optional method that can be implemented by subclasses
        to return relevance scores along with the results.
        
        Args:
            query: The search query or claim to find evidence for
            top_k: Maximum number of results to return
        
        Returns:
            List of (text, score) tuples where score indicates relevance
        """
        # Default implementation just returns results with score 1.0
        results = await self.retrieve(query, top_k)
        return [(text, 1.0) for text in results]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

