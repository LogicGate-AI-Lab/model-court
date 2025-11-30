"""
OpenAI LLM provider implementation.
"""

from typing import Optional
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider using the official OpenAI SDK.
    
    Supports GPT-3.5, GPT-4, and other OpenAI models.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model_name: OpenAI model name (e.g., gpt-3.5-turbo, gpt-4)
            api_key: OpenAI API key (can also be set via OPENAI_API_KEY env var)
            base_url: Custom base URL for OpenAI-compatible endpoints
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Additional parameters passed to OpenAI API
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs
        )
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Install with: pip install openai"
                )
            
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional parameters for the API call
        
        Returns:
            Generated text
        """
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Merge default params with kwargs
        api_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            api_params["max_tokens"] = self.max_tokens
        
        # Override with any additional params
        api_params.update(kwargs)
        api_params.update(self.extra_params)
        
        try:
            response = await client.chat.completions.create(**api_params)
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client."""
        if self._client is not None:
            await self._client.close()
        return False

