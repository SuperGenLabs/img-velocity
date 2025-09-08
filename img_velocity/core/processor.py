"""Image processing with smart compression and resizing."""

import logging
from pathlib import Path

from PIL import Image, ImageFilter

from ..utils.helpers import sanitize_filename
from ..utils.logging import get_logger
from ..utils.security import SecurityValidator
from .config import Configuration

logger = get_logger(__name__.split('.')[-1])


class ImageProcessor:
    """Handles individual image processing with smart compression."""

    def __init__(self, config: Configuration):
        self.config = config

    def apply_smart_sharpening(
        self,
        img: Image.Image,
        original_size: tuple[int, int],
        target_size: tuple[int, int],
    ) -> Image.Image:
        """Apply smart sharpening based on downscale factor."""
        original_width, original_height = original_size
        target_width, target_height = target_size

        # Calculate scale factor (use the smaller dimension to be conservative)
        scale_factor = min(
            target_width / original_width, target_height / original_height
        )

        # Only apply sharpening if we're downscaling significantly
        if scale_factor >= 0.75:
            # No sharpening needed for minimal downscaling or upscaling
            return img
        if scale_factor >= 0.5:
            # Medium sharpening for moderate downscaling
            sharpening_filter = ImageFilter.UnsharpMask(
                radius=1, percent=150, threshold=3
            )
            return img.filter(sharpening_filter)
        # Strong sharpening for significant downscaling
        sharpening_filter = ImageFilter.UnsharpMask(
            radius=1.5, percent=200, threshold=2
        )
        return img.filter(sharpening_filter)

    def process_single_size(
        self, args: tuple[Path, Path, tuple[int, int], tuple[int, int], bool, Path]
    ) -> dict[str, any] | None:
        """Process a single image size variant."""
        (
            source_path,
            output_path,
            target_size,
            original_size,
            is_thumbnail,
            output_dir,
        ) = args

        try:
            # Validate output path stays within output_dir
            output_path = SecurityValidator.validate_path(output_path, output_dir)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Open and process image
            with Image.open(source_path) as img:
                # Convert to RGB if needed (preserving transparency for RGBA)
                if img.mode == "P":
                    # Handle palette images
                    if "transparency" in img.info:
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")
                elif img.mode in ("RGBA", "LA"):
                    # Keep transparency
                    pass
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize image
                resized_img = img.resize(target_size, Image.Resampling.LANCZOS)

                # Apply smart sharpening
                sharpened_img = self.apply_smart_sharpening(
                    resized_img, original_size, target_size
                )

                # Get quality setting
                quality = self.config.get_webp_quality(
                    target_size[0], target_size[1], is_thumbnail
                )

                # Save as WebP
                save_kwargs = {
                    "format": "WebP",
                    "quality": quality,
                    "method": 6,  # Maximum compression effort
                }

                # Handle transparency
                if sharpened_img.mode in ("RGBA", "LA"):
                    save_kwargs["lossless"] = (
                        False  # Use lossy compression even with transparency
                    )

                sharpened_img.save(output_path, **save_kwargs)

                # Return result info
                return {
                    "path": str(output_path.relative_to(output_dir)),
                    "width": target_size[0],
                    "height": target_size[1],
                    "size": output_path.stat().st_size,
                    "type": "thumbnail" if is_thumbnail else "standard",
                }

        except Exception as e:
            # Log error but don't crash
            logger.warning(f"Failed to process {source_path} -> {output_path}: {e}")
            return None

    def process_image(
        self,
        image_info: dict[str, any],
        output_dir: Path,
        thumbnails: bool = False,
        overrides: dict[str, any] | None = None,
    ) -> dict[str, any]:
        """Process a single image into all required variants."""
        source_path = image_info["path"]
        aspect_ratio = image_info["aspect_ratio"]
        original_size = (image_info["width"], image_info["height"])

        # Get output configuration
        output_config = self.config.get_output_sizes_with_override(
            aspect_ratio, overrides
        )

        if not output_config:
            return {
                "status": "skipped",
                "source": source_path.name,
                "reason": "unsupported_aspect_ratio",
            }

        # Create sanitized filename base
        base_filename = sanitize_filename(source_path.stem)

        # Create output directory structure with validation
        output_subdir = output_dir / output_config["folder"] / base_filename
        try:
            output_subdir = SecurityValidator.validate_path(output_subdir, output_dir)
        except ValueError as e:
            logger.error(f"Invalid output path for {source_path.name}: {e}")
            return {
                "status": "error",
                "source": source_path.name,
                "error": str(e)
            }
        output_subdir.mkdir(parents=True, exist_ok=True)

        variants = []

        try:
            # Process standard sizes
            for width, height in output_config["sizes"]:
                output_filename = f"{base_filename}-{width}x{height}.webp"
                output_path = output_subdir / output_filename

                args = (
                    source_path,
                    output_path,
                    (width, height),
                    original_size,
                    False,
                    output_dir,
                )
                result = self.process_single_size(args)

                if result:
                    variants.append(result)

            # Process thumbnails if requested
            if thumbnails and output_config["thumbnail_sizes"]:
                for width, height in output_config["thumbnail_sizes"]:
                    output_filename = f"thumbnail-{base_filename}-{width}x{height}.webp"
                    output_path = output_subdir / output_filename

                    args = (
                        source_path,
                        output_path,
                        (width, height),
                        original_size,
                        True,
                        output_dir,
                    )
                    result = self.process_single_size(args)

                    if result:
                        variants.append(result)

            return {
                "status": "success",
                "source": source_path.name,
                "aspect_ratio": f"{aspect_ratio[0]}:{aspect_ratio[1]}",
                "variants": variants,
            }

        except Exception as e:
            return {"status": "error", "source": source_path.name, "error": str(e)}
