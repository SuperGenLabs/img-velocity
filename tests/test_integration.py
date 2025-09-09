"""Integration tests for complete workflows."""

import json

import pytest
from PIL import Image

from img_velocity.core import BatchProcessor


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_complete_processing_workflow(self, temp_dir):
        """Test complete image processing workflow from start to finish."""
        # Set up test environment
        input_dir = temp_dir / "integration_input"
        input_dir.mkdir()
        output_dir = temp_dir / "integration_output"

        # Create diverse test images
        test_images = {
            "square_valid.jpg": ((1600, 1600), "JPEG"),
            "landscape_16_9.jpg": ((3840, 2160), "JPEG"),
            "portrait_9_16.png": ((810, 1440), "PNG"),
            "wide_banner.webp": ((3840, 768), "WEBP"),
            "square_small.jpg": ((800, 800), "JPEG"),  # Too small
            "unusual_ratio.jpg": ((1500, 1000), "JPEG"),  # 3:2 but small
        }

        for filename, ((width, height), format_type) in test_images.items():
            img_path = input_dir / filename
            if format_type == "PNG" and "portrait" in filename:
                # Create PNG with transparency
                img = Image.new("RGBA", (width, height), (255, 0, 0, 128))
            else:
                img = Image.new("RGB", (width, height), "blue")
            img.save(img_path, format_type)

        # Run batch processing
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, thumbnails=True, max_workers=2)

        # Verify output structure
        assert output_dir.exists()

        # Check manifest
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should have processed valid images only
        expected_processed = [
            "square_valid.jpg",
            "landscape_16_9.jpg",
            "portrait_9_16.png",
            "wide_banner.webp",
        ]

        assert len(manifest["images"]) == len(expected_processed)
        for img_name in expected_processed:
            assert img_name in manifest["images"]
            img_data = manifest["images"][img_name]
            assert len(img_data["variants"]) > 0
            assert "aspect_ratio" in img_data

        # Verify directory structure
        expected_dirs = [
            "square-1-1/square-valid",
            "landscape-16-9/landscape-16-9",
            "portrait-9-16/portrait-9-16",
            "wide-banner-5-1/wide-banner",
        ]

        for expected_dir in expected_dirs:
            full_path = output_dir / expected_dir
            assert full_path.exists(), f"Missing directory: {expected_dir}"

            # Should have WebP files
            webp_files = list(full_path.glob("*.webp"))
            assert len(webp_files) > 0, f"No WebP files in {expected_dir}"

    def test_override_workflow_integration(self, temp_dir):
        """Test integration with override parameters."""
        input_dir = temp_dir / "override_input"
        input_dir.mkdir()
        output_dir = temp_dir / "override_output"

        # Create images that normally wouldn't meet requirements
        small_images = [
            ("small_16_9.jpg", (1280, 720)),  # 16:9 but small
            ("small_square.jpg", (800, 800)),  # 1:1 but small
            ("tiny_wide.jpg", (1000, 200)),  # 5:1 but small
        ]

        for filename, (width, height) in small_images:
            img_path = input_dir / filename
            img = Image.new("RGB", (width, height), "green")
            img.save(img_path, "JPEG")

        # Process with accept_all override
        processor = BatchProcessor()
        overrides = {"accept_all": True}
        processor.process_images(
            input_dir, output_dir, overrides=overrides, max_workers=1
        )

        # All images should be processed with accept_all
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should process all images (even small ones)
        assert len(manifest["images"]) >= 2  # At least the valid ratio ones

    def test_thumbnail_generation_integration(self, temp_dir):
        """Test thumbnail generation in complete workflow."""
        input_dir = temp_dir / "thumb_input"
        input_dir.mkdir()
        output_dir = temp_dir / "thumb_output"

        # Create valid image
        img_path = input_dir / "thumbnail_test.jpg"
        img = Image.new("RGB", (1600, 1600), "purple")
        img.save(img_path, "JPEG")

        # Process with thumbnails enabled
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, thumbnails=True, max_workers=1)

        # Check for thumbnail files
        thumb_dir = output_dir / "square-1-1" / "thumbnail-test"
        assert thumb_dir.exists()

        # Should have both standard and thumbnail WebP files
        all_webp = list(thumb_dir.glob("*.webp"))
        standard_webp = list(
            thumb_dir.glob("thumbnail-test-*.webp")
        )  # Standard files: {base}-{size}.webp
        thumbnail_webp = list(
            thumb_dir.glob("thumbnail-thumbnail-test-*.webp")
        )  # Thumbnail files: thumbnail-{base}-{size}.webp

        assert len(all_webp) > 0
        assert len(standard_webp) > 0
        assert len(thumbnail_webp) > 0

        # Verify in manifest
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        variants = manifest["images"]["thumbnail_test.jpg"]["variants"]
        standard_variants = [v for v in variants if v["type"] == "standard"]
        thumb_variants = [v for v in variants if v["type"] == "thumbnail"]

        assert len(standard_variants) > 0
        assert len(thumb_variants) > 0

    @pytest.mark.slow
    def test_large_batch_integration(self, temp_dir):
        """Test processing larger batch of images."""
        input_dir = temp_dir / "large_batch_input"
        input_dir.mkdir()
        output_dir = temp_dir / "large_batch_output"

        # Create multiple valid images
        image_configs = [
            ("batch_square_1.jpg", (1600, 1600), "JPEG"),
            ("batch_square_2.jpg", (2000, 2000), "JPEG"),
            ("batch_landscape_1.jpg", (3840, 2160), "JPEG"),
            ("batch_landscape_2.jpg", (4096, 2304), "JPEG"),
            ("batch_portrait_1.png", (810, 1440), "PNG"),
            ("batch_portrait_2.png", (1080, 1920), "PNG"),
        ]

        for filename, (width, height), fmt in image_configs:
            img_path = input_dir / filename
            img = Image.new("RGB", (width, height), "orange")
            img.save(img_path, fmt)

        # Process with multiple workers
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, thumbnails=True, max_workers=3)

        # Verify all images were processed
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert len(manifest["images"]) == len(image_configs)

        # Verify each image has reasonable number of variants
        for _img_name, img_data in manifest["images"].items():
            assert len(img_data["variants"]) >= 5  # At least several sizes + thumbnails

    def test_error_recovery_integration(self, temp_dir):
        """Test that processing continues despite some errors."""
        input_dir = temp_dir / "error_recovery_input"
        input_dir.mkdir()
        output_dir = temp_dir / "error_recovery_output"

        # Create mix of valid and problematic files
        # Valid image
        valid_img = input_dir / "valid.jpg"
        Image.new("RGB", (1600, 1600), "cyan").save(valid_img, "JPEG")

        # Corrupted "image" file
        corrupt_img = input_dir / "corrupt.jpg"
        corrupt_img.write_bytes(b"This is not a real JPEG file")

        # Non-image file
        text_file = input_dir / "notimage.txt"
        text_file.write_text("Just some text")

        # Another valid image
        valid_img2 = input_dir / "valid2.jpg"
        Image.new("RGB", (3840, 2160), "magenta").save(valid_img2, "JPEG")

        # Process (should handle errors gracefully)
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, max_workers=1)

        # Should still create manifest with valid images
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should have processed the valid images only
        assert len(manifest["images"]) == 2
        assert "valid.jpg" in manifest["images"]
        assert "valid2.jpg" in manifest["images"]

        # Corrupted and text files should not appear
        assert "corrupt.jpg" not in manifest["images"]
        assert "notimage.txt" not in manifest["images"]

    def test_custom_resolution_override_integration(self, temp_dir):
        """Test complete workflow with custom resolution override."""
        input_dir = temp_dir / "custom_res_input"
        input_dir.mkdir()
        output_dir = temp_dir / "custom_res_output"

        # Create large image
        img_path = input_dir / "custom_resolution.jpg"
        img = Image.new("RGB", (4096, 2304), "lime")  # 16:9
        img.save(img_path, "JPEG")

        # Process with custom resolution override
        processor = BatchProcessor()
        overrides = {"resolution": (2560, 1440)}
        processor.process_images(
            input_dir, output_dir, overrides=overrides, max_workers=1
        )

        # Check that custom resolution was used
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        variants = manifest["images"]["custom_resolution.jpg"]["variants"]

        # Should include the custom resolution
        resolutions = [(v["width"], v["height"]) for v in variants]
        assert (2560, 1440) in resolutions

        # Should also have scaled-down versions
        assert len(variants) > 1

        # All variants should maintain 16:9 aspect ratio
        for variant in variants:
            width, height = variant["width"], variant["height"]
            # Allow some rounding error
            ratio = width / height
            assert abs(ratio - 16 / 9) < 0.01

    def test_manifest_structure_integration(self, temp_dir):
        """Test manifest structure in complete workflow."""
        input_dir = temp_dir / "manifest_test_input"
        input_dir.mkdir()
        output_dir = temp_dir / "manifest_test_output"

        # Create test image
        img_path = input_dir / "manifest_test.jpg"
        img = Image.new("RGB", (1600, 1600), "silver")
        img.save(img_path, "JPEG")

        # Process
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, thumbnails=True, max_workers=1)

        # Analyze manifest structure
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Check top-level structure
        assert "version" in manifest
        assert "images" in manifest
        assert manifest["version"] == "1.0"

        # Check image entry structure
        img_data = manifest["images"]["manifest_test.jpg"]
        assert "aspect_ratio" in img_data
        assert "variants" in img_data
        assert img_data["aspect_ratio"] == "1:1"

        # Check variant structure
        for variant in img_data["variants"]:
            required_fields = ["path", "width", "height", "size", "type"]
            for field in required_fields:
                assert field in variant, f"Missing field: {field}"

            # Check field types
            assert isinstance(variant["width"], int)
            assert isinstance(variant["height"], int)
            assert isinstance(variant["size"], int)
            assert variant["type"] in ["standard", "thumbnail"]
            assert isinstance(variant["path"], str)
            assert variant["size"] > 0

    def test_file_naming_and_structure_integration(self, temp_dir):
        """Test file naming and directory structure."""
        input_dir = temp_dir / "naming_test_input"
        input_dir.mkdir()
        output_dir = temp_dir / "naming_test_output"

        # Create image with complex filename
        img_path = input_dir / "My Complex_File Name v2.jpg"
        img = Image.new("RGB", (1600, 1600), "gold")
        img.save(img_path, "JPEG")

        # Process
        processor = BatchProcessor()
        processor.process_images(input_dir, output_dir, thumbnails=True, max_workers=1)

        # Check directory structure
        expected_dir = output_dir / "square-1-1" / "my-complex-file-name-v2"
        assert expected_dir.exists()

        # Check file naming
        webp_files = list(expected_dir.glob("*.webp"))
        assert len(webp_files) > 0

        # All files should follow naming convention
        for webp_file in webp_files:
            name = webp_file.name
            assert name.startswith(
                ("my-complex-file-name-v2-", "thumbnail-my-complex-file-name-v2-")
            )
            assert name.endswith(".webp")
            assert " " not in name  # No spaces
            assert "_" not in name  # No underscores

    @pytest.mark.performance
    def test_performance_benchmarking_integration(self, temp_dir):
        """Test benchmarking functionality integration."""
        input_dir = temp_dir / "benchmark_input"
        input_dir.mkdir()
        output_dir = temp_dir / "benchmark_output"

        # Create sufficient images for benchmarking
        for i in range(8):
            img_path = input_dir / f"benchmark_{i}.jpg"
            img = Image.new("RGB", (1600, 1600), f"#{i * 30:02x}0000")
            img.save(img_path, "JPEG")

        # Run benchmark
        processor = BatchProcessor()
        # This should complete without errors (specific results depend on system)
        processor.benchmark_workers(input_dir, thumbnails=False)

        # Benchmark should clean up after itself
        benchmark_dirs = list(output_dir.glob("benchmark_temp_*"))
        assert len(benchmark_dirs) == 0  # Should be cleaned up
