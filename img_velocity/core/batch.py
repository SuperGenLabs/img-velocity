"""Batch processing orchestration."""

import multiprocessing
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.filesystem import FileSystemUtils
from ..utils.logging import get_logger
from ..utils.progress import ProgressTracker
from ..utils.security import SecurityValidator
from .config import Configuration
from .validator import ImageValidator

logger = get_logger(__name__.split(".")[-1])


def process_image_wrapper(
    image_info: Dict[str, Any],
    output_dir: Path,
    thumbnails: bool = False,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wrapper function for multiprocessing."""
    # Import here to avoid circular import
    from .processor import ImageProcessor

    config = Configuration()
    processor = ImageProcessor(config)
    return processor.process_image(image_info, output_dir, thumbnails, overrides)


class BatchProcessor:
    """Orchestrates batch processing of images with multiprocessing."""

    def __init__(self):
        self.config = Configuration()
        self.validator = ImageValidator(self.config)
        self.progress_tracker = ProgressTracker()
        self.fs_utils = FileSystemUtils()
        # Don't initialize processor here to avoid circular import
        self._processor = None

    @property
    def processor(self):
        """Lazy load processor to avoid circular import."""
        if self._processor is None:
            from .processor import ImageProcessor

            self._processor = ImageProcessor(self.config)
        return self._processor

    def scan_images(
        self, input_dir: Path, overrides: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Path], List[Dict[str, Any]]]:
        """Scan directory for valid images that meet requirements."""
        logger.info("Scanning for images...")

        all_image_files = []
        valid_image_infos = []

        for file_path in input_dir.iterdir():
            if file_path.is_file():
                try:
                    # Validate each file path
                    validated_path = SecurityValidator.validate_image_path(
                        file_path, input_dir
                    )
                    all_image_files.append(validated_path)
                    info = self.validator.get_image_info(validated_path)
                    if info and self.validator.meets_requirements_with_override(
                        info, overrides
                    ):
                        valid_image_infos.append(info)
                except ValueError as e:
                    logger.debug(f"Skipping invalid file {file_path}: {e}")
                    continue

        return all_image_files, valid_image_infos

    def determine_worker_count(
        self, max_workers: Optional[int], image_count: int
    ) -> int:
        """Determine optimal number of workers."""
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), image_count, 8)
        else:
            max_workers = min(max_workers, image_count)

        # Platform-specific worker limits (Windows has a 61 worker limit)
        return min(max_workers, 60)

    def process_images(
        self,
        input_dir: Path,
        output_dir: Path,
        thumbnails: bool = False,
        max_workers: Optional[int] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Process all images in input directory."""
        # Validate input paths
        try:
            input_dir = SecurityValidator.validate_path(input_dir)
            output_dir = SecurityValidator.validate_path(output_dir)
        except ValueError as e:
            logger.error(f"Invalid path: {e}")
            return

        if not input_dir.exists() or not input_dir.is_dir():
            logger.error(f"Invalid input directory: {input_dir}")
            return

        # Validate worker count
        try:
            max_workers = SecurityValidator.validate_worker_count(max_workers)
        except ValueError as e:
            logger.error(f"Invalid worker count: {e}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        # Scan for images
        all_image_files, valid_image_infos = self.scan_images(input_dir, overrides)

        total_files = len(all_image_files)
        valid_files = len(valid_image_infos)
        skipped_files = total_files - valid_files

        if total_files == 0:
            logger.warning("No image files found in the input directory.")
            return

        self._print_scan_summary(total_files, valid_files, skipped_files, overrides)

        if valid_files == 0:
            logger.warning("No valid images to process.")
            return

        # Determine worker count
        max_workers = self.determine_worker_count(max_workers, valid_files)
        logger.info(
            f"Processing {valid_files} images using {max_workers} parallel workers..."
        )

        # Process images
        results = self._process_with_multiprocessing(
            valid_image_infos, output_dir, thumbnails, max_workers, overrides
        )

        # Generate manifest and summary
        self._finalize_processing(
            results, output_dir, total_files, valid_files, skipped_files, max_workers
        )

    def _print_scan_summary(
        self,
        total_files: int,
        valid_files: int,
        skipped_files: int,
        overrides: Optional[Dict[str, Any]],
    ) -> None:
        """Print summary of scanned files."""
        logger.info(f"Found {total_files} image files:")

        if overrides:
            override_desc = []
            if "aspect_ratio" in overrides:
                override_desc.append(
                    f"aspect ratio {overrides['aspect_ratio'][0]}:{overrides['aspect_ratio'][1]}"
                )
            if "resolution" in overrides:
                override_desc.append(
                    f"resolution {overrides['resolution'][0]}x{overrides['resolution'][1]}"
                )
            logger.info(f"  • Using overrides: {', '.join(override_desc)}")

        logger.info(f"  • {valid_files} meet requirements and will be processed")
        if skipped_files > 0:
            logger.info(
                f"  • {skipped_files} will be skipped (don't meet requirements)"
            )

    def _process_with_multiprocessing(
        self,
        valid_image_infos: List[Dict[str, Any]],
        output_dir: Path,
        thumbnails: bool,
        max_workers: int,
        overrides: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Process images using multiprocessing."""
        results = []
        processed_count = 0
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_info = {
                executor.submit(
                    process_image_wrapper, info, output_dir, thumbnails, overrides
                ): info
                for info in valid_image_infos
            }

            # Process completed jobs
            for i, future in enumerate(as_completed(future_to_info)):
                current_time = time.time()
                elapsed_time = current_time - start_time

                # Update progress
                self.progress_tracker.display_progress(
                    i + 1, len(valid_image_infos), elapsed_time
                )

                try:
                    result = future.result()
                    results.append(result)

                    if result["status"] == "success":
                        processed_count += 1
                except Exception as e:
                    info = future_to_info[future]
                    results.append(
                        {
                            "status": "error",
                            "source": str(info["path"].name),
                            "error": str(e),
                        }
                    )

        # Final progress update
        total_time = time.time() - start_time
        self.progress_tracker.display_progress(
            len(valid_image_infos), len(valid_image_infos), total_time
        )
        logger.debug(
            "Processing complete"
        )  # Debug level since progress bar shows completion

        return results

    def _finalize_processing(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path,
        total_files: int,
        valid_files: int,
        skipped_files: int,
        max_workers: int,
    ) -> None:
        """Generate manifest and print final summary."""
        logger.info("Generating manifest...")
        self.fs_utils.generate_manifest(results, output_dir)

        processed_count = sum(1 for r in results if r["status"] == "success")

        # Log final summary
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total image files found:     {total_files}")
        logger.info(f"Successfully processed:      {processed_count}")
        logger.info(f"Skipped (requirements):      {skipped_files}")
        if valid_files - processed_count > 0:
            logger.warning(
                f"Failed during processing:    {valid_files - processed_count}"
            )
        logger.info(f"Parallel workers used:       {max_workers}")
        logger.info(f"Manifest file:               {output_dir / 'manifest.json'}")
        logger.info(f"Output directory:            {output_dir}")

        if processed_count > 0:
            total_variants = sum(
                len(r.get("variants", [])) for r in results if r["status"] == "success"
            )
            logger.info(f"Total image variants created: {total_variants}")
        logger.info("=" * 60)

    def benchmark_workers(
        self,
        input_dir: Path,
        thumbnails: bool = False,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Benchmark different worker counts to find optimal performance."""
        # Validate input path
        try:
            input_dir = SecurityValidator.validate_path(input_dir)
        except ValueError as e:
            logger.error(f"Invalid input directory: {e}")
            return

        logger.info("BENCHMARKING OPTIMAL WORKER COUNT")
        logger.info("=" * 50)

        # Get subset of images for testing
        _, valid_image_infos = self.scan_images(input_dir, overrides)
        valid_image_infos = valid_image_infos[:10]  # Limit to 10 for benchmarking

        if len(valid_image_infos) < 3:
            logger.error("Need at least 3 valid images for benchmarking")
            return

        logger.info(f"Testing with {len(valid_image_infos)} images...")

        # Test different worker counts
        cpu_count = multiprocessing.cpu_count()
        test_workers = [1, cpu_count // 2, cpu_count, cpu_count * 2]
        test_workers = [w for w in test_workers if w > 0 and w <= 60]
        test_workers = sorted(set(test_workers))

        if not test_workers:
            test_workers = [1]
        elif max(test_workers) < 60 and cpu_count < 30:
            test_workers.append(min(60, cpu_count * 3))
            test_workers = sorted(set(test_workers))

        results = self._run_benchmark_tests(
            test_workers, valid_image_infos, thumbnails, overrides
        )

        if results:
            self._print_benchmark_results(results, cpu_count)

    def _run_benchmark_tests(
        self,
        test_workers: List[int],
        valid_image_infos: List[Dict[str, Any]],
        thumbnails: bool,
        overrides: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Run benchmark tests with different worker counts."""
        results = []

        # Create a base temp directory for all benchmark runs
        temp_base = Path(tempfile.mkdtemp(prefix="img_velocity_benchmark_"))

        try:
            for workers in test_workers:
                logger.info(f"Testing {workers} workers...")

                # Create temporary output directory within temp base
                temp_output = temp_base / f"test_{workers}_workers"
                temp_output.mkdir(parents=True, exist_ok=True)

                start_time = time.time()

                try:
                    with ProcessPoolExecutor(max_workers=workers) as executor:
                        futures = [
                            executor.submit(
                                process_image_wrapper,
                                info,
                                temp_output,
                                thumbnails,
                                overrides,
                            )
                            for info in valid_image_infos
                        ]

                        for future in as_completed(futures):
                            future.result()  # Wait for completion

                    elapsed = time.time() - start_time
                    images_per_second = len(valid_image_infos) / elapsed

                    results.append(
                        {
                            "workers": workers,
                            "time": elapsed,
                            "images_per_second": images_per_second,
                        }
                    )

                    logger.info(
                        f"   {elapsed:.1f}s ({images_per_second:.1f} images/sec)"
                    )

                except Exception as e:
                    logger.error(f"   Failed: {e}")

                finally:
                    # Clean up this specific test directory
                    if temp_output.exists():
                        shutil.rmtree(temp_output)
        finally:
            # Clean up the entire temp base directory
            if temp_base.exists():
                shutil.rmtree(temp_base, ignore_errors=True)

        return results

    def _print_benchmark_results(
        self, results: List[Dict[str, Any]], cpu_count: int
    ) -> None:
        """Print benchmark results and recommendations."""
        best_result = max(results, key=lambda x: x["images_per_second"])

        logger.info("\nBENCHMARK RESULTS")
        logger.info("=" * 50)
        for result in results:
            marker = " [BEST]" if result == best_result else ""
            logger.info(
                f"{result['workers']:2d} workers: {result['time']:5.1f}s ({result['images_per_second']:4.1f} img/sec){marker}"
            )

        logger.info("\nRECOMMENDATION:")
        logger.info(
            f"   Use --workers {best_result['workers']} for optimal performance"
        )
        logger.info(
            f"   Expected speed: {best_result['images_per_second']:.1f} images per second"
        )

        logger.info("\nSYSTEM INFO:")
        logger.info(f"   CPU cores: {cpu_count}")
        logger.info(
            f"   Optimal workers: {best_result['workers']} ({best_result['workers'] / cpu_count:.1f}x cores)"
        )
        logger.info(
            "   Platform worker limit: 60 (applied for cross-platform compatibility)"
        )

        if best_result["workers"] > cpu_count:
            logger.info(
                "   Your system benefits from oversubscription (more workers than cores)"
            )
        elif best_result["workers"] < cpu_count:
            logger.info("   Your system is likely I/O or memory bound")
        else:
            logger.info("   Your system performs best with 1 worker per core")
