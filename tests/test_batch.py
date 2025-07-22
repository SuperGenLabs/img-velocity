"""Comprehensive tests for BatchProcessor class."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from img_velocity.core.batch import process_image_wrapper
from img_velocity.core.config import Configuration


class TestBatchProcessor:
    """Test BatchProcessor class functionality."""

    def test_batch_processor_initialization(self, batch_processor):
        """Test BatchProcessor initializes correctly."""
        assert isinstance(batch_processor.config, Configuration)
        assert batch_processor.validator is not None
        assert batch_processor.processor is not None
        assert batch_processor.progress_tracker is not None
        assert batch_processor.fs_utils is not None

    def test_scan_images_basic(self, batch_processor, sample_images):
        """Test basic image scanning functionality."""
        input_dir = sample_images["square_large"].parent

        all_files, valid_infos = batch_processor.scan_images(input_dir)

        # Should find image files
        assert len(all_files) > 0
        assert len(valid_infos) > 0
        assert len(valid_infos) <= len(all_files)  # Valid is subset of all

        # Verify all valid infos have required fields
        for info in valid_infos:
            assert "path" in info
            assert "width" in info
            assert "height" in info
            assert "aspect_ratio" in info
            assert "format" in info

    def test_scan_images_with_overrides(self, batch_processor, sample_images):
        """Test image scanning with override parameters."""
        input_dir = sample_images["square_large"].parent

        # Test accept_all override
        overrides = {"accept_all": True}
        all_files, valid_infos = batch_processor.scan_images(input_dir, overrides)

        # With accept_all, more images should be valid
        assert len(valid_infos) >= len(all_files) - 2  # Minus text files and corrupted

        # Test aspect ratio override
        overrides = {"aspect_ratio": (16, 9)}
        all_files, valid_infos = batch_processor.scan_images(input_dir, overrides)

        # Should only include 16:9 images
        for info in valid_infos:
            assert info["aspect_ratio"] == (16, 9)

    def test_scan_images_empty_directory(self, batch_processor, temp_dir):
        """Test scanning empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        all_files, valid_infos = batch_processor.scan_images(empty_dir)

        assert len(all_files) == 0
        assert len(valid_infos) == 0

    def test_scan_images_no_valid_images(self, batch_processor, temp_dir):
        """Test scanning directory with no valid images."""
        # Create directory with only text files
        no_images_dir = temp_dir / "no_images"
        no_images_dir.mkdir()

        (no_images_dir / "file1.txt").write_text("Not an image")
        (no_images_dir / "file2.doc").write_text("Also not an image")

        all_files, valid_infos = batch_processor.scan_images(no_images_dir)

        assert len(all_files) == 2  # Found files, but...
        assert len(valid_infos) == 0  # None are valid images

    @pytest.mark.parametrize(
        "max_workers,image_count,expected_max",
        [
            (None, 4, 4),  # None -> min(cpu_count, image_count, 8)
            (None, 12, 8),  # Capped at 8 when None
            (2, 10, 2),  # Explicit worker count
            (100, 5, 5),  # Limited by image count
            (70, 10, 10),  # Limited by platform max (60) - this should be 10, not 60
        ],
    )
    def test_determine_worker_count(
        self, batch_processor, max_workers, image_count, expected_max
    ):
        """Test worker count determination logic."""
        with patch("multiprocessing.cpu_count", return_value=8):
            result = batch_processor.determine_worker_count(max_workers, image_count)

            # Should not exceed platform limit of 60
            assert result <= 60
            # Should not exceed image count
            assert result <= image_count

            if max_workers is None:
                # Should be min(cpu_count, image_count, 8)
                assert result == min(8, image_count, 8)
            else:
                # Should be min(max_workers, image_count, 60)
                assert result == min(max_workers, image_count, 60)

    def test_determine_worker_count_edge_cases(self, batch_processor):
        """Test worker count determination with edge cases."""
        # Very high CPU count
        with patch("multiprocessing.cpu_count", return_value=128):
            result = batch_processor.determine_worker_count(None, 50)
            assert result <= 60  # Platform limit
            assert result <= 50  # Image count limit

        # Single image
        result = batch_processor.determine_worker_count(None, 1)
        assert result == 1

        # Zero images (edge case)
        result = batch_processor.determine_worker_count(None, 0)
        assert result >= 0

    @patch("img_velocity.core.batch.ProcessPoolExecutor")
    def test_process_with_multiprocessing(
        self, mock_executor, batch_processor, sample_images, output_dir
    ):
        """Test multiprocessing workflow."""
        # Set up mock
        mock_context = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_context

        # Create mock futures
        mock_futures = []
        for i in range(3):
            mock_future = MagicMock()
            mock_future.result.return_value = {
                "status": "success",
                "source": f"image_{i}.jpg",
                "variants": [],
            }
            mock_futures.append(mock_future)

        mock_context.submit.side_effect = mock_futures

        # Create valid image infos
        valid_infos = [
            {
                "path": Path(f"image_{i}.jpg"),
                "width": 1600,
                "height": 1600,
                "aspect_ratio": (1, 1),
            }
            for i in range(3)
        ]

        # Test the method
        with patch("img_velocity.core.batch.as_completed", return_value=mock_futures):
            results = batch_processor._process_with_multiprocessing(
                valid_infos, output_dir, False, 2, None
            )

        # Verify results
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)

        # Verify executor was called correctly
        mock_executor.assert_called_once_with(max_workers=2)
        assert mock_context.submit.call_count == 3

    def test_process_images_invalid_input_dir(
        self, batch_processor, temp_dir, output_dir
    ):
        """Test processing with invalid input directory."""
        fake_dir = temp_dir / "nonexistent"

        # Should handle gracefully
        batch_processor.process_images(fake_dir, output_dir)
        # Test passes if no exception is raised

    def test_process_images_no_images_found(
        self, batch_processor, temp_dir, output_dir
    ):
        """Test processing directory with no images."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        # Should handle gracefully
        batch_processor.process_images(empty_dir, output_dir)
        # Test passes if no exception is raised

    def test_process_images_complete_workflow(
        self, batch_processor, sample_images, output_dir
    ):
        """Test complete image processing workflow."""
        input_dir = sample_images["square_large"].parent

        # Run processing
        batch_processor.process_images(
            input_dir, output_dir, thumbnails=True, max_workers=2
        )

        # Verify output directory was created
        assert output_dir.exists()

        # Verify manifest was created
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        # Verify manifest content
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "version" in manifest
        assert "images" in manifest
        assert len(manifest["images"]) > 0

        # Verify at least some images were processed
        processed_images = 0
        for _img_name, img_data in manifest["images"].items():
            if len(img_data["variants"]) > 0:
                processed_images += 1

        assert processed_images > 0

    def test_process_images_with_overrides(
        self, batch_processor, sample_images, output_dir
    ):
        """Test processing with override parameters."""
        input_dir = sample_images["square_large"].parent
        overrides = {"accept_all": True}

        batch_processor.process_images(
            input_dir, output_dir, max_workers=1, overrides=overrides
        )

        # Should complete without errors
        assert output_dir.exists()
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

    @patch("img_velocity.core.batch.ProcessPoolExecutor")
    def test_process_images_with_errors(
        self, mock_executor, batch_processor, sample_images, output_dir
    ):
        """Test processing with some failures."""
        # Set up mock to simulate errors
        mock_context = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_context

        # Create mix of successful and failed futures - need enough for all 5 valid images
        mock_future_success = MagicMock()
        mock_future_success.result.return_value = {
            "status": "success",
            "source": "good.jpg",
            "variants": [],
            "aspect_ratio": (16, 9),  # Add required aspect_ratio field
        }

        mock_future_error = MagicMock()
        mock_future_error.result.side_effect = Exception("Processing failed")

        # Create enough futures for all valid images (5 total)
        all_futures = [
            mock_future_success,
            mock_future_error,
            mock_future_success,
            mock_future_error,
            mock_future_success,
        ]
        mock_context.submit.side_effect = all_futures

        input_dir = sample_images["square_large"].parent

        with patch("img_velocity.core.batch.as_completed", return_value=all_futures):
            # Should handle errors gracefully
            batch_processor.process_images(input_dir, output_dir, max_workers=1)

        # Should still create output and manifest
        assert output_dir.exists()

    def test_benchmark_workers_insufficient_images(
        self, batch_processor, temp_dir, output_dir
    ):
        """Test benchmark with insufficient images."""
        # Create directory with only 1 image
        input_dir = temp_dir / "input"
        input_dir.mkdir()

        img_path = input_dir / "single.jpg"
        Image.new("RGB", (1600, 1600), "red").save(img_path, "JPEG")

        # Should handle gracefully
        batch_processor.benchmark_workers(input_dir, output_dir)
        # Test passes if no exception is raised

    def test_benchmark_workers_basic_functionality(
        self, batch_processor, performance_images, output_dir
    ):
        """Test basic benchmarking functionality."""
        input_dir = performance_images[0].parent

        with patch("multiprocessing.cpu_count", return_value=4), patch.object(
            batch_processor, "_run_benchmark_tests"
        ) as mock_run_tests:
            mock_run_tests.return_value = [
                {"workers": 1, "time": 10.0, "images_per_second": 0.5},
                {"workers": 2, "time": 6.0, "images_per_second": 0.83},
                {"workers": 4, "time": 4.0, "images_per_second": 1.25},
            ]

            batch_processor.benchmark_workers(input_dir, output_dir)

            # Verify benchmark tests were called
            mock_run_tests.assert_called_once()

    def test_run_benchmark_tests(self, batch_processor, performance_images, output_dir):
        """Test benchmark test execution."""
        input_dir = performance_images[0].parent

        # Get some valid image infos
        _, valid_infos = batch_processor.scan_images(input_dir)
        valid_infos = valid_infos[:3]  # Limit for testing

        test_workers = [1, 2]

        # Run benchmark tests
        results = batch_processor._run_benchmark_tests(
            test_workers, valid_infos, output_dir, False, None
        )

        # Verify results structure
        assert len(results) <= len(test_workers)  # Some may fail

        for result in results:
            assert "workers" in result
            assert "time" in result
            assert "images_per_second" in result
            assert result["workers"] in test_workers
            assert result["time"] > 0
            assert result["images_per_second"] > 0

    def test_print_scan_summary(self, batch_processor, capsys):
        """Test scan summary printing."""
        overrides = {"aspect_ratio": (16, 9)}
        batch_processor._print_scan_summary(10, 6, 4, overrides)

        captured = capsys.readouterr()
        assert "Found 10 image files" in captured.out
        assert "6 meet requirements" in captured.out
        assert "4 will be skipped" in captured.out
        assert "aspect ratio 16:9" in captured.out

    def test_print_scan_summary_no_overrides(self, batch_processor, capsys):
        """Test scan summary without overrides."""
        batch_processor._print_scan_summary(5, 3, 2, None)

        captured = capsys.readouterr()
        assert "Found 5 image files" in captured.out
        assert "overrides" not in captured.out.lower()

    def test_finalize_processing(self, batch_processor, output_dir, capsys):
        """Test processing finalization and summary."""
        results = [
            {
                "status": "success",
                "source": "img1.jpg",
                "variants": [{"type": "standard"}, {"type": "thumbnail"}],
            },
            {
                "status": "success",
                "source": "img2.jpg",
                "variants": [{"type": "standard"}],
            },
            {"status": "error", "source": "img3.jpg", "error": "Processing failed"},
        ]

        with patch.object(
            batch_processor.fs_utils, "generate_manifest"
        ) as mock_manifest:
            batch_processor._finalize_processing(results, output_dir, 10, 8, 2, 4)

        captured = capsys.readouterr()

        # Verify summary output
        assert "PROCESSING COMPLETE" in captured.out
        assert "Total image files found:     10" in captured.out
        assert "Successfully processed:      2" in captured.out
        assert "Skipped (requirements):      2" in captured.out
        assert "Parallel workers used:       4" in captured.out
        assert "Total image variants created: 3" in captured.out

        # Verify manifest generation was called
        mock_manifest.assert_called_once_with(results, output_dir)

    def test_print_benchmark_results(self, batch_processor, capsys):
        """Test benchmark results printing."""
        results = [
            {"workers": 1, "time": 10.0, "images_per_second": 0.5},
            {"workers": 2, "time": 6.0, "images_per_second": 0.83},
            {"workers": 4, "time": 4.0, "images_per_second": 1.25},
        ]

        batch_processor._print_benchmark_results(results, cpu_count=4)

        captured = capsys.readouterr()

        assert "BENCHMARK RESULTS" in captured.out
        assert "RECOMMENDATION" in captured.out
        assert "Use --workers 4" in captured.out  # Best performer
        assert "🥇" in captured.out  # Winner marker
        assert "CPU cores: 4" in captured.out

    def test_process_image_wrapper_function(self, input_dir, output_dir):
        """Test the standalone wrapper function for multiprocessing."""
        # Create test image
        img_path = input_dir / "wrapper_test.jpg"
        Image.new("RGB", (1600, 1600), "purple").save(img_path, "JPEG")

        image_info = {
            "path": img_path,
            "width": 1600,
            "height": 1600,
            "aspect_ratio": (1, 1),
            "format": "JPEG",
        }

        # Test the wrapper function
        result = process_image_wrapper(image_info, output_dir, thumbnails=False)

        assert result["status"] == "success"
        assert result["source"] == "wrapper_test.jpg"
        assert len(result["variants"]) > 0

    def test_process_image_wrapper_with_overrides(self, input_dir, output_dir):
        """Test wrapper function with overrides."""
        img_path = input_dir / "wrapper_override.jpg"
        Image.new("RGB", (2560, 1440), "cyan").save(img_path, "JPEG")

        image_info = {
            "path": img_path,
            "width": 2560,
            "height": 1440,
            "aspect_ratio": (16, 9),
            "format": "JPEG",
        }

        overrides = {"resolution": (1920, 1080)}

        result = process_image_wrapper(
            image_info, output_dir, thumbnails=False, overrides=overrides
        )

        assert result["status"] == "success"
        # Should have custom resolution in variants
        variant_sizes = [(v["width"], v["height"]) for v in result["variants"]]
        assert (1920, 1080) in variant_sizes

    def test_batch_processor_integration_small_dataset(self, batch_processor, temp_dir):
        """Integration test with small, controlled dataset."""
        # Create controlled input
        input_dir = temp_dir / "integration_input"
        input_dir.mkdir()
        output_dir = temp_dir / "integration_output"

        # Create exactly 2 valid images
        img1 = input_dir / "valid1.jpg"
        Image.new("RGB", (1600, 1600), "red").save(img1, "JPEG")

        img2 = input_dir / "valid2.jpg"
        Image.new("RGB", (3840, 2160), "blue").save(img2, "JPEG")

        # Create 1 invalid image
        img3 = input_dir / "invalid.jpg"
        Image.new("RGB", (800, 600), "green").save(img3, "JPEG")  # Too small

        # Run processing
        batch_processor.process_images(
            input_dir, output_dir, thumbnails=True, max_workers=1
        )

        # Verify results
        assert output_dir.exists()

        # Check manifest
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should have processed 2 images
        assert len(manifest["images"]) == 2
        assert "valid1.jpg" in manifest["images"]
        assert "valid2.jpg" in manifest["images"]

        # Each processed image should have variants
        for _img_name, img_data in manifest["images"].items():
            assert len(img_data["variants"]) > 0
            assert "aspect_ratio" in img_data

    @patch("time.time")
    def test_progress_tracking_during_processing(
        self, mock_time, batch_processor, sample_images, output_dir
    ):
        """Test that progress tracking is called during processing."""
        # Mock time to control elapsed time calculations - provide many more values
        mock_time.side_effect = list(
            range(20)
        )  # 0, 1, 2, 3, ... 19 - enough for any number of calls

        input_dir = sample_images["square_large"].parent

        with patch.object(
            batch_processor.progress_tracker, "display_progress"
        ) as mock_progress:
            batch_processor.process_images(input_dir, output_dir, max_workers=1)

            # Progress should have been called multiple times
            assert mock_progress.call_count > 0

            # Verify progress calls have expected structure
            for call_args in mock_progress.call_args_list:
                args = call_args[0]
                assert len(args) >= 3  # current, total, elapsed_time
                assert isinstance(args[0], int)  # current
                assert isinstance(args[1], int)  # total
                assert isinstance(args[2], (int, float))  # elapsed_time
