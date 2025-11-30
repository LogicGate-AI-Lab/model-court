"""
Base class for court code (precedent database).

All court code implementations must inherit from BaseCourtCode.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_court.core.models import CourtCodeEntry, Precedent


class BaseCourtCode(ABC):
    """
    Abstract base class for court code (precedent database).
    
    The court code stores historical verdicts and allows searching
    for similar precedents to inform current decisions.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the court code database.
        
        Args:
            db_path: Path to the database file/directory
        """
        self.db_path = db_path
    
    @abstractmethod
    async def search_exact(self, claim: str) -> Optional[CourtCodeEntry]:
        """
        Search for an exact match of the claim.
        
        Args:
            claim: The claim text to search for
        
        Returns:
            Exact matching entry if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        claim: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Precedent]:
        """
        Search for similar claims using vector similarity.
        
        Args:
            claim: The claim text to search for
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of similar precedents sorted by similarity (highest first)
        """
        pass
    
    @abstractmethod
    async def add_entry(self, entry: CourtCodeEntry) -> str:
        """
        Add a new entry to the court code.
        
        Args:
            entry: The court code entry to add
        
        Returns:
            ID of the added entry
        """
        pass
    
    @abstractmethod
    async def update_entry(self, entry_id: str, **updates) -> bool:
        """
        Update an existing entry in the court code.
        
        Args:
            entry_id: ID of the entry to update
            **updates: Fields to update
        
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_entry(self, entry_id: str) -> Optional[CourtCodeEntry]:
        """
        Retrieve a specific entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
        
        Returns:
            The entry if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry from the court code.
        
        Args:
            entry_id: ID of the entry to delete
        
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    async def search_with_validity(
        self,
        claim: str,
        check_date: Optional[datetime] = None,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> tuple[Optional[CourtCodeEntry], List[Precedent]]:
        """
        Search for both exact matches and similar precedents, considering validity.
        
        This is a convenience method that combines exact and similar search,
        and filters results based on their validity period.
        
        Args:
            claim: The claim text to search for
            check_date: Date to check validity against (defaults to now)
            top_k: Maximum number of similar results to return
            threshold: Minimum similarity score for similar results
        
        Returns:
            Tuple of (exact_match, similar_precedents)
            - exact_match: Exact matching entry if found and valid, None otherwise
            - similar_precedents: List of valid similar precedents
        """
        check_date = check_date or datetime.now()
        
        # Search for exact match
        exact = await self.search_exact(claim)
        if exact and not exact.is_valid(check_date):
            exact = None
        
        # Search for similar precedents
        similar = await self.search_similar(claim, top_k, threshold)
        valid_similar = [p for p in similar if p.is_valid(check_date)]
        
        return exact, valid_similar
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(db_path={self.db_path})"

