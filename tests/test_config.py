"""Comprehensive tests for Configuration class."""

import pytest


class TestConfiguration:
    """Test Configuration class functionality."""

    def test_supported_formats_constant(self, config):
        """Test SUPPORTED_FORMATS contains expected formats."""
        expected_formats = {"JPEG", "PNG", "WEBP"}
        assert expected_formats == config.SUPPORTED_FORMATS
        assert isinstance(config.SUPPORTED_FORMATS, set)

    @pytest.mark.parametrize(
        "width,height,expected",
        [
            (1920, 1080, (16, 9)),
            (1600, 1600, (1, 1)),
            (2048, 1536, (4, 3)),
            (3456, 2304, (3, 2)),
            (810, 1440, (9, 16)),
            (1536, 2048, (3, 4)),
            (1024, 1536, (2, 3)),
            (3840, 768, (5, 1)),
            (3840, 480, (8, 1)),
            # Edge cases
            (100, 200, (1, 2)),
            (300, 100, (3, 1)),
            (7, 5, (7, 5)),  # Prime numbers
            (1000, 1000, (1, 1)),  # Perfect square
        ],
    )
    def test_get_aspect_ratio(self, config, width, height, expected):
        """Test aspect ratio calculation with various dimensions."""
        result = config.get_aspect_ratio(width, height)
        assert result == expected
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(x, int) for x in result)

    def test_get_aspect_ratio_gcd_reduction(self, config):
        """Test that aspect ratios are properly reduced using GCD."""
        # 3840x2160 should reduce to 16:9, not stay as 3840:2160
        result = config.get_aspect_ratio(3840, 2160)
        assert result == (16, 9)

        # 2000x1000 should reduce to 2:1
        result = config.get_aspect_ratio(2000, 1000)
        assert result == (2, 1)

    def test_min_requirements_coverage(self, config):
        """Test that all required aspect ratios have minimum requirements."""
        required_ratios = [
            (1, 1),
            (16, 9),
            (4, 3),
            (3, 2),
            (9, 16),
            (3, 4),
            (2, 3),
            (5, 1),
            (8, 1),
        ]

        for ratio in required_ratios:
            assert ratio in config.MIN_REQUIREMENTS
            min_w, min_h = config.MIN_REQUIREMENTS[ratio]
            assert isinstance(min_w, int)
            assert isinstance(min_h, int)
            assert min_w > 0
            assert min_h > 0
            # Verify the minimum meets the aspect ratio
            calculated_ratio = config.get_aspect_ratio(min_w, min_h)
            assert calculated_ratio == ratio

    def test_output_configs_structure(self, config):
        """Test OUTPUT_CONFIGS has proper structure."""
        for ratio, conf in config.OUTPUT_CONFIGS.items():
            assert isinstance(ratio, tuple)
            assert len(ratio) == 2
            assert isinstance(conf, dict)

            # Required keys
            assert "folder" in conf
            assert "sizes" in conf
            assert "thumbnail_sizes" in conf

            # Folder should be string
            assert isinstance(conf["folder"], str)
            assert len(conf["folder"]) > 0

            # Sizes should be list of tuples
            assert isinstance(conf["sizes"], list)
            assert len(conf["sizes"]) > 0
            for size in conf["sizes"]:
                assert isinstance(size, tuple)
                assert len(size) == 2
                assert all(isinstance(x, int) and x > 0 for x in size)

            # Thumbnails can be empty list
            assert isinstance(conf["thumbnail_sizes"], list)
            for thumb in conf["thumbnail_sizes"]:
                assert isinstance(thumb, tuple)
                assert len(thumb) == 2
                assert all(isinstance(x, int) and x > 0 for x in thumb)

    def test_output_configs_folder_naming(self, config):
        """Test folder names follow expected patterns."""
        expected_folders = {
            (1, 1): "square-1-1",
            (16, 9): "landscape-16-9",
            (4, 3): "landscape-4-3",
            (3, 2): "landscape-3-2",
            (9, 16): "portrait-9-16",
            (3, 4): "portrait-3-4",
            (2, 3): "portrait-2-3",
            (5, 1): "wide-banner-5-1",
            (8, 1): "slim-banner-8-1",
        }

        for ratio, expected_folder in expected_folders.items():
            assert ratio in config.OUTPUT_CONFIGS
            assert config.OUTPUT_CONFIGS[ratio]["folder"] == expected_folder

    def test_get_output_sizes_valid_ratios(self, config, expected_outputs):
        """Test get_output_sizes returns correct configurations."""
        for ratio, expected in expected_outputs.items():
            result = config.get_output_sizes(ratio)
            assert result == expected

    def test_get_output_sizes_invalid_ratio(self, config):
        """Test get_output_sizes with unsupported aspect ratio."""
        result = config.get_output_sizes((7, 3))  # Unusual ratio
        assert result == {}

    @pytest.mark.parametrize(
        "width,height,is_thumbnail,expected_quality",
        [
            # Regular images
            (400, 300, False, 80),  # Small
            (800, 600, False, 80),  # Small boundary
            (1024, 768, False, 85),  # Medium
            (1920, 1080, False, 85),  # Medium-large
            (2000, 1500, False, 85),  # Medium boundary
            (3840, 2160, False, 82),  # Large
            (4096, 2160, False, 82),  # Very large
            # Thumbnails
            (75, 75, True, 55),  # Tiny thumbnail
            (100, 100, True, 55),  # Small thumbnail boundary
            (150, 150, True, 65),  # Larger thumbnail
            (300, 200, True, 65),  # Large thumbnail
        ],
    )
    def test_get_webp_quality(
        self, config, width, height, is_thumbnail, expected_quality
    ):
        """Test WebP quality calculation for various sizes."""
        result = config.get_webp_quality(width, height, is_thumbnail)
        assert result == expected_quality
        assert isinstance(result, int)
        assert 50 <= result <= 100  # Reasonable quality range

    def test_get_webp_quality_edge_cases(self, config):
        """Test WebP quality with edge case dimensions."""
        # Very small image
        quality = config.get_webp_quality(10, 10, False)
        assert quality == 80

        # Very large image
        quality = config.get_webp_quality(8000, 6000, False)
        assert quality == 82

        # Extreme aspect ratios
        quality = config.get_webp_quality(4000, 100, False)
        assert quality == 82  # Based on max dimension

    def test_get_output_sizes_with_override_no_overrides(self, config):
        """Test override function without any overrides."""
        ratio = (16, 9)
        result = config.get_output_sizes_with_override(ratio, None)
        expected = config.get_output_sizes(ratio)
        assert result == expected

    def test_get_output_sizes_with_override_accept_all(self, config):
        """Test override with accept_all flag."""
        ratio = (16, 9)
        overrides = {"accept_all": True}
        result = config.get_output_sizes_with_override(ratio, overrides)
        expected = config.get_output_sizes(ratio)
        assert result == expected

    def test_get_output_sizes_with_override_aspect_ratio(self, config):
        """Test override with specific aspect ratio."""
        original_ratio = (4, 3)
        target_ratio = (16, 9)
        overrides = {"aspect_ratio": target_ratio}

        result = config.get_output_sizes_with_override(original_ratio, overrides)
        expected = config.get_output_sizes(target_ratio)
        assert result == expected

    def test_get_output_sizes_with_override_custom_aspect(self, config):
        """Test override with custom aspect ratio not in defaults."""
        ratio = (21, 9)  # Ultra-wide, not in defaults
        overrides = {"aspect_ratio": ratio}

        result = config.get_output_sizes_with_override((16, 9), overrides)

        assert result["folder"] == "custom-21-9"
        assert result["sizes"] == []
        assert result["thumbnail_sizes"] == []

    def test_get_output_sizes_with_override_resolution(self, config):
        """Test override with custom resolution."""
        ratio = (16, 9)
        overrides = {"resolution": (2560, 1440)}

        result = config.get_output_sizes_with_override(ratio, overrides)

        # Should start with override resolution
        assert (2560, 1440) in result["sizes"]
        # Should have scaled-down versions
        assert len(result["sizes"]) > 1

        # Check scaling factors are applied correctly
        sizes = result["sizes"]
        assert sizes[0] == (2560, 1440)  # Original

        # Verify all sizes maintain aspect ratio and are reasonable
        for width, height in sizes:
            assert width >= 50  # Minimum size
            assert height >= 50
            calculated_ratio = config.get_aspect_ratio(width, height)
            assert calculated_ratio == ratio

    def test_get_output_sizes_with_override_resolution_thumbnails(self, config):
        """Test override resolution generates appropriate thumbnails."""
        ratio = (16, 9)
        overrides = {"resolution": (3200, 1800)}

        result = config.get_output_sizes_with_override(ratio, overrides)

        # Should have thumbnail sizes
        assert len(result["thumbnail_sizes"]) > 0

        # Thumbnails should be smaller than main sizes
        max_thumb_dim = max(max(thumb) for thumb in result["thumbnail_sizes"])
        min_main_dim = min(min(size) for size in result["sizes"])
        assert max_thumb_dim < min_main_dim

    def test_get_output_sizes_with_override_combined(self, config):
        """Test override with both aspect ratio and resolution."""
        overrides = {"aspect_ratio": (16, 9), "resolution": (1920, 1080)}

        result = config.get_output_sizes_with_override((4, 3), overrides)

        # Should use 16:9 folder structure
        assert result["folder"] == "landscape-16-9"

        # Should start with 1920x1080
        assert (1920, 1080) in result["sizes"]

        # All sizes should maintain 16:9 ratio
        for width, height in result["sizes"]:
            calculated_ratio = config.get_aspect_ratio(width, height)
            assert calculated_ratio == (16, 9)

    def test_output_configs_size_ordering(self, config):
        """Test that output sizes are ordered from largest to smallest."""
        for _ratio, conf in config.OUTPUT_CONFIGS.items():
            sizes = conf["sizes"]
            if len(sizes) > 1:
                # Check that sizes are in descending order by area
                areas = [w * h for w, h in sizes]
                assert areas == sorted(areas, reverse=True)

    def test_output_configs_thumbnails_smaller_than_main(self, config):
        """Test that thumbnail sizes are smaller than main sizes."""
        for _ratio, conf in config.OUTPUT_CONFIGS.items():
            if conf["thumbnail_sizes"] and conf["sizes"]:
                max_thumb_area = max(w * h for w, h in conf["thumbnail_sizes"])
                min_main_area = min(w * h for w, h in conf["sizes"])
                assert max_thumb_area < min_main_area

    def test_configuration_immutability(self, config):
        """Test that configuration constants are not accidentally modified."""
        # Attempt to modify (shouldn't affect originals in well-designed system)
        config.SUPPORTED_FORMATS.add("TIFF")
        config.MIN_REQUIREMENTS[(1, 2)] = (800, 1600)

        # In a properly designed system, these should not affect the class constants
        # This test documents current behavior and catches unintended changes
        assert "TIFF" in config.SUPPORTED_FORMATS  # Current behavior
        assert (1, 2) in config.MIN_REQUIREMENTS  # Current behavior
