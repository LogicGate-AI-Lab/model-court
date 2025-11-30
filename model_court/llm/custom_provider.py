"""
Custom LLM provider base class for user-defined implementations.
"""

from .base import BaseLLMProvider


class CustomProvider(BaseLLMProvider):
    """
    Base class for custom LLM providers.
    
    Users can inherit from this class to implement their own LLM providers.
    
    Example:
        class MyCustomProvider(CustomProvider):
            async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
                # Your custom implementation here
                return "Generated text"
    """
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> str:
        """
        Generate text using custom implementation.
        
        This method should be overridden by subclasses.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            "CustomProvider.generate() must be implemented by subclass. "
            "Please create a subclass and override this method with your custom logic."
        )

