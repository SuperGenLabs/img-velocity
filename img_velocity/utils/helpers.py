"""General utility functions."""

import math
import re
from typing import Any


def format_time(seconds: float) -> str:
    """Format seconds into human readable time."""
    if seconds < 60:
        # Use ceiling for values >= 0.5 to ensure 0.5 becomes 1
        return f"{math.ceil(seconds) if seconds >= 0.5 else int(round(seconds))}s"
    if seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:.0f}h {minutes:.0f}m"


def sanitize_filename(filename: str) -> str:
    """Replace spaces and underscores with hyphens, convert to lowercase."""
    sanitized = filename.lower().replace(" ", "-").replace("_", "-")
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    return sanitized.strip("-")


def parse_override_params(override_args: list[str]) -> dict[str, Any]:
    """Parse override parameters from command line arguments."""
    overrides = {}

    # If no arguments provided with --override, it means accept all images
    if not override_args:
        overrides["accept_all"] = True
        return overrides

    for arg in override_args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key == "aspect-ratio":
                # Parse aspect ratio like "16:9"
                match = re.match(r"^(\d+):(\d+)$", value)
                if match:
                    w, h = int(match.group(1)), int(match.group(2))
                    overrides["aspect_ratio"] = (w, h)
                else:
                    raise ValueError(
                        f"Invalid aspect ratio format: {value}. Use format like '16:9'"
                    )
            elif key == "resolution":
                # Parse resolution like "1920x1080" - handle extra equals signs in value
                clean_value = value.split("=")[
                    0
                ]  # Take only the part before any additional equals
                match = re.match(r"^(\d+)x(\d+)$", clean_value)
                if match:
                    w, h = int(match.group(1)), int(match.group(2))
                    overrides["resolution"] = (w, h)
                else:
                    raise ValueError(
                        f"Invalid resolution format: {clean_value}. Use format like '1920x1080'"
                    )
            else:
                raise ValueError(f"Unknown override parameter: {key}")
        else:
            raise ValueError(
                f"Override parameter must be in format key=value, got: {arg}"
            )

    return overrides
