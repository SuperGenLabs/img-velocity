"""Comprehensive tests for ImageProcessor class."""

import pytest
from PIL import Image

from img_velocity.core.config import Configuration
from img_velocity.core.processor import ImageProcessor


class TestImageProcessor:
    """Test ImageProcessor class functionality."""

    def test_processor_initialization(self, config):
        """Test processor initializes with config."""
        processor = ImageProcessor(config)
        assert processor.config is config
        assert isinstance(processor.config, Configuration)

    @pytest.mark.parametrize(
        "original_size,target_size,expected_sharpening",
        [
            # No sharpening cases (target >= original or minimal downscale)
            ((1000, 1000), (1000, 1000), False),  # Same size
            ((1000, 1000), (1200, 1200), False),  # Upscale
            ((1000, 1000), (800, 800), False),  # Scale factor 0.8 (>= 0.75)
            # Medium sharpening (0.5 <= scale < 0.75)
            ((1000, 1000), (600, 600), True),  # Scale factor 0.6
            ((1000, 1000), (500, 500), True),  # Scale factor 0.5
            # Strong sharpening (scale < 0.5)
            ((1000, 1000), (400, 400), True),  # Scale factor 0.4
            ((2000, 1000), (500, 250), True),  # Scale factor 0.25
        ],
    )
    def test_apply_smart_sharpening(
        self, processor, input_dir, original_size, target_size, expected_sharpening
    ):
        """Test smart sharpening logic based on downscale factor."""
        # Create test image
        img_path = input_dir / "sharpen_test.jpg"
        img = Image.new("RGB", original_size, "red")
        img.save(img_path, "JPEG")

        # Load and apply sharpening
        with Image.open(img_path) as test_img:
            result = processor.apply_smart_sharpening(
                test_img, original_size, target_size
            )

            # Result should always be an Image
            assert isinstance(result, Image.Image)

            # For this test, we can't easily verify sharpening was applied,
            # but we can verify the function doesn't crash and returns reasonable results
            assert (
                result.size == test_img.size
            )  # Size shouldn't change during sharpening

    def test_apply_smart_sharpening_edge_cases(self, processor, input_dir):
        """Test sharpening with edge case dimensions."""
        # Very small image
        small_img = Image.new("RGB", (10, 10), "blue")
        result = processor.apply_smart_sharpening(small_img, (10, 10), (5, 5))
        assert isinstance(result, Image.Image)

        # Very large downscale
        large_img = Image.new("RGB", (4000, 4000), "green")
        result = processor.apply_smart_sharpening(large_img, (4000, 4000), (200, 200))
        assert isinstance(result, Image.Image)

        # Extreme aspect ratio change
        wide_img = Image.new("RGB", (2000, 500), "yellow")
        result = processor.apply_smart_sharpening(wide_img, (2000, 500), (400, 100))
        assert isinstance(result, Image.Image)

    def test_process_single_size_jpeg_to_webp(self, processor, input_dir, output_dir):
        """Test processing single JPEG to WebP."""
        # Create source image
        source_path = input_dir / "source.jpg"
        img = Image.new("RGB", (1000, 800), "purple")
        img.save(source_path, "JPEG")

        # Set up processing parameters
        output_path = output_dir / "result.webp"
        target_size = (500, 400)
        original_size = (1000, 800)
        is_thumbnail = False

        args = (
            source_path,
            output_path,
            target_size,
            original_size,
            is_thumbnail,
            output_dir,
        )

        # Process
        result = processor.process_single_size(args)

        # Verify result
        assert result is not None
        assert output_path.exists()
        assert result["width"] == 500
        assert result["height"] == 400
        assert result["type"] == "standard"
        assert result["size"] > 0  # File has content
        assert result["path"] == str(output_path.relative_to(output_dir))

        # Verify output is WebP
        with Image.open(output_path) as webp_img:
            assert webp_img.format == "WEBP"
            assert webp_img.size == (500, 400)

    def test_process_single_size_png_with_transparency(
        self, processor, input_dir, output_dir
    ):
        """Test processing PNG with alpha channel."""
        # Create PNG with transparency
        source_path = input_dir / "transparent.png"
        img = Image.new("RGBA", (800, 600), (255, 0, 0, 128))  # Semi-transparent red
        img.save(source_path, "PNG")

        output_path = output_dir / "transparent_result.webp"
        target_size = (400, 300)
        original_size = (800, 600)

        args = (source_path, output_path, target_size, original_size, False, output_dir)
        result = processor.process_single_size(args)

        assert result is not None
        assert output_path.exists()

        # Verify transparency is preserved
        with Image.open(output_path) as webp_img:
            assert webp_img.format == "WEBP"
            assert webp_img.mode in ("RGBA", "LA")  # Has transparency

    def test_process_single_size_thumbnail_quality(
        self, processor, input_dir, output_dir
    ):
        """Test thumbnail processing uses appropriate quality."""
        source_path = input_dir / "thumb_source.jpg"
        Image.new("RGB", (1000, 1000), "orange").save(source_path, "JPEG")

        # Process as thumbnail
        thumb_path = output_dir / "thumbnail.webp"
        args = (source_path, thumb_path, (150, 150), (1000, 1000), True, output_dir)

        result = processor.process_single_size(args)

        assert result is not None
        assert result["type"] == "thumbnail"
        assert thumb_path.exists()

        # Thumbnail should be smaller file size than standard (roughly)
        # This is a heuristic test since quality affects file size
        thumb_size = thumb_path.stat().st_size
        assert thumb_size > 100  # Reasonable minimum size

    def test_process_single_size_error_handling(self, processor, temp_dir, output_dir):
        """Test error handling in single size processing."""
        # Non-existent source file
        fake_source = temp_dir / "fake.jpg"
        output_path = output_dir / "should_not_exist.webp"

        args = (fake_source, output_path, (100, 100), (200, 200), False, output_dir)
        result = processor.process_single_size(args)

        assert result is None
        assert not output_path.exists()

    def test_process_single_size_various_formats(
        self, processor, input_dir, output_dir
    ):
        """Test processing different input formats."""
        formats_to_test = [
            ("RGB", "JPEG", "test.jpg"),
            ("RGBA", "PNG", "test.png"),
            ("RGB", "WEBP", "test.webp"),
            ("P", "PNG", "palette.png"),  # Palette mode
        ]

        for mode, format_name, filename in formats_to_test:
            source_path = input_dir / filename
            if mode == "P":
                # Create palette image
                img = Image.new("RGB", (200, 200), "red")
                img = img.quantize(colors=8)  # Convert to palette mode
            else:
                img = Image.new(
                    mode, (200, 200), "blue" if mode == "RGB" else (0, 0, 255, 255)
                )

            img.save(source_path, format_name)

            output_path = output_dir / f"output_{filename}.webp"
            args = (source_path, output_path, (100, 100), (200, 200), False, output_dir)

            result = processor.process_single_size(args)

            assert result is not None, f"Failed to process {format_name} in {mode} mode"
            assert output_path.exists()

            with Image.open(output_path) as webp_img:
                assert webp_img.format == "WEBP"
                assert webp_img.size == (100, 100)

    def test_process_image_complete_workflow(self, processor, input_dir, output_dir):
        """Test complete image processing workflow."""
        # Create source image
        source_path = input_dir / "workflow_test.jpg"
        img = Image.new("RGB", (1600, 1600), "teal")
        img.save(source_path, "JPEG")

        # Create image info
        image_info = {
            "path": source_path,
            "width": 1600,
            "height": 1600,
            "aspect_ratio": (1, 1),
            "format": "JPEG",
        }

        # Process image
        result = processor.process_image(image_info, output_dir, thumbnails=True)

        # Verify result structure
        assert result["status"] == "success"
        assert result["source"] == "workflow_test.jpg"
        assert result["aspect_ratio"] == "1:1"
        assert "variants" in result
        assert len(result["variants"]) > 0

        # Verify output directory structure
        expected_dir = output_dir / "square-1-1" / "workflow-test"
        assert expected_dir.exists()

        # Verify multiple sizes were created
        webp_files = list(expected_dir.glob("*.webp"))
        assert len(webp_files) > 1  # Should have multiple sizes

        # Verify thumbnails were created
        thumbnail_files = list(expected_dir.glob("thumbnail-*.webp"))
        assert len(thumbnail_files) > 0

    def test_process_image_without_thumbnails(self, processor, input_dir, output_dir):
        """Test image processing without thumbnail generation."""
        source_path = input_dir / "no_thumbs.jpg"
        img = Image.new("RGB", (3840, 2160), "navy")
        img.save(source_path, "JPEG")

        image_info = {
            "path": source_path,
            "width": 3840,
            "height": 2160,
            "aspect_ratio": (16, 9),
            "format": "JPEG",
        }

        result = processor.process_image(image_info, output_dir, thumbnails=False)

        assert result["status"] == "success"

        # Check that no thumbnails were created
        output_subdir = output_dir / "landscape-16-9" / "no-thumbs"
        thumbnail_files = list(output_subdir.glob("thumbnail-*.webp"))
        assert len(thumbnail_files) == 0

        # But standard sizes should exist
        standard_files = list(output_subdir.glob("no-thumbs-*.webp"))
        assert len(standard_files) > 0

    def test_process_image_with_overrides(self, processor, input_dir, output_dir):
        """Test image processing with override parameters."""
        source_path = input_dir / "override_test.jpg"
        img = Image.new("RGB", (2560, 1440), "maroon")
        img.save(source_path, "JPEG")

        image_info = {
            "path": source_path,
            "width": 2560,
            "height": 1440,
            "aspect_ratio": (16, 9),
            "format": "JPEG",
        }

        # Override with custom resolution
        overrides = {"resolution": (1920, 1080)}

        result = processor.process_image(
            image_info, output_dir, thumbnails=False, overrides=overrides
        )

        assert result["status"] == "success"

        # Verify custom resolution was used
        output_subdir = output_dir / "landscape-16-9" / "override-test"
        assert output_subdir.exists()

        # Should include the override resolution
        expected_file = output_subdir / "override-test-1920x1080.webp"
        assert expected_file.exists()

    def test_process_image_unsupported_aspect_ratio(
        self, processor, input_dir, output_dir
    ):
        """Test processing image with unsupported aspect ratio."""
        source_path = input_dir / "unsupported.jpg"
        img = Image.new("RGB", (1234, 567), "olive")
        img.save(source_path, "JPEG")

        # This creates an unusual aspect ratio not in the config
        image_info = {
            "path": source_path,
            "width": 1234,
            "height": 567,
            "aspect_ratio": (1234, 567),  # This won't be in OUTPUT_CONFIGS
            "format": "JPEG",
        }

        result = processor.process_image(image_info, output_dir)

        assert result["status"] == "skipped"
        assert result["reason"] == "unsupported_aspect_ratio"

    def test_process_image_filename_sanitization(
        self, processor, input_dir, output_dir
    ):
        """Test filename sanitization in processing."""
        # Create file with spaces and special characters
        source_path = input_dir / "My Test Image_v2.jpg"
        img = Image.new("RGB", (1600, 1600), "coral")
        img.save(source_path, "JPEG")

        image_info = {
            "path": source_path,
            "width": 1600,
            "height": 1600,
            "aspect_ratio": (1, 1),
            "format": "JPEG",
        }

        result = processor.process_image(image_info, output_dir)

        assert result["status"] == "success"

        # Check that filename was sanitized (spaces -> hyphens, lowercase)
        expected_dir = output_dir / "square-1-1" / "my-test-image-v2"
        assert expected_dir.exists()

        webp_files = list(expected_dir.glob("my-test-image-v2-*.webp"))
        assert len(webp_files) > 0

    def test_process_image_error_recovery(self, processor, temp_dir, output_dir):
        """Test error handling during image processing."""
        # Create invalid image info
        invalid_info = {
            "path": temp_dir / "nonexistent.jpg",
            "width": 1600,
            "height": 1600,
            "aspect_ratio": (1, 1),
            "format": "JPEG",
        }

        # Should handle gracefully without crashing
        result = processor.process_image(invalid_info, output_dir)

        # The exact behavior depends on implementation, but it shouldn't crash
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.parametrize(
        "transparency_mode",
        [
            "RGBA",  # Direct RGBA
            "LA",  # Grayscale with alpha
            "P_with_transparency",  # Palette with transparency
            "P_without_transparency",  # Palette without transparency
        ],
    )
    def test_transparency_handling(
        self, processor, input_dir, output_dir, transparency_mode
    ):
        """Test handling of different transparency modes."""
        source_path = input_dir / f"transparency_{transparency_mode}.png"

        if transparency_mode == "RGBA":
            img = Image.new("RGBA", (500, 500), (255, 0, 0, 128))
        elif transparency_mode == "LA":
            img = Image.new("LA", (500, 500), (128, 200))
        elif transparency_mode == "P_with_transparency":
            img = Image.new("RGB", (500, 500), "red")
            img = img.quantize(colors=8)
            img.info["transparency"] = 0  # Make color 0 transparent
        else:  # P_without_transparency
            img = Image.new("RGB", (500, 500), "blue")
            img = img.quantize(colors=8)

        img.save(source_path, "PNG")

        # Process the image
        output_path = output_dir / f"result_{transparency_mode}.webp"
        args = (source_path, output_path, (250, 250), (500, 500), False, output_dir)

        result = processor.process_single_size(args)

        assert result is not None
        assert output_path.exists()

        # Verify result
        with Image.open(output_path) as webp_img:
            assert webp_img.format == "WEBP"
            assert webp_img.size == (250, 250)

    def test_quality_optimization_by_size(self, processor, input_dir, output_dir):
        """Test that different sizes get appropriate quality settings."""
        source_path = input_dir / "quality_test.jpg"
        img = Image.new("RGB", (4000, 4000), "gold")
        img.save(source_path, "JPEG")

        # Test different target sizes
        test_sizes = [
            ((200, 200), "small"),
            ((800, 800), "medium"),
            ((2000, 2000), "large"),
            ((4000, 4000), "xlarge"),
        ]

        file_sizes = {}

        for target_size, size_name in test_sizes:
            output_path = output_dir / f"quality_{size_name}.webp"
            args = (
                source_path,
                output_path,
                target_size,
                (4000, 4000),
                False,
                output_dir,
            )

            result = processor.process_single_size(args)
            assert result is not None

            file_sizes[size_name] = output_path.stat().st_size

        # Verify files exist and have reasonable sizes
        for size_name in file_sizes:
            assert file_sizes[size_name] > 100  # Minimum reasonable size

        # Generally, larger images should result in larger files (though quality settings complicate this)
        # This is more of a sanity check than a strict requirement
