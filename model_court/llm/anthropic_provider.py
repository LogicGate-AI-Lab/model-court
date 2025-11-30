"""
Anthropic Claude LLM provider implementation.
"""

from typing import Optional
from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider using the official Anthropic SDK.
    
    Supports Claude 3 models (Opus, Sonnet, Haiku).
    """
    
    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize Anthropic Claude provider.
        
        Args:
            model_name: Claude model name (e.g., claude-3-opus-20240229)
            api_key: Anthropic API key (can also be set via ANTHROPIC_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate (required by Claude)
            timeout: Request timeout in seconds
            **kwargs: Additional parameters passed to Anthropic API
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens or 4096,  # Claude requires max_tokens
            timeout=timeout,
            **kwargs
        )
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "Anthropic SDK not installed. Install with: pip install anthropic"
                )
            
            self._client = AsyncAnthropic(
                api_key=self.api_key,
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
        Generate text using Anthropic Claude API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional parameters for the API call
        
        Returns:
            Generated text
        """
        client = self._get_client()
        
        # Prepare API parameters
        api_params = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            api_params["system"] = system_prompt
        
        # Override with any additional params
        api_params.update(kwargs)
        api_params.update(self.extra_params)
        
        try:
            response = await client.messages.create(**api_params)
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client."""
        if self._client is not None:
            await self._client.close()
        return False

