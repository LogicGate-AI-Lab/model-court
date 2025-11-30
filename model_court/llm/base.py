"""
Base class for LLM providers.

All LLM providers must inherit from BaseLLMProvider and implement the generate method.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    This class defines the interface that all LLM providers must implement.
    Providers can be OpenAI, Google, Anthropic, or custom implementations.
    """
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize the LLM provider.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for authentication (if required)
            base_url: Base URL for the API endpoint (for custom endpoints)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum number of tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_params = kwargs
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> str:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: System-level instructions (optional)
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text as a string
        
        Raises:
            Exception: If generation fails
        """
        pass
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON output based on the given prompt.
        
        This is a convenience method that requests JSON-formatted output.
        Some providers may have native JSON mode support.
        
        Args:
            prompt: The user prompt
            system_prompt: System-level instructions (optional)
            **kwargs: Additional generation parameters
        
        Returns:
            Parsed JSON as a dictionary
        
        Raises:
            Exception: If generation or JSON parsing fails
        """
        import json
        
        # Append JSON formatting instruction to system prompt
        json_instruction = "\n\nYou MUST respond with ONLY valid JSON. Do not include any explanations, quotes, or other text. Just the raw JSON object starting with { and ending with }."
        full_system_prompt = system_prompt + json_instruction
        
        response = await self.generate(prompt, full_system_prompt, **kwargs)
        
        # Clean response: remove leading/trailing whitespace and quotes
        response = response.strip()
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        
        # Try to extract JSON from response
        try:
            # First try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find raw JSON object or array
            json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, raise an error
            raise ValueError(f"Could not parse JSON from response: {response[:200]}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"

