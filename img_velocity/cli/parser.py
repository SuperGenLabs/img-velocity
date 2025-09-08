"""Command line interface parsing."""

import argparse
import sys

from ..utils.helpers import parse_override_params
from ..utils.logging import get_logger

logger = get_logger(__name__.split(".")[-1])


class CLIParser:
    """Handles command line argument parsing and validation."""

    def __init__(self):
        self.parser = self._create_parser()
        self.original_argv = None  # Initialize original_argv attribute

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Convert images to multiple WebP sizes with smart optimization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Usage examples:
  img-velocity input/ output/                    # Process images
  img-velocity input/ output/ --thumbnails       # Include thumbnails
  img-velocity --benchmark input/                # Find optimal worker count

Supported input formats: JPEG, PNG, WebP

Minimum size requirements by aspect ratio:
  • Square (1:1): 1600×1600
  • Landscape 16:9: 3840×2160
  • Landscape 21:9: 3440×1440  # Ultrawide
  • Landscape 4:3: 2048×1536
  • Landscape 3:2: 3456×2304
  • Instagram 4:5: 1600×2000
  • Portrait 9:16: 810×1440
  • Portrait 3:4: 1536×2048
  • Portrait 2:3: 1024×1536
  • Wide banner 5:1: 3840×768
  • Slim banner 8:1: 3840×480

Override options:
  --override                          Accept all images (no requirements)
  --override aspect-ratio="16:9"      Accept only 16:9 aspect ratio images
  --override resolution="1920x1080"   Accept images >= 1920x1080 resolution
  --override aspect-ratio="16:9" resolution="1920x1080"  Combined requirements

When using overrides:
  • Images are processed based on override criteria instead of defaults
  • Output folders use the target aspect ratio structure
  • Resolution overrides set the maximum output size (scales down from there)
  • Custom aspect ratios create folders like "custom-16-9"

Benchmark mode:
  • Tests different worker counts (1, CPU/2, CPU, CPU*2, etc.)
  • Uses system temp directory for test output
  • Recommends optimal --workers value for your system
  • Tests with first 10 valid images from input directory

Features:
  • Parallel processing for speed
  • Smart sharpening for downscaled images
  • Metadata stripping for smaller files
  • Automatic filename sanitization
  • Output validation
  • Manifest generation for web integration
            """,
        )

        parser.add_argument(
            "input_dir", nargs="?", help="Input directory containing images"
        )
        parser.add_argument(
            "output_dir", nargs="?", help="Output directory for WebP variants"
        )
        parser.add_argument(
            "--thumbnails", action="store_true", help="Generate thumbnail variants"
        )
        parser.add_argument("--workers", type=int, help="Number of parallel workers")
        parser.add_argument(
            "--benchmark",
            metavar="INPUT_DIR",
            help="Benchmark different worker counts using images from INPUT_DIR",
        )
        parser.add_argument(
            "--override",
            nargs="*",
            help='Override requirements. Usage: --override [aspect-ratio="16:9"] [resolution="1920x1080"]',
        )
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Set logging level (default: INFO)",
        )

        return parser

    def filter_multiprocessing_args(self) -> None:
        """Filter out PyInstaller multiprocessing arguments that interfere with argparse."""
        filtered_args = []
        skip_next = False

        for i, arg in enumerate(sys.argv[1:], 1):
            if skip_next:
                skip_next = False
                continue
            if arg.startswith("--multiprocessing-fork"):
                # Skip this argument and potentially the next one if it's a separate value
                if "=" not in arg and i < len(sys.argv) - 1:
                    skip_next = True
                continue
            filtered_args.append(arg)

        # Temporarily replace sys.argv for argparse
        self.original_argv = sys.argv[1:]
        sys.argv[1:] = filtered_args

    def restore_argv(self) -> None:
        """Restore original sys.argv."""
        if hasattr(self, "original_argv") and self.original_argv is not None:
            sys.argv[1:] = self.original_argv

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        self.filter_multiprocessing_args()

        try:
            args = self.parser.parse_args()

            # Parse override parameters
            if args.override is not None:
                try:
                    args.overrides = parse_override_params(args.override)
                except ValueError as e:
                    logger.error(f"Error parsing override parameters: {e}")
                    sys.exit(1)
            else:
                args.overrides = None

            return args

        finally:
            self.restore_argv()
