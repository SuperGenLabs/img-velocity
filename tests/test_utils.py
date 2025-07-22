"""Comprehensive tests for utility functions and classes."""

import json
from unittest.mock import MagicMock, patch

import pytest

from img_velocity.utils.filesystem import FileSystemUtils
from img_velocity.utils.helpers import (
    format_time,
    parse_override_params,
    sanitize_filename,
)
from img_velocity.utils.progress import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initializes correctly."""
        tracker = ProgressTracker()
        assert isinstance(tracker, ProgressTracker)

    @patch("shutil.get_terminal_size")
    def test_display_progress_basic(self, mock_terminal_size, capsys):
        """Test basic progress display."""
        mock_terminal_size.return_value = MagicMock(columns=80)

        tracker = ProgressTracker()
        tracker.display_progress(5, 10, 25.0)

        captured = capsys.readouterr()

        # Should show progress bar
        assert "[" in captured.out
        assert "]" in captured.out
        assert "5/10" in captured.out
        assert "50.0%" in captured.out
        assert "ETA:" in captured.out

    @patch("shutil.get_terminal_size")
    def test_display_progress_eta_calculation(self, mock_terminal_size, capsys):
        """Test ETA calculation in progress display."""
        mock_terminal_size.return_value = MagicMock(columns=80)

        tracker = ProgressTracker()

        # Test with current > 0 (should calculate ETA)
        tracker.display_progress(2, 10, 20.0)
        captured = capsys.readouterr()
        assert "ETA:" in captured.out
        assert "calculating" not in captured.out

        # Test with current = 0 (should show "calculating")
        tracker.display_progress(0, 10, 0.0)
        captured = capsys.readouterr()
        assert "ETA: calculating" in captured.out

    @patch("shutil.get_terminal_size")
    def test_display_progress_terminal_width_adaptation(
        self, mock_terminal_size, capsys
    ):
        """Test progress bar adapts to terminal width."""
        # Test with narrow terminal
        mock_terminal_size.return_value = MagicMock(columns=50)

        tracker = ProgressTracker()
        tracker.display_progress(5, 10, 10.0)

        captured = capsys.readouterr()

        # Should still display something reasonable
        assert len(captured.out) <= 50
        assert "5/10" in captured.out

    @patch("shutil.get_terminal_size")
    def test_display_progress_very_narrow_terminal(self, mock_terminal_size, capsys):
        """Test progress display with very narrow terminal."""
        # Very narrow terminal that forces minimal display
        mock_terminal_size.return_value = MagicMock(columns=20)

        tracker = ProgressTracker()
        tracker.display_progress(7, 20, 15.0)

        captured = capsys.readouterr()

        # Should show minimal version
        assert "7/20" in captured.out
        assert "%" in captured.out

    def test_display_progress_terminal_error_handling(self, capsys):
        """Test progress display handles terminal size errors."""
        with patch("shutil.get_terminal_size", side_effect=OSError("Terminal error")):
            tracker = ProgressTracker()
            tracker.display_progress(3, 8, 12.0)

            captured = capsys.readouterr()

            # Should still work with fallback
            assert "3/8" in captured.out
            assert "%" in captured.out

    @patch("shutil.get_terminal_size")
    def test_display_progress_custom_bar_width(self, mock_terminal_size, capsys):
        """Test progress display with custom bar width."""
        mock_terminal_size.return_value = MagicMock(columns=120)

        tracker = ProgressTracker()
        tracker.display_progress(6, 12, 30.0, bar_width=60)

        captured = capsys.readouterr()

        # Should use custom bar width
        assert "6/12" in captured.out
        assert "50.0%" in captured.out

    @patch("shutil.get_terminal_size")
    def test_display_progress_with_current_file(self, mock_terminal_size, capsys):
        """Test progress display with custom bar width parameter."""
        mock_terminal_size.return_value = MagicMock(columns=100)

        tracker = ProgressTracker()
        tracker.display_progress(3, 7, 18.0, bar_width=50)

        captured = capsys.readouterr()

        # Should display progress with custom bar width
        assert "3/7" in captured.out
        assert "42.9%" in captured.out

    @pytest.mark.parametrize(
        "current,total,expected_percent",
        [
            (0, 10, 0.0),
            (5, 10, 50.0),
            (10, 10, 100.0),
            (1, 3, 33.3),
            (2, 3, 66.7),
        ],
    )
    @patch("shutil.get_terminal_size")
    def test_display_progress_percentage_calculation(
        self, mock_terminal_size, current, total, expected_percent, capsys
    ):
        """Test percentage calculation in progress display."""
        mock_terminal_size.return_value = MagicMock(columns=80)

        tracker = ProgressTracker()
        tracker.display_progress(current, total, 10.0)

        captured = capsys.readouterr()
        assert f"{expected_percent:.1f}%" in captured.out


class TestFileSystemUtils:
    """Test FileSystemUtils class."""

    def test_filesystem_utils_initialization(self):
        """Test FileSystemUtils initializes correctly."""
        fs_utils = FileSystemUtils()
        assert isinstance(fs_utils, FileSystemUtils)

    def test_generate_manifest_basic(self, temp_dir):
        """Test basic manifest generation."""
        fs_utils = FileSystemUtils()

        results = [
            {
                "status": "success",
                "source": "image1.jpg",
                "aspect_ratio": "16:9",
                "variants": [
                    {
                        "path": "landscape-16-9/image1/image1-1920x1080.webp",
                        "width": 1920,
                        "height": 1080,
                        "size": 150000,
                        "type": "standard",
                    },
                    {
                        "path": "landscape-16-9/image1/image1-1024x576.webp",
                        "width": 1024,
                        "height": 576,
                        "size": 75000,
                        "type": "standard",
                    },
                ],
            },
            {
                "status": "success",
                "source": "image2.jpg",
                "aspect_ratio": "1:1",
                "variants": [
                    {
                        "path": "square-1-1/image2/image2-1600x1600.webp",
                        "width": 1600,
                        "height": 1600,
                        "size": 200000,
                        "type": "standard",
                    }
                ],
            },
        ]

        fs_utils.generate_manifest(results, temp_dir)

        # Verify manifest file was created
        manifest_path = temp_dir / "manifest.json"
        assert manifest_path.exists()

        # Verify manifest content
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["version"] == "1.0"
        assert "images" in manifest
        assert len(manifest["images"]) == 2

        # Check first image
        assert "image1.jpg" in manifest["images"]
        img1_data = manifest["images"]["image1.jpg"]
        assert img1_data["aspect_ratio"] == "16:9"
        assert len(img1_data["variants"]) == 2

        # Check second image
        assert "image2.jpg" in manifest["images"]
        img2_data = manifest["images"]["image2.jpg"]
        assert img2_data["aspect_ratio"] == "1:1"
        assert len(img2_data["variants"]) == 1

    def test_generate_manifest_with_errors(self, temp_dir):
        """Test manifest generation with some failed results."""
        fs_utils = FileSystemUtils()

        results = [
            {
                "status": "success",
                "source": "good_image.jpg",
                "aspect_ratio": "16:9",
                "variants": [
                    {
                        "path": "landscape-16-9/good_image/good_image-1920x1080.webp",
                        "width": 1920,
                        "height": 1080,
                        "size": 150000,
                        "type": "standard",
                    }
                ],
            },
            {
                "status": "error",
                "source": "bad_image.jpg",
                "error": "Processing failed",
            },
            {
                "status": "skipped",
                "source": "skipped_image.jpg",
                "reason": "unsupported_aspect_ratio",
            },
        ]

        fs_utils.generate_manifest(results, temp_dir)

        manifest_path = temp_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should only include successful results
        assert len(manifest["images"]) == 1
        assert "good_image.jpg" in manifest["images"]
        assert "bad_image.jpg" not in manifest["images"]
        assert "skipped_image.jpg" not in manifest["images"]

    def test_generate_manifest_empty_results(self, temp_dir):
        """Test manifest generation with no successful results."""
        fs_utils = FileSystemUtils()

        results = [
            {"status": "error", "source": "failed.jpg", "error": "Failed"},
            {"status": "skipped", "source": "skipped.jpg", "reason": "Too small"},
        ]

        fs_utils.generate_manifest(results, temp_dir)

        manifest_path = temp_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["version"] == "1.0"
        assert len(manifest["images"]) == 0

    def test_generate_manifest_duplicate_sources(self, temp_dir):
        """Test manifest generation with duplicate source names."""
        fs_utils = FileSystemUtils()

        results = [
            {
                "status": "success",
                "source": "image.jpg",
                "aspect_ratio": "16:9",
                "variants": [
                    {
                        "path": "variant1.webp",
                        "width": 1920,
                        "height": 1080,
                        "size": 150000,
                        "type": "standard",
                    }
                ],
            },
            {
                "status": "success",
                "source": "image.jpg",  # Same source name
                "aspect_ratio": "16:9",
                "variants": [
                    {
                        "path": "variant2.webp",
                        "width": 1024,
                        "height": 576,
                        "size": 75000,
                        "type": "standard",
                    }
                ],
            },
        ]

        fs_utils.generate_manifest(results, temp_dir)

        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should combine variants for same source
        assert len(manifest["images"]) == 1
        assert "image.jpg" in manifest["images"]
        assert len(manifest["images"]["image.jpg"]["variants"]) == 2

    def test_generate_manifest_json_serialization(self, temp_dir):
        """Test that manifest is properly JSON serializable."""
        fs_utils = FileSystemUtils()

        # Include various data types that might be problematic
        results = [
            {
                "status": "success",
                "source": "test.jpg",
                "aspect_ratio": "1:1",
                "variants": [
                    {
                        "path": "test.webp",
                        "width": 1600,
                        "height": 1600,
                        "size": 245678,
                        "type": "standard",
                    }
                ],
            }
        ]

        fs_utils.generate_manifest(results, temp_dir)

        # Should not raise any JSON serialization errors
        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path) as f:
            # This will raise an exception if JSON is invalid
            manifest = json.load(f)

        # Verify structure is correct
        assert isinstance(manifest, dict)
        assert isinstance(manifest["images"], dict)


class TestHelperFunctions:
    """Test helper utility functions."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (30, "30s"),
            (45.7, "46s"),
            (60, "1m 0s"),
            (90, "1m 30s"),
            (3600, "1h 0m"),
            (3665, "1h 1m"),
            (7325, "2h 2m"),
            (0, "0s"),
            (0.5, "1s"),
        ],
    )
    def test_format_time(self, seconds, expected):
        """Test time formatting function."""
        result = format_time(seconds)
        assert result == expected

    def test_format_time_edge_cases(self):
        """Test time formatting with edge cases."""
        # Very large time
        large_time = (
            86400 * 2 + 3600 * 5 + 60 * 30 + 45
        )  # 2 days, 5 hours, 30 minutes, 45 seconds
        result = format_time(large_time)
        assert "53h 30m" in result  # Should show as hours

        # Very small time
        small_time = 0.1
        result = format_time(small_time)
        assert result == "0s"

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("simple", "simple"),
            ("Simple File", "simple-file"),
            ("UPPER_CASE_FILE", "upper-case-file"),
            ("mixed_Case File", "mixed-case-file"),
            ("file__with___underscores", "file-with-underscores"),
            ("file  with   spaces", "file-with-spaces"),
            ("file_with-mixed- _separators", "file-with-mixed-separators"),
            ("_starts_with_underscore", "starts-with-underscore"),
            ("ends_with_underscore_", "ends-with-underscore"),
            ("-starts-with-hyphen", "starts-with-hyphen"),
            ("ends-with-hyphen-", "ends-with-hyphen"),
            ("", ""),
            ("___", ""),
            ("   ", ""),
        ],
    )
    def test_sanitize_filename(self, filename, expected):
        """Test filename sanitization."""
        result = sanitize_filename(filename)
        assert result == expected

    def test_sanitize_filename_special_characters(self):
        """Test filename sanitization with various special characters."""
        # Should only handle spaces and underscores, not other special chars
        result = sanitize_filename("file@#$%name")
        assert result == "file@#$%name"  # Should preserve other special chars

        result = sanitize_filename("file name_with spaces")
        assert result == "file-name-with-spaces"

    def test_parse_override_params_empty(self):
        """Test parsing empty override parameters."""
        result = parse_override_params([])
        assert result == {"accept_all": True}

    def test_parse_override_params_aspect_ratio(self):
        """Test parsing aspect ratio overrides."""
        result = parse_override_params(["aspect-ratio=16:9"])
        assert result == {"aspect_ratio": (16, 9)}

        result = parse_override_params(["aspect-ratio=1:1"])
        assert result == {"aspect_ratio": (1, 1)}

        result = parse_override_params(["aspect-ratio=21:9"])
        assert result == {"aspect_ratio": (21, 9)}

    def test_parse_override_params_resolution(self):
        """Test parsing resolution overrides."""
        result = parse_override_params(["resolution=1920x1080"])
        assert result == {"resolution": (1920, 1080)}

        result = parse_override_params(["resolution=3840x2160"])
        assert result == {"resolution": (3840, 2160)}

    def test_parse_override_params_combined(self):
        """Test parsing combined override parameters."""
        result = parse_override_params(["aspect-ratio=16:9", "resolution=1920x1080"])
        expected = {"aspect_ratio": (16, 9), "resolution": (1920, 1080)}
        assert result == expected

    def test_parse_override_params_invalid_aspect_ratio(self):
        """Test parsing invalid aspect ratio formats."""
        with pytest.raises(ValueError, match="Invalid aspect ratio format"):
            parse_override_params(["aspect-ratio=16x9"])  # Wrong separator

        with pytest.raises(ValueError, match="Invalid aspect ratio format"):
            parse_override_params(["aspect-ratio=16"])  # Missing height

        with pytest.raises(ValueError, match="Invalid aspect ratio format"):
            parse_override_params(["aspect-ratio=abc:def"])  # Non-numeric

    def test_parse_override_params_invalid_resolution(self):
        """Test parsing invalid resolution formats."""
        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_override_params(["resolution=1920:1080"])  # Wrong separator

        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_override_params(["resolution=1920"])  # Missing height

        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_override_params(["resolution=abcxdef"])  # Non-numeric

    def test_parse_override_params_unknown_parameter(self):
        """Test parsing unknown override parameters."""
        with pytest.raises(ValueError, match="Unknown override parameter"):
            parse_override_params(["unknown-param=value"])

    def test_parse_override_params_invalid_format(self):
        """Test parsing parameters without equals sign."""
        with pytest.raises(
            ValueError, match="Override parameter must be in format key=value"
        ):
            parse_override_params(["aspect-ratio"])  # Missing value

        with pytest.raises(
            ValueError, match="Override parameter must be in format key=value"
        ):
            parse_override_params(["just-text"])  # No equals

    def test_parse_override_params_edge_cases(self):
        """Test parsing edge cases."""
        # Empty string values
        with pytest.raises(ValueError):
            parse_override_params(["aspect-ratio="])

        # Multiple equals signs (should split on first only and handle gracefully)
        result = parse_override_params(["resolution=1920x1080=extra"])
        # Our implementation handles multiple equals by taking only the first part
        assert result == {"resolution": (1920, 1080)}

    def test_parse_override_params_whitespace_handling(self):
        """Test that parameters handle whitespace correctly."""
        # The current implementation doesn't strip whitespace, so this would fail
        # This test documents current behavior
        with pytest.raises(ValueError):
            parse_override_params([" aspect-ratio=16:9 "])  # Leading/trailing spaces

    @pytest.mark.parametrize(
        "valid_input,expected_output",
        [
            (["aspect-ratio=16:9"], {"aspect_ratio": (16, 9)}),
            (["resolution=1920x1080"], {"resolution": (1920, 1080)}),
            (
                ["aspect-ratio=1:1", "resolution=1600x1600"],
                {"aspect_ratio": (1, 1), "resolution": (1600, 1600)},
            ),
            ([], {"accept_all": True}),
        ],
    )
    def test_parse_override_params_valid_combinations(
        self, valid_input, expected_output
    ):
        """Test various valid parameter combinations."""
        result = parse_override_params(valid_input)
        assert result == expected_output
