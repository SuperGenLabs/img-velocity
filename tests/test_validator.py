"""Comprehensive tests for ImageValidator class."""

import pytest
from PIL import Image

from img_velocity.core.config import Configuration
from img_velocity.core.validator import ImageValidator


class TestImageValidator:
    """Test ImageValidator class functionality."""

    def test_validator_initialization(self, config):
        """Test validator initializes with config."""
        validator = ImageValidator(config)
        assert validator.config is config
        assert isinstance(validator.config, Configuration)

    def test_get_image_info_valid_jpeg(self, validator, sample_images):
        """Test getting info from valid JPEG image."""
        jpeg_path = sample_images["square_large"]
        info = validator.get_image_info(jpeg_path)

        assert info is not None
        assert info["path"] == jpeg_path
        assert info["width"] == 1600
        assert info["height"] == 1600
        assert info["aspect_ratio"] == (1, 1)
        assert info["format"] == "JPEG"

    def test_get_image_info_valid_png(self, validator, sample_images):
        """Test getting info from valid PNG image."""
        png_path = sample_images["portrait_9_16"]
        info = validator.get_image_info(png_path)

        assert info is not None
        assert info["path"] == png_path
        assert info["width"] == 810
        assert info["height"] == 1440
        assert info["aspect_ratio"] == (9, 16)
        assert info["format"] == "PNG"

    def test_get_image_info_valid_webp(self, validator, sample_images):
        """Test getting info from valid WebP image."""
        webp_path = sample_images["wide_banner"]
        info = validator.get_image_info(webp_path)

        assert info is not None
        assert info["path"] == webp_path
        assert info["width"] == 3840
        assert info["height"] == 768
        assert info["aspect_ratio"] == (5, 1)
        assert info["format"] == "WEBP"

    def test_get_image_info_png_with_alpha(self, validator, sample_images):
        """Test PNG with alpha channel."""
        png_alpha_path = sample_images["png_with_alpha"]
        info = validator.get_image_info(png_alpha_path)

        assert info is not None
        assert info["format"] == "PNG"
        assert info["width"] == 1600
        assert info["height"] == 1600

    def test_get_image_info_nonexistent_file(self, validator, temp_dir):
        """Test with nonexistent file."""
        fake_path = temp_dir / "doesnt_exist.jpg"
        info = validator.get_image_info(fake_path)
        assert info is None

    def test_get_image_info_unsupported_format(self, validator, input_dir):
        """Test with unsupported image format."""
        # Create a BMP file (not supported)
        bmp_path = input_dir / "test.bmp"
        img = Image.new("RGB", (100, 100), "red")
        img.save(bmp_path, "BMP")

        info = validator.get_image_info(bmp_path)
        assert info is None

    def test_get_image_info_corrupted_file(self, validator, input_dir):
        """Test with corrupted image file."""
        corrupt_path = input_dir / "corrupt.jpg"
        corrupt_path.write_bytes(b"Not a real image file")

        info = validator.get_image_info(corrupt_path)
        assert info is None

    def test_get_image_info_text_file(self, validator, input_dir):
        """Test with text file having image extension."""
        text_path = input_dir / "fake.jpg"
        text_path.write_text("This is just text")

        info = validator.get_image_info(text_path)
        assert info is None

    @pytest.mark.parametrize(
        "width,height,expected_ratio",
        [
            (1920, 1080, (16, 9)),
            (1080, 1920, (9, 16)),
            (1600, 1600, (1, 1)),
            (2048, 1536, (4, 3)),
            (1536, 2048, (3, 4)),
            (3840, 768, (5, 1)),
            (7680, 960, (8, 1)),  # 8:1 scaled up
        ],
    )
    def test_get_image_info_aspect_ratio_calculation(
        self, validator, input_dir, width, height, expected_ratio
    ):
        """Test aspect ratio calculation for various dimensions."""
        img_path = input_dir / f"test_{width}x{height}.jpg"
        img = Image.new("RGB", (width, height), "blue")
        img.save(img_path, "JPEG")

        info = validator.get_image_info(img_path)
        assert info is not None
        assert info["aspect_ratio"] == expected_ratio

    def test_meets_requirements_valid_images(self, validator, sample_images):
        """Test requirements checking for valid images."""
        # Images that should meet requirements
        valid_images = [
            "square_large",
            "landscape_16_9",
            "portrait_9_16",
            "wide_banner",
        ]

        for img_key in valid_images:
            img_path = sample_images[img_key]
            info = validator.get_image_info(img_path)
            assert info is not None
            assert validator.meets_requirements(info), (
                f"{img_key} should meet requirements"
            )

    def test_meets_requirements_small_images(self, validator, sample_images):
        """Test requirements checking for images that are too small."""
        # Images that should NOT meet requirements (too small)
        small_images = ["square_small", "landscape_small"]

        for img_key in small_images:
            img_path = sample_images[img_key]
            info = validator.get_image_info(img_path)
            assert info is not None
            assert not validator.meets_requirements(info), (
                f"{img_key} should NOT meet requirements"
            )

    def test_meets_requirements_unsupported_aspect_ratio(
        self, validator, sample_images
    ):
        """Test requirements for unsupported aspect ratios."""
        # unusual_aspect is 3:2 but too small, very_wide is 10:1 (unsupported)
        unusual_path = sample_images["unusual_aspect"]
        info = validator.get_image_info(unusual_path)
        assert info is not None
        # Should fail because it's too small for 3:2
        assert not validator.meets_requirements(info)

        wide_path = sample_images["very_wide"]
        info = validator.get_image_info(wide_path)
        assert info is not None
        # Should fail because 10:1 is not supported
        assert not validator.meets_requirements(info)

    @pytest.mark.parametrize(
        "aspect_ratio,min_size,test_size,should_pass",
        [
            ((1, 1), (1600, 1600), (1600, 1600), True),  # Exact minimum
            ((1, 1), (1600, 1600), (1599, 1599), False),  # Just under
            ((1, 1), (1600, 1600), (2000, 2000), True),  # Well over
            ((16, 9), (3840, 2160), (3840, 2160), True),  # Exact minimum
            (
                (3839, 2159),
                (3840, 2160),
                (3839, 2159),
                False,
            ),  # Just under - use actual aspect ratio
            ((16, 9), (3840, 2160), (4096, 2304), True),  # Over minimum
        ],
    )
    def test_meets_requirements_boundary_conditions(
        self, validator, input_dir, aspect_ratio, min_size, test_size, should_pass
    ):
        """Test boundary conditions for size requirements."""
        width, height = test_size
        img_path = input_dir / f"boundary_{width}x{height}.jpg"
        img = Image.new("RGB", (width, height), "green")
        img.save(img_path, "JPEG")

        info = validator.get_image_info(img_path)
        assert info is not None
        assert info["aspect_ratio"] == aspect_ratio

        result = validator.meets_requirements(info)
        assert result == should_pass

    def test_meets_requirements_with_override_no_overrides(
        self, validator, sample_images
    ):
        """Test override function with no overrides."""
        img_path = sample_images["square_large"]
        info = validator.get_image_info(img_path)

        # Should behave same as regular meets_requirements
        regular_result = validator.meets_requirements(info)
        override_result = validator.meets_requirements_with_override(info, None)

        assert regular_result == override_result

    def test_meets_requirements_with_override_accept_all(
        self, validator, sample_images
    ):
        """Test override with accept_all flag."""
        overrides = {"accept_all": True}

        # Even small images should pass with accept_all
        for img_key, img_path in sample_images.items():
            info = validator.get_image_info(img_path)
            if info is not None:  # Skip corrupted files
                result = validator.meets_requirements_with_override(info, overrides)
                assert result, f"{img_key} should pass with accept_all override"

    def test_meets_requirements_with_override_aspect_ratio(
        self, validator, sample_images
    ):
        """Test override with specific aspect ratio."""
        overrides = {"aspect_ratio": (16, 9)}

        # Only 16:9 images should pass
        landscape_16_9_info = validator.get_image_info(sample_images["landscape_16_9"])
        assert validator.meets_requirements_with_override(
            landscape_16_9_info, overrides
        )

        # Non-16:9 images should fail
        square_info = validator.get_image_info(sample_images["square_large"])
        assert not validator.meets_requirements_with_override(square_info, overrides)

    def test_meets_requirements_with_override_resolution(self, validator, input_dir):
        """Test override with custom resolution requirement."""
        overrides = {"resolution": (1920, 1080)}

        # Create images with different sizes
        large_img = input_dir / "large.jpg"
        Image.new("RGB", (2560, 1440), "red").save(large_img, "JPEG")

        small_img = input_dir / "small.jpg"
        Image.new("RGB", (1280, 720), "blue").save(small_img, "JPEG")

        exact_img = input_dir / "exact.jpg"
        Image.new("RGB", (1920, 1080), "green").save(exact_img, "JPEG")

        # Test results
        large_info = validator.get_image_info(large_img)
        assert validator.meets_requirements_with_override(large_info, overrides)

        small_info = validator.get_image_info(small_img)
        assert not validator.meets_requirements_with_override(small_info, overrides)

        exact_info = validator.get_image_info(exact_img)
        assert validator.meets_requirements_with_override(exact_info, overrides)

    def test_meets_requirements_with_override_combined(self, validator, input_dir):
        """Test override with both aspect ratio and resolution."""
        overrides = {"aspect_ratio": (16, 9), "resolution": (1920, 1080)}

        # Create 16:9 image that meets resolution requirement
        valid_img = input_dir / "valid_combined.jpg"
        Image.new("RGB", (3840, 2160), "purple").save(valid_img, "JPEG")

        # Create 16:9 image that's too small
        small_16_9 = input_dir / "small_16_9.jpg"
        Image.new("RGB", (1280, 720), "orange").save(small_16_9, "JPEG")

        # Create large image with wrong aspect ratio
        wrong_aspect = input_dir / "wrong_aspect.jpg"
        Image.new("RGB", (2000, 2000), "yellow").save(wrong_aspect, "JPEG")

        # Test results
        valid_info = validator.get_image_info(valid_img)
        assert validator.meets_requirements_with_override(valid_info, overrides)

        small_info = validator.get_image_info(small_16_9)
        assert not validator.meets_requirements_with_override(small_info, overrides)

        wrong_info = validator.get_image_info(wrong_aspect)
        assert not validator.meets_requirements_with_override(wrong_info, overrides)

    def test_meets_requirements_with_override_aspect_ratio_only(
        self, validator, input_dir
    ):
        """Test override with only aspect ratio (should use default requirements for that ratio)."""
        overrides = {"aspect_ratio": (1, 1)}

        # Create square images of different sizes
        large_square = input_dir / "large_square.jpg"
        Image.new("RGB", (1600, 1600), "cyan").save(
            large_square, "JPEG"
        )  # Meets 1:1 requirements

        small_square = input_dir / "small_square.jpg"
        Image.new("RGB", (800, 800), "magenta").save(small_square, "JPEG")  # Too small

        # Test results
        large_info = validator.get_image_info(large_square)
        assert validator.meets_requirements_with_override(large_info, overrides)

        small_info = validator.get_image_info(small_square)
        assert not validator.meets_requirements_with_override(small_info, overrides)

    def test_meets_requirements_edge_cases(self, validator, input_dir):
        """Test edge cases for requirements checking."""
        # Very small image (1x1)
        tiny_img = input_dir / "tiny.jpg"
        Image.new("RGB", (1, 1), "white").save(tiny_img, "JPEG")

        # Very large image
        huge_img = input_dir / "huge.jpg"
        Image.new("RGB", (8000, 8000), "black").save(huge_img, "JPEG")

        # Prime number dimensions
        prime_img = input_dir / "prime.jpg"
        Image.new("RGB", (1009, 1009), "gray").save(prime_img, "JPEG")

        tiny_info = validator.get_image_info(tiny_img)
        assert not validator.meets_requirements(tiny_info)

        huge_info = validator.get_image_info(huge_img)
        assert validator.meets_requirements(huge_info)  # Should meet 1:1 requirements

        prime_info = validator.get_image_info(prime_img)
        assert not validator.meets_requirements(prime_info)  # Too small for 1:1

    def test_validator_with_different_configs(self, input_dir):
        """Test validator behavior with modified config."""
        # Create custom config with different requirements
        custom_config = Configuration()
        # Temporarily modify requirements for testing
        original_reqs = custom_config.MIN_REQUIREMENTS.copy()
        custom_config.MIN_REQUIREMENTS[(1, 1)] = (800, 800)  # Lower requirement

        validator = ImageValidator(custom_config)

        # Create 800x800 image
        img_path = input_dir / "custom_test.jpg"
        Image.new("RGB", (800, 800), "lime").save(img_path, "JPEG")

        info = validator.get_image_info(img_path)
        assert validator.meets_requirements(info)  # Should pass with custom config

        # Restore original config
        custom_config.MIN_REQUIREMENTS = original_reqs

    def test_get_image_info_file_permissions(self, validator, input_dir):
        """Test handling of files with restricted permissions."""
        img_path = input_dir / "restricted.jpg"
        Image.new("RGB", (100, 100), "silver").save(img_path, "JPEG")

        # Test normal access first
        info = validator.get_image_info(img_path)
        assert info is not None

        # Note: Permission testing is platform-specific and may not work in all environments
        # This test primarily documents expected behavior

    def test_get_image_info_various_jpeg_qualities(self, validator, input_dir):
        """Test JPEG images with different quality settings."""
        qualities = [10, 50, 95]

        for quality in qualities:
            img_path = input_dir / f"quality_{quality}.jpg"
            img = Image.new("RGB", (1000, 1000), f"#{quality:02x}0000")
            img.save(img_path, "JPEG", quality=quality)

            info = validator.get_image_info(img_path)
            assert info is not None
            assert info["format"] == "JPEG"
            assert info["width"] == 1000
            assert info["height"] == 1000
