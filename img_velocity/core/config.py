"""Configuration management for image processing."""

from math import gcd
from typing import Any, Optional


class Configuration:
    """Manages aspect ratios, output sizes, and quality settings."""

    SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}

    MIN_REQUIREMENTS = {
        (1, 1): (1600, 1600),
        (16, 9): (3840, 2160),
        (4, 3): (2048, 1536),
        (3, 2): (3456, 2304),
        (9, 16): (810, 1440),
        (3, 4): (1536, 2048),
        (2, 3): (1024, 1536),
        (5, 1): (3840, 768),
        (8, 1): (3840, 480),
    }

    OUTPUT_CONFIGS = {
        (1, 1): {
            "folder": "square-1-1",
            "sizes": [(1600, 1600), (800, 800), (400, 400), (300, 300), (200, 200)],
            "thumbnail_sizes": [(150, 150), (75, 75)],
        },
        (16, 9): {
            "folder": "landscape-16-9",
            "sizes": [
                (3840, 2160),
                (2048, 1152),
                (1920, 1080),
                (1024, 576),
                (856, 482),
                (428, 241),
            ],
            "thumbnail_sizes": [(320, 180), (214, 120), (160, 90)],
        },
        (4, 3): {
            "folder": "landscape-4-3",
            "sizes": [
                (2048, 1536),
                (1600, 1200),
                (1024, 768),
                (960, 720),
                (800, 600),
                (480, 360),
            ],
            "thumbnail_sizes": [(320, 240), (200, 150), (133, 100)],
        },
        (3, 2): {
            "folder": "landscape-3-2",
            "sizes": [
                (3456, 2304),
                (2048, 1366),
                (1728, 1152),
                (1024, 683),
                (960, 640),
                (480, 320),
            ],
            "thumbnail_sizes": [(300, 200), (225, 150), (150, 100)],
        },
        (9, 16): {
            "folder": "portrait-9-16",
            "sizes": [
                (810, 1440),
                (720, 1280),
                (540, 960),
                (405, 720),
                (360, 640),
                (270, 480),
            ],
            "thumbnail_sizes": [(135, 240), (90, 160), (67, 120)],
        },
        (3, 4): {
            "folder": "portrait-3-4",
            "sizes": [(1536, 2048), (1200, 1600), (768, 1024), (600, 800), (300, 400)],
            "thumbnail_sizes": [(225, 300), (150, 200), (75, 100)],
        },
        (2, 3): {
            "folder": "portrait-2-3",
            "sizes": [
                (1024, 1536),
                (800, 1200),
                (640, 960),
                (512, 768),
                (400, 600),
                (320, 480),
            ],
            "thumbnail_sizes": [(200, 300), (134, 200), (100, 150)],
        },
        (5, 1): {
            "folder": "wide-banner-5-1",
            "sizes": [
                (3840, 768),
                (2048, 410),
                (1920, 384),
                (1024, 205),
                (856, 172),
                (428, 86),
            ],
            "thumbnail_sizes": [],
        },
        (8, 1): {
            "folder": "slim-banner-8-1",
            "sizes": [
                (3840, 480),
                (2048, 256),
                (1920, 240),
                (1024, 128),
                (856, 108),
                (428, 54),
            ],
            "thumbnail_sizes": [],
        },
    }

    @staticmethod
    def get_aspect_ratio(width: int, height: int) -> tuple[int, int]:
        """Calculate simplified aspect ratio."""
        divisor = gcd(width, height)
        return (width // divisor, height // divisor)

    @classmethod
    def get_output_sizes(
        cls, aspect_ratio: tuple[int, int]
    ) -> dict[str, list[tuple[int, int]]]:
        """Get output sizes for aspect ratio."""
        return cls.OUTPUT_CONFIGS.get(aspect_ratio, {})

    @classmethod
    def get_output_sizes_with_override(
        cls, aspect_ratio: tuple[int, int], overrides: Optional[dict[str, Any]] = None
    ) -> dict[str, list[tuple[int, int]]]:
        """Get output sizes for aspect ratio, considering overrides."""
        if not overrides:
            return cls.get_output_sizes(aspect_ratio)

        # Determine target aspect ratio
        if overrides.get("accept_all", False) and "aspect_ratio" not in overrides:
            target_aspect_ratio = aspect_ratio
        else:
            target_aspect_ratio = overrides.get("aspect_ratio", aspect_ratio)

        # Get base configuration
        base_config = cls.get_output_sizes(target_aspect_ratio)
        if not base_config:
            folder_name = f"custom-{target_aspect_ratio[0]}-{target_aspect_ratio[1]}"
            base_config = {"folder": folder_name, "sizes": [], "thumbnail_sizes": []}

        # Handle resolution override
        if "resolution" in overrides:
            override_width, override_height = overrides["resolution"]

            # Generate sizes by scaling down from override resolution
            sizes = [(override_width, override_height)]
            scale_factors = [0.75, 0.5, 0.375, 0.25, 0.125]

            for factor in scale_factors:
                new_width = int(override_width * factor)
                new_height = int(override_height * factor)
                if new_width >= 50 and new_height >= 50:
                    sizes.append((new_width, new_height))

            # Generate thumbnail sizes - ensure they're smaller than smallest main size
            thumbnail_sizes = []
            if sizes:
                # Calculate smallest main size area and dimensions
                min_main_area = min(w * h for w, h in sizes)
                min_main_width = min(w for w, h in sizes)
                min_main_height = min(h for w, h in sizes)

                # Use very small factors and strict dimension checks
                thumb_factors = [0.05, 0.03, 0.02]  # Even smaller factors
                for factor in thumb_factors:
                    thumb_width = int(override_width * factor)
                    thumb_height = int(override_height * factor)
                    thumb_area = thumb_width * thumb_height

                    # Multiple checks: area, width, height must all be smaller
                    if (
                        thumb_area < min_main_area
                        and thumb_width < min_main_width
                        and thumb_height < min_main_height
                        and thumb_width >= 25
                        and thumb_height >= 25
                    ):  # Minimum reasonable size
                        thumbnail_sizes.append((thumb_width, thumb_height))

            return {
                "folder": base_config["folder"],
                "sizes": sizes,
                "thumbnail_sizes": thumbnail_sizes,
            }

        return base_config

    @staticmethod
    def get_webp_quality(width: int, height: int, is_thumbnail: bool = False) -> int:
        """Calculate optimal WebP quality based on dimensions."""
        max_dim = max(width, height)

        if is_thumbnail:
            return 55 if max_dim <= 100 else 65
        if max_dim <= 800:
            return 80
        if max_dim <= 2000:
            return 85
        return 82
