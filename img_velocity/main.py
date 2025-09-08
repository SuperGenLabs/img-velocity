#!/usr/bin/env python3
"""Main entry point for img-velocity."""

import multiprocessing
import sys
from pathlib import Path

from .cli import CLIParser
from .core import BatchProcessor
from .utils.logging import setup_logging


def main():
    """Main entry point."""
    # Fix for PyInstaller multiprocessing on Windows
    multiprocessing.freeze_support()

    # Parse command line arguments
    cli_parser = CLIParser()
    args = cli_parser.parse_args()

    # Set up logging with level from CLI args
    log_level = getattr(args, "log_level", "INFO")
    logger = setup_logging(level=log_level)

    # Create batch processor
    batch_processor = BatchProcessor()

    # Execute the appropriate action
    if args.benchmark:
        # Benchmark mode: use the benchmark argument as input dir
        batch_processor.benchmark_workers(
            Path(args.benchmark), args.thumbnails, args.overrides
        )
    else:
        # Normal processing mode: require both input and output dirs
        if not args.input_dir or not args.output_dir:
            logger.error("input_dir and output_dir are required for processing")
            logger.info("Usage: img-velocity input_dir output_dir [options]")
            logger.info("   or: img-velocity --benchmark input_dir")
            sys.exit(1)

        batch_processor.process_images(
            Path(args.input_dir),
            Path(args.output_dir),
            args.thumbnails,
            args.workers,
            args.overrides,
        )


if __name__ == "__main__":
    main()
