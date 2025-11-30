"""
Base class for embedding models.

All embedding implementations must inherit from BaseEmbedding and implement the embed method.
"""

from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np


class BaseEmbedding(ABC):
    """
    Abstract base class for all embedding models.
    
    Embedding models convert text into dense vector representations
    for similarity search and semantic matching.
    """
    
    def __init__(self, model_name: str, dimension: int):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name/identifier of the embedding model
            dimension: Dimension of the embedding vectors
        """
        self.model_name = model_name
        self.dimension = dimension
    
    @abstractmethod
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the given text(s).
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            numpy array of shape (n, dimension) where n is the number of texts
            If input is a single string, returns shape (1, dimension)
        
        Raises:
            Exception: If embedding generation fails
        """
        pass
    
    def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
        
        Returns:
            numpy array of shape (dimension,)
        """
        result = self.embed(text)
        return result[0]
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name}, dim={self.dimension})"

