from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationResult:
    """Result of a single image generation API call."""
    success: bool
    image_data: Optional[bytes] = None
    revised_prompt: str = ''
    error_message: str = ''
    cost: float = 0.0


class ImageProvider(ABC):
    """
    Abstract base class for AI image generation providers.

    All providers must implement:
    - generate(): Generate an image from a text prompt
    - get_rate_limit(): Return the provider's rate limit (images/min)
    - validate_settings(): Check if the given settings are valid

    Providers declare:
    - requires_nsfw_check: Whether generated images need NSFW screening
    - supported_sizes: List of supported image dimensions
    - supported_qualities: List of supported quality levels
    """

    requires_nsfw_check: bool = True
    supported_sizes: list = []
    supported_qualities: list = []

    @abstractmethod
    def generate(
        self,
        prompt: str,
        size: str = '1024x1024',
        quality: str = 'medium',
        reference_image_url: str = '',
    ) -> GenerationResult:
        """
        Generate a single image from a text prompt.

        Args:
            prompt: The text prompt for image generation.
            size: Image dimensions (e.g., '1024x1024').
            quality: Quality level (e.g., 'low', 'medium', 'high').
            reference_image_url: Optional reference image URL.

        Returns:
            GenerationResult with image data or error info.
        """
        pass

    @abstractmethod
    def get_rate_limit(self) -> int:
        """
        Return the maximum images per minute for this provider.

        Returns:
            Integer representing images per minute.
        """
        pass

    @abstractmethod
    def validate_settings(
        self, size: str, quality: str
    ) -> tuple[bool, str]:
        """
        Validate that the given settings are supported.

        Args:
            size: Requested image dimensions.
            quality: Requested quality level.

        Returns:
            Tuple of (is_valid, error_message).
        """
        pass

    def get_cost_per_image(
        self, size: str = '1024x1024', quality: str = 'medium'
    ) -> float:
        """
        Return the estimated cost per image for given settings.
        Override in subclasses with actual pricing.

        Returns:
            Float representing cost in USD.
        """
        return 0.0
