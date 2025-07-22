"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from img_velocity.core import (
    BatchProcessor,
    Configuration,
    ImageProcessor,
    ImageValidator,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def input_dir(temp_dir):
    """Create input directory with test structure."""
    input_path = temp_dir / "input"
    input_path.mkdir()
    return input_path


@pytest.fixture
def output_dir(temp_dir):
    """Create output directory."""
    output_path = temp_dir / "output"
    output_path.mkdir()
    return output_path


@pytest.fixture
def config():
    """Configuration instance."""
    return Configuration()


@pytest.fixture
def validator(config):
    """ImageValidator instance."""
    return ImageValidator(config)


@pytest.fixture
def processor(config):
    """ImageProcessor instance."""
    return ImageProcessor(config)


@pytest.fixture
def batch_processor():
    """BatchProcessor instance."""
    return BatchProcessor()


def create_test_image(
    path: Path,
    width: int,
    height: int,
    mode: str = "RGB",
    format: str = "JPEG",
    has_transparency: bool = False,
) -> Path:
    """Create a test image with specified dimensions and properties."""
    if has_transparency and mode == "RGB":
        mode = "RGBA"

    # Create image with gradient for visual testing
    if mode == "RGBA":
        img = Image.new(
            "RGBA", (width, height), (255, 0, 0, 128)
        )  # Semi-transparent red
        # Add some pattern
        for x in range(0, width, 10):
            for y in range(0, height, 10):
                if (x + y) % 20 == 0:
                    img.putpixel((x, y), (0, 255, 0, 255))  # Green pixels
    else:
        img = Image.new(mode, (width, height), "red")
        # Add gradient
        for x in range(width):
            for y in range(height):
                intensity = int((x + y) / (width + height) * 255)
                img.putpixel((x, y), (intensity, 0, 255 - intensity))

    img.save(path, format)
    return path


@pytest.fixture
def sample_images(input_dir):
    """Create comprehensive set of test images."""
    images = {}

    # Valid images that meet requirements
    images["square_large"] = create_test_image(
        input_dir / "square_large.jpg", 1600, 1600, format="JPEG"
    )
    images["landscape_16_9"] = create_test_image(
        input_dir / "landscape_16_9.jpg", 3840, 2160, format="JPEG"
    )
    images["portrait_9_16"] = create_test_image(
        input_dir / "portrait_9_16.png", 810, 1440, format="PNG"
    )
    images["wide_banner"] = create_test_image(
        input_dir / "wide_banner.webp", 3840, 768, format="WEBP"
    )

    # Images that don't meet requirements (too small)
    images["square_small"] = create_test_image(
        input_dir / "square_small.jpg", 800, 800, format="JPEG"
    )
    images["landscape_small"] = create_test_image(
        input_dir / "landscape_small.jpg", 1920, 1080, format="JPEG"
    )

    # Edge cases
    images["png_with_alpha"] = create_test_image(
        input_dir / "png_alpha.png", 1600, 1600, format="PNG", has_transparency=True
    )
    images["unusual_aspect"] = create_test_image(
        input_dir / "unusual.jpg",
        1500,
        1000,
        format="JPEG",  # 3:2 but small
    )
    images["very_wide"] = create_test_image(
        input_dir / "very_wide.jpg",
        4000,
        400,
        format="JPEG",  # 10:1
    )

    # Unsupported format (will be ignored)
    txt_file = input_dir / "not_image.txt"
    txt_file.write_text("This is not an image")

    # Corrupted file
    corrupt_file = input_dir / "corrupt.jpg"
    corrupt_file.write_bytes(b"Not a real JPEG file")

    return images


@pytest.fixture
def expected_outputs():
    """Expected output structure for different aspect ratios."""
    return {
        (1, 1): {
            "folder": "square-1-1",
            "sizes": [(1600, 1600), (800, 800), (400, 400), (300, 300), (200, 200)],
            "thumbnail_sizes": [(150, 150), (75, 75)],
        },
        (16, 9): {
            "folder": "landscape-16-9",
            "sizes": [
                (3840, 2160),
                (2048, 1152),
                (1920, 1080),
                (1024, 576),
                (856, 482),
                (428, 241),
            ],
            "thumbnail_sizes": [(320, 180), (214, 120), (160, 90)],
        },
        (9, 16): {
            "folder": "portrait-9-16",
            "sizes": [
                (810, 1440),
                (720, 1280),
                (540, 960),
                (405, 720),
                (360, 640),
                (270, 480),
            ],
            "thumbnail_sizes": [(135, 240), (90, 160), (67, 120)],
        },
    }


@pytest.fixture
def override_scenarios():
    """Different override parameter scenarios for testing."""
    return {
        "accept_all": {"accept_all": True},
        "aspect_16_9": {"aspect_ratio": (16, 9)},
        "resolution_1920": {"resolution": (1920, 1080)},
        "combined": {"aspect_ratio": (16, 9), "resolution": (1920, 1080)},
        "custom_aspect": {"aspect_ratio": (21, 9)},  # Ultra-wide
        "high_res": {"resolution": (4096, 2160)},
    }


@pytest.fixture
def performance_images(input_dir):
    """Create images for performance testing."""
    images = []

    # Create multiple large images for batch processing tests
    for i in range(5):
        img_path = create_test_image(
            input_dir / f"perf_test_{i}.jpg", 3840, 2160, format="JPEG"
        )
        images.append(img_path)

    return images


class MockProgressTracker:
    """Mock progress tracker for testing."""

    def __init__(self):
        self.calls = []

    def display_progress(self, current, total, elapsed_time, bar_width=40):
        self.calls.append(
            {"current": current, "total": total, "elapsed_time": elapsed_time}
        )


@pytest.fixture
def mock_progress_tracker():
    """Mock progress tracker."""
    return MockProgressTracker()
