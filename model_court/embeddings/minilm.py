"""
MiniLM embedding model implementation using sentence-transformers.
"""

from typing import Union, List
import numpy as np
from .base import BaseEmbedding


class MiniLMEmbedding(BaseEmbedding):
    """
    MiniLM embedding model.
    
    Uses sentence-transformers library with all-MiniLM-L6-v2 model.
    This is a lightweight model suitable for general-purpose embedding.
    """
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSION = 384
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize MiniLM embedding model.
        
        Args:
            device: Device to run the model on ("cpu" or "cuda")
        """
        super().__init__(model_name=self.MODEL_NAME, dimension=self.DIMENSION)
        self.device = device
        self._model = None
    
    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
            
            print(f"Loading {self.MODEL_NAME} model... This may take a moment on first use.")
            self._model = SentenceTransformer(self.MODEL_NAME, device=self.device)
            print(f"Model loaded successfully on {self.device}.")
        
        return self._model
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the given text(s).
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            numpy array of shape (n, 384) where n is the number of texts
        """
        model = self._load_model()
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate embeddings
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return embeddings

