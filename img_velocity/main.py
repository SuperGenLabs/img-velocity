#!/usr/bin/env python3
"""Main entry point for img-velocity."""

import multiprocessing
from pathlib import Path

from .cli import CLIParser
from .core import BatchProcessor


def main():
    """Main entry point."""
    # Fix for PyInstaller multiprocessing on Windows
    multiprocessing.freeze_support()

    # Parse command line arguments
    cli_parser = CLIParser()
    args = cli_parser.parse_args()

    # Create batch processor
    batch_processor = BatchProcessor()

    # Execute the appropriate action
    if args.benchmark:
        batch_processor.benchmark_workers(
            Path(args.input_dir), Path(args.output_dir), args.thumbnails, args.overrides
        )
    else:
        batch_processor.process_images(
            Path(args.input_dir),
            Path(args.output_dir),
            args.thumbnails,
            args.workers,
            args.overrides,
        )


if __name__ == "__main__":
    main()
