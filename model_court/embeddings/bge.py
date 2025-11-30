"""
BGE (BAAI General Embedding) model implementation using sentence-transformers.
"""

from typing import Union, List
import numpy as np
from .base import BaseEmbedding


class BGEEmbedding(BaseEmbedding):
    """
    BGE-Large embedding model.
    
    Uses sentence-transformers library with BAAI/bge-large-en-v1.5 model.
    This is a high-quality model with better performance but larger size.
    """
    
    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    DIMENSION = 1024
    
    def __init__(self, device: str = "cpu", normalize_embeddings: bool = True):
        """
        Initialize BGE embedding model.
        
        Args:
            device: Device to run the model on ("cpu" or "cuda")
            normalize_embeddings: Whether to normalize embeddings to unit length
        """
        super().__init__(model_name=self.MODEL_NAME, dimension=self.DIMENSION)
        self.device = device
        self.normalize_embeddings = normalize_embeddings
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
        
        For BGE models, it's recommended to prepend "Represent this sentence for searching: "
        to queries for better performance, but we keep it flexible here.
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            numpy array of shape (n, 1024) where n is the number of texts
        """
        model = self._load_model()
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate embeddings
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False
        )
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query with BGE-specific instruction.
        
        BGE models perform better when queries are prepended with an instruction.
        
        Args:
            query: Query text
        
        Returns:
            numpy array of shape (1024,)
        """
        # Add instruction prefix for queries
        instruction = "Represent this sentence for searching: "
        query_with_instruction = instruction + query
        
        embeddings = self.embed(query_with_instruction)
        return embeddings[0]

