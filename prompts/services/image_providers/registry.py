"""
Provider registry for looking up image generation providers by name.
"""
import logging

from .base import ImageProvider

logger = logging.getLogger(__name__)

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
    try:
        from .replicate_provider import ReplicateImageProvider
        register_provider('replicate', ReplicateImageProvider)
    except ImportError:
        logger.info("Replicate provider unavailable — replicate/httpx not installed")
    try:
        from .xai_provider import XAIImageProvider
        register_provider('xai', XAIImageProvider)
    except ImportError:
        logger.info("xAI provider unavailable — openai SDK not installed")


_register_defaults()
