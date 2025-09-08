"""Logging configuration for img-velocity."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Optional custom format string

    Returns:
        Configured logger instance
    """
    # Default format for console output (simplified)
    console_format = format_string or "%(levelname)s: %(message)s"

    # File format includes timestamp and module info
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Get root logger
    logger = logging.getLogger("img_velocity")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(logging.Formatter(console_format))
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # File gets everything DEBUG and above
        file_handler.setFormatter(logging.Formatter(file_format))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"img_velocity.{name}")


class ProgressHandler(logging.Handler):
    """Custom handler that doesn't interfere with progress bars."""

    def __init__(self, progress_tracker=None):
        super().__init__()
        self.progress_tracker = progress_tracker

    def emit(self, record):
        """Emit a log record, clearing progress bar if needed."""
        if self.progress_tracker and self.progress_tracker.active:
            # Clear the progress bar line
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()

        # Output the log message
        msg = self.format(record)
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

        # Redraw progress bar if it was active
        if self.progress_tracker and self.progress_tracker.active:
            self.progress_tracker.redraw()
