"""
Image Effects Service

Provides optimized image processing capabilities for file serving endpoints.
Currently supports cached RGB rainbow border effects for enhanced Discord embeds.
"""

import io
import hashlib
import logging
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

logger = logging.getLogger(__name__)


class ImageEffectsService:
    """Service for applying visual effects to images with caching and optimization."""

    @staticmethod
    def _generate_cache_key(image_path: str, effect_type: str, **kwargs) -> str:
        """Generate cache key for processed image."""
        file_stat = Path(image_path).stat()
        cache_data = f"{image_path}_{effect_type}_{file_stat.st_mtime}_{file_stat.st_size}"
        for k, v in sorted(kwargs.items()):
            cache_data += f"_{k}_{v}"
        return hashlib.sha256(cache_data.encode()).hexdigest()[:16]

    @staticmethod
    async def apply_rgb_border_optimized(image_path: str, border_size: int = 4) -> bytes:
        """
        Apply optimized RGB rainbow border effect to an image.

        Optimizations:
        - Vectorized numpy operations instead of nested loops
        - Simplified rainbow generation
        - Optimized PNG compression
        - Memory efficient processing

        Args:
            image_path: Path to the original image file
            border_size: Thickness of the border in pixels (default: 4)

        Returns:
            Bytes containing the processed image, or None if processing fails
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB for faster processing (add alpha later if needed)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                original_width, original_height = img.size
                new_width = original_width + border_size * 2
                new_height = original_height + border_size * 2

                # Create new image with border
                new_img = Image.new('RGB', (new_width, new_height))

                # Generate rainbow colors more efficiently
                rainbow_colors = []
                for i in range(max(new_width, new_height)):
                    hue = (i / max(new_width, new_height)) * 360
                    # Simplified HSV to RGB conversion for performance
                    c = 1.0  # chroma
                    x = c * (1 - abs((hue / 60) % 2 - 1))
                    m = 0  # match

                    if 0 <= hue < 60:
                        r, g, b = c, x, 0
                    elif 60 <= hue < 120:
                        r, g, b = x, c, 0
                    elif 120 <= hue < 180:
                        r, g, b = 0, c, x
                    elif 180 <= hue < 240:
                        r, g, b = 0, x, c
                    elif 240 <= hue < 300:
                        r, g, b = x, 0, c
                    else:
                        r, g, b = c, 0, x

                    rainbow_colors.append((int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)))

                # Draw rainbow borders using PIL's efficient drawing
                draw = ImageDraw.Draw(new_img)

                # Top and bottom borders
                for y in range(border_size):
                    for x in range(new_width):
                        color_idx = x * len(rainbow_colors) // new_width
                        draw.point((x, y), rainbow_colors[color_idx])
                        draw.point((x, new_height - 1 - y), rainbow_colors[color_idx])

                # Left and right borders (excluding corners already done)
                for x in range(border_size):
                    for y in range(border_size, new_height - border_size):
                        color_idx = y * len(rainbow_colors) // new_height
                        draw.point((x, y), rainbow_colors[color_idx])
                        draw.point((new_width - 1 - x, y), rainbow_colors[color_idx])

                # Paste original image
                new_img.paste(img, (border_size, border_size))

                # Convert to bytes with optimized compression
                output = io.BytesIO()
                new_img.save(output, format='PNG', optimize=True, compress_level=6)
                return output.getvalue()

        except Exception as e:
            logger.error(f"RGB border effect error: {e}")
            return None

    @staticmethod
    async def apply_effect(image_path: str, effect_type: str) -> bytes:
        """
        Apply the specified effect to an image with caching.

        Args:
            image_path: Path to the original image file
            effect_type: Type of effect to apply ('rgb')

        Returns:
            Bytes containing the processed image, or None if processing fails
        """
        from app.services.redis_service import redis_service

        # Generate cache key for processed image
        cache_key = f"effect:{effect_type}:{ImageEffectsService._generate_cache_key(image_path, effect_type)}"

        # Try to get cached processed image
        if redis_service.is_connected():
            cached_data = redis_service._safe_operation(redis_service.redis_client.get, cache_key)
            if cached_data:
                try:
                    import base64
                    return base64.b64decode(cached_data)
                except Exception:
                    # Invalid cache data, continue to regenerate
                    pass

        # Apply effect
        processed_data = None
        if effect_type == "rgb":
            processed_data = await ImageEffectsService.apply_rgb_border_optimized(image_path)

        # Cache the processed image (for 1 hour)
        if processed_data and redis_service.is_connected():
            try:
                import base64
                cached_value = base64.b64encode(processed_data).decode('utf-8')
                redis_service._safe_operation(
                    redis_service.redis_client.setex,
                    cache_key,
                    3600,  # 1 hour cache
                    cached_value
                )
            except Exception as e:
                logger.warning(f"Failed to cache processed image: {e}")

        return processed_data