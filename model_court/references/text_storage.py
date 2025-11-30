"""
Simple text storage reference implementation.
"""

from typing import List, Optional, Union
from pathlib import Path
from .base import BaseReference


class SimpleTextStorage(BaseReference):
    """
    Simple text storage reference source.
    
    Stores reference text directly or loads from a file.
    This is the simplest reference type, useful for providing
    fixed context or user-defined reference material.
    """
    
    def __init__(
        self,
        text: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None
    ):
        """
        Initialize simple text storage.
        
        Args:
            text: Reference text (if providing directly)
            file_path: Path to text file (if loading from file)
            name: Optional name for this reference
        
        Raises:
            ValueError: If neither text nor file_path is provided
        """
        super().__init__(name=name or "TextStorage")
        
        if text is None and file_path is None:
            raise ValueError("Must provide either 'text' or 'file_path'")
        
        if text is not None:
            self.text = text
        else:
            self.file_path = Path(file_path)
            self.text = self._load_text()
    
    def _load_text(self) -> str:
        """Load text from file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to load text from {self.file_path}: {str(e)}")
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieve reference text.
        
        For SimpleTextStorage, the entire text is returned as a single result.
        The query parameter is ignored since we're not performing actual search.
        
        Args:
            query: Not used (for interface compatibility)
            top_k: Not used (for interface compatibility)
        
        Returns:
            List containing the reference text
        """
        # Return the entire text as a single result
        return [self.text]
    
    async def retrieve_with_scores(self, query: str, top_k: int = 5) -> List[tuple[str, float]]:
        """
        Retrieve reference text with score.
        
        Args:
            query: Not used
            top_k: Not used
        
        Returns:
            List of (text, 1.0) tuple
        """
        return [(self.text, 1.0)]
    
    def update_text(self, new_text: str) -> None:
        """
        Update the stored text.
        
        Args:
            new_text: New text content
        """
        self.text = new_text
    
    def reload_from_file(self) -> None:
        """
        Reload text from file.
        
        Raises:
            RuntimeError: If no file_path was set
        """
        if not hasattr(self, 'file_path'):
            raise RuntimeError("No file path set, cannot reload")
        
        self.text = self._load_text()

