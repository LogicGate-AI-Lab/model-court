"""
Google Gemini LLM provider implementation.
"""

from typing import Optional
from .base import BaseLLMProvider


class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider using the official Google Generative AI SDK.
    
    Supports Gemini models with optional grounding (search).
    """
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        enable_grounding: bool = False,
        **kwargs
    ):
        """
        Initialize Google Gemini provider.
        
        Args:
            model_name: Gemini model name (e.g., gemini-1.5-pro, gemini-1.5-flash)
            api_key: Google API key (can also be set via GOOGLE_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            enable_grounding: Enable Google Search grounding
            **kwargs: Additional parameters passed to Gemini API
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs
        )
        self.enable_grounding = enable_grounding
        self._client = None
        self._model = None
    
    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            try:
                import google.generativeai as genai
            except ImportError:
                raise ImportError(
                    "Google Generative AI SDK not installed. "
                    "Install with: pip install google-generativeai"
                )
            
            # Configure API key
            genai.configure(api_key=self.api_key)
            
            # Set up generation config
            generation_config = {
                "temperature": self.temperature,
            }
            if self.max_tokens:
                generation_config["max_output_tokens"] = self.max_tokens
            
            generation_config.update(self.extra_params)
            
            # Create model instance
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
        
        return self._model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> str:
        """
        Generate text using Google Gemini API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (prepended to user prompt)
            **kwargs: Additional parameters for the API call
        
        Returns:
            Generated text
        """
        model = self._get_model()
        
        # Combine system and user prompts
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            # Gemini doesn't have native async support in all versions,
            # so we'll use synchronous call in an async wrapper
            import asyncio
            
            def _sync_generate():
                response = model.generate_content(full_prompt)
                return response.text
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _sync_generate)
            return result
            
        except Exception as e:
            raise RuntimeError(f"Google Gemini API call failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Gemini doesn't require explicit cleanup
        return False

