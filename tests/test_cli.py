"""Comprehensive tests for CLI components."""

import sys
from unittest.mock import patch

import pytest

from img_velocity.cli.parser import CLIParser


class TestCLIParser:
    """Test CLIParser class functionality."""

    def test_cli_parser_initialization(self):
        """Test CLIParser initializes correctly."""
        parser = CLIParser()
        assert parser.parser is not None
        assert hasattr(parser, "original_argv")  # May not exist until filter is called

    def test_create_parser_structure(self):
        """Test parser has expected arguments."""
        parser = CLIParser()

        # Get all argument names
        actions = parser.parser._actions
        arg_names = []
        for action in actions:
            if hasattr(action, "dest") and action.dest != "help":
                arg_names.append(action.dest)

        # Check required arguments exist
        expected_args = [
            "input_dir",
            "output_dir",
            "thumbnails",
            "workers",
            "benchmark",
            "override",
        ]
        for arg in expected_args:
            assert arg in arg_names, f"Missing argument: {arg}"

    def test_parse_args_basic(self):
        """Test basic argument parsing."""
        parser = CLIParser()

        test_args = ["input/", "output/"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.input_dir == "input/"
            assert args.output_dir == "output/"
            assert args.thumbnails is False
            assert args.workers is None
            assert args.benchmark is False
            assert args.override is None
            assert args.overrides is None

    def test_parse_args_with_thumbnails(self):
        """Test parsing with thumbnails flag."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--thumbnails"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.thumbnails is True

    def test_parse_args_with_workers(self):
        """Test parsing with workers argument."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", "8"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.workers == 8

    def test_parse_args_with_benchmark(self):
        """Test parsing with benchmark flag."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--benchmark"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.benchmark is True

    def test_parse_args_override_accept_all(self):
        """Test parsing override with no parameters (accept all)."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--override"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.override == []
            assert args.overrides == {"accept_all": True}

    def test_parse_args_override_aspect_ratio(self):
        """Test parsing override with aspect ratio."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--override", "aspect-ratio=16:9"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.override == ["aspect-ratio=16:9"]
            assert args.overrides["aspect_ratio"] == (16, 9)

    def test_parse_args_override_resolution(self):
        """Test parsing override with resolution."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--override", "resolution=1920x1080"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.override == ["resolution=1920x1080"]
            assert args.overrides["resolution"] == (1920, 1080)

    def test_parse_args_override_combined(self):
        """Test parsing override with multiple parameters."""
        parser = CLIParser()

        test_args = [
            "input/",
            "output/",
            "--override",
            "aspect-ratio=16:9",
            "resolution=1920x1080",
        ]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert len(args.override) == 2
            assert args.overrides["aspect_ratio"] == (16, 9)
            assert args.overrides["resolution"] == (1920, 1080)

    def test_parse_args_all_options(self):
        """Test parsing with all options specified."""
        parser = CLIParser()

        test_args = [
            "input_dir/",
            "output_dir/",
            "--thumbnails",
            "--workers",
            "4",
            "--benchmark",
            "--override",
            "aspect-ratio=16:9",
        ]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.input_dir == "input_dir/"
            assert args.output_dir == "output_dir/"
            assert args.thumbnails is True
            assert args.workers == 4
            assert args.benchmark is True
            assert args.overrides["aspect_ratio"] == (16, 9)

    def test_parse_args_invalid_override_format(self):
        """Test parsing with invalid override format."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--override", "invalid-format"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args), patch(
            "sys.exit"
        ) as mock_exit:
            parser.parse_args()
            mock_exit.assert_called_once_with(1)

    def test_parse_args_invalid_aspect_ratio(self):
        """Test parsing with invalid aspect ratio format."""
        parser = CLIParser()

        test_args = [
            "input/",
            "output/",
            "--override",
            "aspect-ratio=16x9",
        ]  # Wrong separator

        with patch.object(sys, "argv", ["img-velocity"] + test_args), patch(
            "sys.exit"
        ) as mock_exit:
            parser.parse_args()
            mock_exit.assert_called_once_with(1)

    def test_parse_args_invalid_resolution(self):
        """Test parsing with invalid resolution format."""
        parser = CLIParser()

        test_args = [
            "input/",
            "output/",
            "--override",
            "resolution=1920:1080",
        ]  # Wrong separator

        with patch.object(sys, "argv", ["img-velocity"] + test_args), patch(
            "sys.exit"
        ) as mock_exit:
            parser.parse_args()
            mock_exit.assert_called_once_with(1)

    def test_parse_args_missing_required_args(self):
        """Test parsing without required arguments."""
        parser = CLIParser()

        test_args = ["input/"]  # Missing output directory

        with patch.object(sys, "argv", ["img-velocity"] + test_args), pytest.raises(
            SystemExit
        ):
            parser.parse_args()

    def test_parse_args_help(self):
        """Test help argument parsing."""
        parser = CLIParser()

        test_args = ["--help"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args()

            # Help should exit with code 0
            assert exc_info.value.code == 0

    def test_filter_multiprocessing_args_basic(self):
        """Test filtering of multiprocessing arguments."""
        parser = CLIParser()

        # Simulate sys.argv with multiprocessing args
        original_argv = [
            "input/",
            "output/",
            "--multiprocessing-fork=123",
            "--workers",
            "4",
        ]

        with patch.object(sys, "argv", ["img-velocity"] + original_argv):
            parser.filter_multiprocessing_args()

            # Should have filtered out multiprocessing args
            assert "--multiprocessing-fork=123" not in sys.argv
            assert "--workers" in sys.argv
            assert "4" in sys.argv

    def test_filter_multiprocessing_args_separate_value(self):
        """Test filtering multiprocessing args with separate values."""
        parser = CLIParser()

        # Multiprocessing arg with separate value
        original_argv = [
            "input/",
            "output/",
            "--multiprocessing-fork",
            "123",
            "--thumbnails",
        ]

        with patch.object(sys, "argv", ["img-velocity"] + original_argv):
            parser.filter_multiprocessing_args()

            # Should filter both the flag and its value
            assert "--multiprocessing-fork" not in sys.argv
            assert "123" not in sys.argv
            assert "--thumbnails" in sys.argv

    def test_filter_multiprocessing_args_no_multiprocessing(self):
        """Test filtering when no multiprocessing args present."""
        parser = CLIParser()

        original_argv = ["input/", "output/", "--workers", "2"]

        with patch.object(sys, "argv", ["img-velocity"] + original_argv):
            original_filtered = sys.argv[1:]
            parser.filter_multiprocessing_args()

            # Should be unchanged
            assert sys.argv[1:] == original_filtered

    def test_restore_argv(self):
        """Test restoration of original argv."""
        parser = CLIParser()

        original = ["input/", "output/", "--multiprocessing-fork=123"]

        with patch.object(sys, "argv", ["img-velocity"] + original):
            # Filter args
            parser.filter_multiprocessing_args()

            # Should be different now
            assert sys.argv[1:] != original

            # Restore
            parser.restore_argv()

            # Should be back to original
            assert sys.argv[1:] == original

    def test_restore_argv_without_filter(self):
        """Test restore_argv when filter wasn't called."""
        parser = CLIParser()

        original = ["input/", "output/"]

        with patch.object(sys, "argv", ["img-velocity"] + original):
            # Call restore without filter (should not crash)
            parser.restore_argv()

            # Should be unchanged
            assert sys.argv[1:] == original

    def test_parser_help_content(self):
        """Test that parser help contains expected information."""
        parser = CLIParser()

        help_text = parser.parser.format_help()

        # Check for key sections
        assert "Supported input formats" in help_text
        assert "JPEG, PNG, WebP" in help_text
        assert "Minimum size requirements" in help_text
        assert "Override options" in help_text
        assert "Features:" in help_text

        # Check for specific aspect ratios
        assert "16:9" in help_text
        assert "1:1" in help_text
        assert "Square (1:1): 1600×1600" in help_text

        # Check for override examples
        assert '--override aspect-ratio="16:9"' in help_text
        assert '--override resolution="1920x1080"' in help_text

    def test_parser_epilog_content(self):
        """Test parser epilog contains comprehensive information."""
        parser = CLIParser()

        epilog = parser.parser.epilog

        # Should contain all supported aspect ratios with requirements
        expected_ratios = [
            "Square (1:1): 1600×1600",
            "Landscape 16:9: 3840×2160",
            "Portrait 9:16: 810×1440",
            "Wide banner 5:1: 3840×768",
            "Slim banner 8:1: 3840×480",
        ]

        for ratio_info in expected_ratios:
            assert ratio_info in epilog

    @pytest.mark.parametrize("worker_count", [1, 2, 4, 8, 16])
    def test_parse_args_worker_count_validation(self, worker_count):
        """Test parsing various worker counts."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", str(worker_count)]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.workers == worker_count

    def test_parse_args_invalid_worker_count(self):
        """Test parsing with invalid worker count."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", "invalid"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args), pytest.raises(
            SystemExit
        ):
            parser.parse_args()

    def test_parse_args_negative_worker_count(self):
        """Test parsing with negative worker count."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", "-1"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            # Should parse but be invalid (handled elsewhere)
            assert args.workers == -1

    def test_parse_args_zero_worker_count(self):
        """Test parsing with zero worker count."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", "0"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.workers == 0

    def test_parser_argument_types(self):
        """Test that arguments have correct types."""
        parser = CLIParser()

        test_args = ["input/", "output/", "--workers", "4"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            # Check types
            assert isinstance(args.input_dir, str)
            assert isinstance(args.output_dir, str)
            assert isinstance(args.thumbnails, bool)
            assert isinstance(args.workers, int)
            assert isinstance(args.benchmark, bool)

    def test_override_parameter_edge_cases(self):
        """Test edge cases in override parameter parsing."""
        parser = CLIParser()

        # Test with custom aspect ratio (not in defaults)
        test_args = ["input/", "output/", "--override", "aspect-ratio=21:9"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.overrides["aspect_ratio"] == (21, 9)

        # Test with very high resolution
        test_args = ["input/", "output/", "--override", "resolution=7680x4320"]

        with patch.object(sys, "argv", ["img-velocity"] + test_args):
            args = parser.parse_args()

            assert args.overrides["resolution"] == (7680, 4320)

    def test_multiple_override_scenarios(self):
        """Test various combinations of override parameters."""
        parser = CLIParser()

        test_scenarios = [
            (["--override"], {"accept_all": True}),
            (["--override", "aspect-ratio=1:1"], {"aspect_ratio": (1, 1)}),
            (["--override", "resolution=4096x4096"], {"resolution": (4096, 4096)}),
            (
                ["--override", "aspect-ratio=3:2", "resolution=3456x2304"],
                {"aspect_ratio": (3, 2), "resolution": (3456, 2304)},
            ),
        ]

        for override_args, expected_overrides in test_scenarios:
            test_args = ["input/", "output/"] + override_args

            with patch.object(sys, "argv", ["img-velocity"] + test_args):
                args = parser.parse_args()

                for key, value in expected_overrides.items():
                    assert args.overrides[key] == value

    def test_argument_order_independence(self):
        """Test that argument order doesn't matter."""
        parser = CLIParser()

        # Different orders of the same arguments
        orders = [
            ["input/", "output/", "--thumbnails", "--workers", "4", "--benchmark"],
            ["--thumbnails", "input/", "--workers", "4", "output/", "--benchmark"],
            ["--benchmark", "--workers", "4", "--thumbnails", "input/", "output/"],
        ]

        for test_args in orders:
            with patch.object(sys, "argv", ["img-velocity"] + test_args):
                args = parser.parse_args()

                assert args.input_dir == "input/"
                assert args.output_dir == "output/"
                assert args.thumbnails is True
                assert args.workers == 4
                assert args.benchmark is True

    def test_parse_args_context_manager_behavior(self):
        """Test that argv filtering and restoration work as context."""
        parser = CLIParser()

        original_argv = [
            "input/",
            "output/",
            "--multiprocessing-fork=123",
            "--workers",
            "2",
        ]

        with patch.object(sys, "argv", ["img-velocity"] + original_argv):
            # Before parsing
            assert "--multiprocessing-fork=123" in sys.argv

            # Parse args (should filter and restore)
            args = parser.parse_args()

            # After parsing, should be restored
            assert sys.argv[1:] == original_argv

            # But parsing should have worked
            assert args.workers == 2
            assert args.input_dir == "input/"
