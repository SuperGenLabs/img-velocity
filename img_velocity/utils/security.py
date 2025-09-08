"""Security utilities for input validation and path sanitization."""

import re
from pathlib import Path
from typing import Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger(__name__.split(".")[-1])


class SecurityValidator:
    """Validates and sanitizes user inputs for security."""

    # Characters not allowed in filenames
    UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')

    # Maximum path component length (common filesystem limit)
    MAX_FILENAME_LENGTH = 255
    MAX_PATH_LENGTH = 4096

    @staticmethod
    def validate_path(path: Path, base_dir: Optional[Path] = None) -> Path:
        """
        Validate and sanitize a file path to prevent directory traversal.

        Args:
            path: Path to validate
            base_dir: Optional base directory to ensure path stays within

        Returns:
            Validated absolute path

        Raises:
            ValueError: If path is invalid or attempts directory traversal
        """
        # Convert to Path object if string
        if isinstance(path, str):
            path = Path(path)

        # Resolve to absolute path (follows symlinks and removes ..)
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {path}") from e

        # Check path length
        if len(str(resolved_path)) > SecurityValidator.MAX_PATH_LENGTH:
            raise ValueError(f"Path too long: {resolved_path}")

        # If base_dir specified, ensure path is within it
        if base_dir:
            base_dir = base_dir.resolve()
            try:
                # This will raise ValueError if path is not relative to base_dir
                resolved_path.relative_to(base_dir)
            except ValueError:
                raise ValueError(
                    f"Path '{resolved_path}' is outside allowed directory '{base_dir}'"
                ) from None

        # Check for null bytes (can terminate strings early in some contexts)
        if "\x00" in str(resolved_path):
            raise ValueError("Path contains null bytes")

        return resolved_path

    @staticmethod
    def sanitize_filename(filename: str, allow_dots: bool = True) -> str:
        """
        Sanitize a filename to be safe for filesystem operations.

        Args:
            filename: Filename to sanitize
            allow_dots: Whether to allow dots (for extensions)

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove path separators to prevent directory traversal
        filename = filename.replace("/", "").replace("\\", "")

        # Remove unsafe characters
        filename = SecurityValidator.UNSAFE_FILENAME_CHARS.sub("", filename)

        # Handle dots
        if not allow_dots:
            filename = filename.replace(".", "")
        else:
            # Prevent hidden files and directory traversal via ..
            while filename.startswith("."):
                filename = filename[1:]
            filename = filename.replace("..", "")

        # Limit length
        if len(filename) > SecurityValidator.MAX_FILENAME_LENGTH:
            # Preserve extension if present
            from pathlib import Path

            p = Path(filename)
            ext = p.suffix
            name = p.stem
            max_name_length = SecurityValidator.MAX_FILENAME_LENGTH - len(ext)
            filename = name[:max_name_length] + ext

        # Final validation
        if not filename or filename in (".", ".."):
            raise ValueError("Invalid filename after sanitization")

        return filename

    @staticmethod
    def validate_image_path(image_path: Path, base_dir: Path) -> Path:
        """
        Validate an image file path with additional image-specific checks.

        Args:
            image_path: Path to image file
            base_dir: Base directory containing images

        Returns:
            Validated path

        Raises:
            ValueError: If path is invalid or not an image file
        """
        # First do general path validation
        validated_path = SecurityValidator.validate_path(image_path, base_dir)

        # Check file extension
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
        if validated_path.suffix.lower() not in allowed_extensions:
            raise ValueError(f"Invalid image file extension: {validated_path.suffix}")

        # Ensure it's a file, not a directory
        if validated_path.exists() and validated_path.is_dir():
            raise ValueError(f"Path is a directory, not a file: {validated_path}")

        return validated_path

    @staticmethod
    def validate_resolution(width: int, height: int) -> Tuple[int, int]:
        """
        Validate image resolution values.

        Args:
            width: Image width
            height: Image height

        Returns:
            Validated (width, height) tuple

        Raises:
            ValueError: If resolution is invalid
        """
        # Check types
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("Resolution must be integers")

        # Check ranges (prevent DoS via huge allocations)
        min_dimension = 1
        max_dimension = 50000  # Reasonable max for image processing

        if not (min_dimension <= width <= max_dimension):
            raise ValueError(
                f"Width {width} outside valid range {min_dimension}-{max_dimension}"
            )

        if not (min_dimension <= height <= max_dimension):
            raise ValueError(
                f"Height {height} outside valid range {min_dimension}-{max_dimension}"
            )

        return (width, height)

    @staticmethod
    def validate_worker_count(workers: Optional[int]) -> Optional[int]:
        """
        Validate worker count for multiprocessing.

        Args:
            workers: Number of workers or None for auto

        Returns:
            Validated worker count

        Raises:
            ValueError: If worker count is invalid
        """
        if workers is None:
            return None

        if not isinstance(workers, int):
            raise ValueError("Worker count must be an integer")

        if workers < 1:
            raise ValueError("Worker count must be at least 1")

        # Reasonable upper limit to prevent resource exhaustion
        max_workers = 100
        if workers > max_workers:
            raise ValueError(f"Worker count cannot exceed {max_workers}")

        return workers
