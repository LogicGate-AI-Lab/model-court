"""
OpenAI embedding model implementation.
"""

from typing import Union, List, Optional
import numpy as np
from .base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    """
    OpenAI embedding model.
    
    Uses OpenAI's embedding API (text-embedding-3-small or text-embedding-3-large).
    """
    
    # Model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize OpenAI embedding model.
        
        Args:
            model_name: OpenAI embedding model name
            api_key: OpenAI API key (can also be set via OPENAI_API_KEY env var)
            timeout: Request timeout in seconds
        
        Raises:
            ValueError: If model_name is not recognized
        """
        if model_name not in self.MODEL_DIMENSIONS:
            available = ", ".join(self.MODEL_DIMENSIONS.keys())
            raise ValueError(
                f"Unknown model: {model_name}. Available models: {available}"
            )
        
        dimension = self.MODEL_DIMENSIONS[model_name]
        super().__init__(model_name=model_name, dimension=dimension)
        
        self.api_key = api_key
        self.timeout = timeout
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Install with: pip install openai"
                )
            
            self._client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
        
        return self._client
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the given text(s).
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            numpy array of shape (n, dimension) where n is the number of texts
        """
        client = self._get_client()
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # Call OpenAI API
            response = client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
            
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding API call failed: {str(e)}")

