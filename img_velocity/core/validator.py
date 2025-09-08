"""Image validation and requirements checking."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from .config import Configuration


class ImageValidator:
    """Validates images against requirements and overrides."""

    def __init__(self, config: Configuration):
        self.config = config

    def get_image_info(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Get image information if it's a supported format."""
        try:
            with Image.open(image_path) as img:
                if img.format and img.format.upper() in self.config.SUPPORTED_FORMATS:
                    width, height = img.size
                    aspect_ratio = self.config.get_aspect_ratio(width, height)
                    return {
                        "path": image_path,
                        "width": width,
                        "height": height,
                        "aspect_ratio": aspect_ratio,
                        "format": img.format,
                    }
        except Exception:
            pass
        return None

    def meets_requirements(self, info: Dict[str, Any]) -> bool:
        """Check if image meets minimum size requirements."""
        aspect_ratio = info["aspect_ratio"]
        if aspect_ratio not in self.config.MIN_REQUIREMENTS:
            return False

        min_width, min_height = self.config.MIN_REQUIREMENTS[aspect_ratio]
        return info["width"] >= min_width and info["height"] >= min_height

    def meets_requirements_with_override(
        self, info: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if image meets requirements, considering overrides."""
        if not overrides:
            return self.meets_requirements(info)

        # Accept all override
        if overrides.get("accept_all", False):
            return True

        # Aspect ratio override
        if (
            "aspect_ratio" in overrides
            and info["aspect_ratio"] != overrides["aspect_ratio"]
        ):
            return False

        # Resolution override
        if "resolution" in overrides:
            override_width, override_height = overrides["resolution"]
            return info["width"] >= override_width and info["height"] >= override_height

        # Only aspect ratio override (no resolution)
        if "aspect_ratio" in overrides and "resolution" not in overrides:
            temp_info = info.copy()
            temp_info["aspect_ratio"] = overrides["aspect_ratio"]
            return self.meets_requirements(temp_info)

        # No overrides, use default logic
        return self.meets_requirements(info)
