"""Generate responsive WebP image sets with intelligent compression for faster web performance."""

from .cli import CLIParser
from .core import BatchProcessor, Configuration, ImageProcessor, ImageValidator
from .utils import FileSystemUtils, ProgressTracker

__version__ = "0.1.0"

__all__ = [
    "Configuration",
    "ImageValidator",
    "ImageProcessor",
    "BatchProcessor",
    "CLIParser",
    "ProgressTracker",
    "FileSystemUtils",
    "process_images",
    "process_single_image",
]


def process_images(
    input_dir,
    output_dir,
    thumbnails=False,
    workers=None,
    overrides=None,
):
    """
    Process multiple images from a directory.

    Args:
        input_dir: Path to input directory containing images
        output_dir: Path to output directory for WebP variants
        thumbnails: Generate thumbnail variants
        workers: Number of parallel workers (None for auto)
        overrides: Override requirements dict

    Returns:
        List of processing results

    Raises:
        ValueError: If paths or parameters are invalid
    """
    from pathlib import Path

    from .utils.security import SecurityValidator

    # Validate paths
    input_dir = SecurityValidator.validate_path(Path(input_dir))
    output_dir = SecurityValidator.validate_path(Path(output_dir))

    # Validate workers
    workers = SecurityValidator.validate_worker_count(workers)

    processor = BatchProcessor()
    return processor.process_images(
        input_dir,
        output_dir,
        thumbnails,
        workers,
        overrides,
    )


def process_single_image(
    image_path,
    output_dir,
    thumbnails=False,
    overrides=None,
):
    """
    Process a single image file.

    Args:
        image_path: Path to image file
        output_dir: Path to output directory
        thumbnails: Generate thumbnail variants
        overrides: Override requirements dict

    Returns:
        Processing result dict

    Raises:
        ValueError: If paths are invalid
    """
    from pathlib import Path

    from .utils.security import SecurityValidator

    # Validate paths
    image_path = SecurityValidator.validate_path(Path(image_path))
    output_dir = SecurityValidator.validate_path(Path(output_dir))

    config = Configuration()
    validator = ImageValidator(config)
    processor = ImageProcessor(config)

    image_info = validator.get_image_info(image_path)
    if not image_info:
        return {"status": "error", "source": str(image_path), "error": "Invalid image"}

    if not validator.meets_requirements_with_override(image_info, overrides):
        return {
            "status": "skipped",
            "source": str(image_path),
            "reason": "requirements",
        }

    return processor.process_image(
        image_info,
        output_dir,
        thumbnails,
        overrides,
    )
