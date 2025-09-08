"""Configuration management for image processing."""

from math import gcd
from typing import Any, Dict, Optional, Tuple


class Configuration:
    """Manages aspect ratios, output sizes, and quality settings."""

    SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}

    MIN_REQUIREMENTS = {
        (1, 1): (1600, 1600),
        (16, 9): (3840, 2160),
        (21, 9): (3440, 1440),  # Ultrawide monitors
        (4, 3): (2048, 1536),
        (3, 2): (3456, 2304),
        (4, 5): (1600, 2000),  # Instagram portrait
        (9, 16): (810, 1440),
        (3, 4): (1536, 2048),
        (2, 3): (1024, 1536),
        (5, 1): (3840, 768),
        (8, 1): (3840, 480),
    }

    OUTPUT_CONFIGS = {
        (1, 1): {
            "folder": "square-1-1",
            "sizes": [
                (1600, 1600),  # High-res gallery/zoom
                (1080, 1080),  # Instagram full size
                (800, 800),  # Desktop grid
                (600, 600),  # Small desktop
                (400, 400),  # Mobile grid
                (200, 200),  # Thumbnail grid
                (100, 100),  # Small thumbnail
            ],
            "thumbnail_sizes": [(64, 64), (32, 32)],  # Icons and blur-up
        },
        (16, 9): {
            "folder": "landscape-16-9",
            "sizes": [
                (3840, 2160),  # 4K displays
                (2560, 1440),  # 1440p displays
                (1920, 1080),  # Full HD
                (1280, 720),  # HD/laptop
                (768, 432),  # Tablet
                (640, 360),  # Large mobile
                (390, 219),  # iPhone 14 Pro
                (375, 211),  # iPhone SE
            ],
            "thumbnail_sizes": [(160, 90), (64, 36), (32, 18)],  # Lazy load progression
        },
        (21, 9): {
            "folder": "ultrawide-21-9",
            "sizes": [
                (3440, 1440),  # Native ultrawide
                (2560, 1080),  # Smaller ultrawide
                (1920, 810),  # HD ultrawide
                (1280, 540),  # Laptop
                (768, 324),  # Tablet (fallback)
                (640, 270),  # Mobile (fallback)
            ],
            "thumbnail_sizes": [(210, 90), (105, 45)],  # Cinematic thumbs
        },
        (4, 3): {
            "folder": "landscape-4-3",
            "sizes": [
                (2048, 1536),  # High-res
                (1600, 1200),  # Desktop
                (1280, 960),  # Standard
                (1024, 768),  # iPad landscape
                (768, 576),  # Tablet
                (640, 480),  # Mobile landscape
                (400, 300),  # Mobile
            ],
            "thumbnail_sizes": [(160, 120), (80, 60), (32, 24)],
        },
        (3, 2): {
            "folder": "landscape-3-2",
            "sizes": [
                (3456, 2304),  # DSLR native
                (2400, 1600),  # High-res
                (1920, 1280),  # Desktop
                (1440, 960),  # Laptop
                (1200, 800),  # Small desktop
                (768, 512),  # Tablet
                (600, 400),  # Mobile landscape
                (375, 250),  # iPhone
            ],
            "thumbnail_sizes": [(150, 100), (75, 50), (30, 20)],
        },
        (4, 5): {
            "folder": "instagram-4-5",
            "sizes": [
                (1600, 2000),  # High-res export
                (1080, 1350),  # Instagram max
                (800, 1000),  # Desktop display
                (640, 800),  # Tablet
                (480, 600),  # Mobile landscape
                (400, 500),  # Mobile portrait
                (320, 400),  # Small mobile
            ],
            "thumbnail_sizes": [(160, 200), (80, 100), (32, 40)],
        },
        (9, 16): {
            "folder": "portrait-9-16",
            "sizes": [
                (1080, 1920),  # Stories/Reels HD
                (720, 1280),  # Standard stories
                (540, 960),  # Reduced quality
                (428, 761),  # iPhone 14 Pro Max
                (390, 693),  # iPhone 14 Pro
                (375, 667),  # iPhone SE
                (360, 640),  # Android
            ],
            "thumbnail_sizes": [(90, 160), (45, 80), (18, 32)],
        },
        (3, 4): {
            "folder": "portrait-3-4",
            "sizes": [
                (1536, 2048),  # iPad Pro portrait
                (1200, 1600),  # High-res
                (900, 1200),  # Desktop
                (768, 1024),  # iPad portrait
                (600, 800),  # Tablet
                (450, 600),  # Mobile
                (375, 500),  # iPhone portrait
            ],
            "thumbnail_sizes": [(150, 200), (75, 100), (30, 40)],
        },
        (2, 3): {
            "folder": "portrait-2-3",
            "sizes": [
                (1600, 2400),  # Print quality
                (1200, 1800),  # High-res
                (1000, 1500),  # Desktop
                (800, 1200),  # Standard
                (600, 900),  # Tablet
                (400, 600),  # Mobile
                (320, 480),  # Small mobile
            ],
            "thumbnail_sizes": [(160, 240), (80, 120), (32, 48)],
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
            "thumbnail_sizes": [(320, 64), (160, 32)],
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
            "thumbnail_sizes": [(320, 40), (160, 20)],
        },
    }

    @staticmethod
    def get_aspect_ratio(width: int, height: int) -> Tuple[int, int]:
        """Calculate simplified aspect ratio."""
        divisor = gcd(width, height)
        return (width // divisor, height // divisor)

    @classmethod
    def get_output_sizes(cls, aspect_ratio: Tuple[int, int]) -> Dict[str, Any]:
        """Get output sizes for aspect ratio."""
        return cls.OUTPUT_CONFIGS.get(aspect_ratio, {})

    @classmethod
    def get_output_sizes_with_override(
        cls, aspect_ratio: Tuple[int, int], overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
            base_config = {
                "folder": folder_name,
                "sizes": [],
                "thumbnail_sizes": [],
            }

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
