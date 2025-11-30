"""
Factory for creating LLM providers from configuration.
"""

from typing import Dict, Any, Type, Optional
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .google_provider import GoogleProvider
from .anthropic_provider import AnthropicProvider
from .custom_provider import CustomProvider


# Registry of provider classes
_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "gemini": GoogleProvider,  # Alias
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,  # Alias
    "openai_compatible": OpenAIProvider,  # For local models with OpenAI API
    "custom": CustomProvider,
}


def register_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    Register a custom provider class.
    
    This allows users to add their own LLM providers to the factory.
    
    Args:
        name: Provider name to register
        provider_class: Provider class (must inherit from BaseLLMProvider)
    
    Raises:
        TypeError: If provider_class is not a subclass of BaseLLMProvider
    
    Example:
        class MyProvider(BaseLLMProvider):
            async def generate(self, prompt, system_prompt="", **kwargs):
                return "response"
        
        register_provider("my_provider", MyProvider)
    """
    if not issubclass(provider_class, BaseLLMProvider):
        raise TypeError(
            f"Provider class must inherit from BaseLLMProvider, "
            f"got {provider_class.__name__}"
        )
    
    _PROVIDER_REGISTRY[name.lower()] = provider_class


def create_llm_provider(config: Dict[str, Any]) -> BaseLLMProvider:
    """
    Create an LLM provider from configuration dictionary.
    
    Args:
        config: Configuration dictionary with the following structure:
            {
                "provider": "openai",  # Required: provider name
                "model_name": "gpt-3.5-turbo",  # Required: model name
                "api_key": "sk-...",  # Optional: API key
                "base_url": "...",  # Optional: custom base URL
                "temperature": 0.7,  # Optional: temperature
                "max_tokens": 1000,  # Optional: max tokens
                "timeout": 60,  # Optional: timeout in seconds
                # ... other provider-specific params
            }
    
    Returns:
        Initialized LLM provider instance
    
    Raises:
        ValueError: If provider is not specified or not found
        TypeError: If config is not a dictionary
    
    Example:
        config = {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-...",
            "temperature": 0.5
        }
        provider = create_llm_provider(config)
    """
    if not isinstance(config, dict):
        raise TypeError(f"Config must be a dictionary, got {type(config).__name__}")
    
    provider_name = config.get("provider")
    if not provider_name:
        raise ValueError("Config must include 'provider' field")
    
    provider_name = provider_name.lower()
    if provider_name not in _PROVIDER_REGISTRY:
        available = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {available}"
        )
    
    provider_class = _PROVIDER_REGISTRY[provider_name]
    
    # Extract parameters
    params = {
        "model_name": config.get("model_name"),
        "api_key": config.get("api_key"),
        "base_url": config.get("base_url"),
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens"),
        "timeout": config.get("timeout", 60),
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Add any extra parameters
    extra_params = {
        k: v for k, v in config.items()
        if k not in ["provider", "model_name", "api_key", "base_url", 
                     "temperature", "max_tokens", "timeout"]
    }
    params.update(extra_params)
    
    # Validate required parameters
    if "model_name" not in params:
        raise ValueError("Config must include 'model_name' field")
    
    try:
        return provider_class(**params)
    except Exception as e:
        raise RuntimeError(
            f"Failed to create provider '{provider_name}': {str(e)}"
        )


def list_providers() -> list[str]:
    """
    List all registered provider names.
    
    Returns:
        List of provider names
    """
    return sorted(_PROVIDER_REGISTRY.keys())

