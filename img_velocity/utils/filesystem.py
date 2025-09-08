"""File system operations and utilities."""

import json
from pathlib import Path


class FileSystemUtils:
    """Handles file operations, directory creation, and manifest generation."""

    def generate_manifest(
        self, results: list[dict[str, any]], output_dir: Path
    ) -> None:
        """Generate manifest.json for processed images."""
        manifest = {"version": "1.0", "images": {}}

        for result in results:
            if result["status"] == "success":
                source = result["source"]
                if source not in manifest["images"]:
                    manifest["images"][source] = {
                        "aspect_ratio": result["aspect_ratio"],
                        "variants": [],
                    }
                manifest["images"][source]["variants"].extend(result["variants"])

        manifest_path = output_dir / "manifest.json"
        with manifest_path.open("w") as f:
            json.dump(manifest, f, indent=2)
