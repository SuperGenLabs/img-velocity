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
    """
    from pathlib import Path
    
    processor = BatchProcessor()
    return processor.process_images(
        Path(input_dir),
        Path(output_dir),
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
    """
    from pathlib import Path
    
    config = Configuration()
    validator = ImageValidator(config)
    processor = ImageProcessor(config)
    
    image_info = validator.get_image_info(Path(image_path))
    if not image_info:
        return {"status": "error", "source": image_path, "error": "Invalid image"}
        
    if not validator.meets_requirements_with_override(image_info, overrides):
        return {"status": "skipped", "source": image_path, "reason": "requirements"}
        
    return processor.process_image(
        image_info,
        Path(output_dir),
        thumbnails,
        overrides,
    )
