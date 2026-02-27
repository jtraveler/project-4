"""
Provider registry for looking up image generation providers by name.
"""

from .base import ImageProvider

# Registry of available providers
PROVIDERS: dict[str, type[ImageProvider]] = {}


def register_provider(
    name: str, provider_class: type[ImageProvider]
) -> None:
    """Register a provider class by name."""
    PROVIDERS[name] = provider_class


def get_provider(name: str, **kwargs) -> ImageProvider:
    """
    Get an instantiated provider by name.

    Args:
        name: Provider name (e.g., 'openai').
        **kwargs: Arguments passed to the provider constructor.

    Returns:
        An instantiated ImageProvider.

    Raises:
        ValueError: If the provider name is not registered.
    """
    if name not in PROVIDERS:
        available = (
            ', '.join(PROVIDERS.keys()) or '(none registered)'
        )
        raise ValueError(
            f"Unknown provider: '{name}'. Available: {available}"
        )
    return PROVIDERS[name](**kwargs)


# Auto-register built-in providers
def _register_defaults():
    from .openai_provider import OpenAIImageProvider
    register_provider('openai', OpenAIImageProvider)


_register_defaults()
