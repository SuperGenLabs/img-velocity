# img-velocity

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-lightgrey)](https://github.com/supergenlabs/img-velocity/releases)

> **Stop serving massive images to mobile users. Generate responsive WebP sets that actually make your site fast.**

I built this because I got tired of manually resizing images for every project. You know the drill - you've got a beautiful 4K hero image, but it's killing your mobile users' data plans and your Core Web Vitals. This tool takes your images and spits out perfectly optimized WebP variants that you can serve based on device type, screen size, or whatever responsive strategy you're using.

## Why You Need This

**The Problem**: Your 3MB hero image looks great on desktop, but it's murdering your mobile performance. Google's Core Web Vitals are judging you. Your users are bouncing because images take forever to load.

**The Solution**: Generate multiple WebP variants automatically. Serve the 320px version to phones, the 1920px version to desktops, and everything in between. Your images will load faster than your JavaScript framework.

```bash
# Turn this nightmare...
hero-image.jpg (3.2MB, 4096×2304)

# Into this dream...
hero-image-320x180.webp (12KB)    # Mobile
hero-image-768x432.webp (45KB)    # Tablet 
hero-image-1920x1080.webp (95KB)  # Desktop
hero-image-3840x2160.webp (180KB) # 4K displays
```

## What It Does

- **Parallel Processing**: Uses all your CPU cores to process images blazingly fast
- **Smart Compression**: Automatically adjusts WebP quality based on image size
- **Responsive Ready**: Generates the exact sizes you need for responsive design
- **Override Everything**: Don't like the defaults? Override aspect ratios and resolutions
- **Progress Tracking**: See exactly how fast your images are processing
- **Performance Tuning**: Built-in benchmarking finds the optimal worker count
- **Web Integration**: Generates a manifest.json for easy web framework integration
- **Security First**: Input validation, path sanitization, and injection protection
- **Library & CLI**: Use as a command-line tool or import as a Python library
- **Proper Logging**: Configurable logging levels instead of print statements

## Quick Start

### Install

```bash
# From PyPI (once published)
pip install img-velocity

# From source
git clone https://github.com/supergenlabs/img-velocity.git
cd img-velocity
pip install -e .
```

### Basic Usage

#### As a CLI Tool

```bash
# Convert all images in a directory
img-velocity input/ output/

# Include thumbnails for lazy loading
img-velocity input/ output/ --thumbnails

# Use all your CPU cores
img-velocity input/ output/ --workers 8

# Control logging verbosity
img-velocity input/ output/ --log-level DEBUG
```

#### As a Python Library

```python
import img_velocity

# Process a directory of images
results = img_velocity.process_images(
    "input/photos/",
    "output/optimized/",
    thumbnails=True,
    workers=8
)

# Process a single image
result = img_velocity.process_single_image(
    "hero-image.jpg",
    "output/",
    thumbnails=True
)

# Advanced: Use the classes directly
from img_velocity import Configuration, ImageProcessor

config = Configuration()
processor = ImageProcessor(config)
# ... custom processing logic
```

That's it. Point it at a folder of images, and it'll organize everything by aspect ratio and generate multiple WebP sizes for each.

## How to Use It

Here's how to integrate img-velocity into modern web applications:

### 1. Process Your Images

```bash
# Process all images with thumbnails for lazy loading
img-velocity assets/raw-images/ public/images/ --thumbnails
```

### 2. Use the Generated Structure

Your output will look like this:

```
public/images/
├── landscape-16-9/
│   └── hero-image/
│       ├── hero-image-3840x2160.webp
│       ├── hero-image-1920x1080.webp
│       ├── hero-image-1024x576.webp
│       └── thumbnail-hero-image-320x180.webp
├── square-1-1/
│   └── profile-pic/
│       ├── profile-pic-1600x1600.webp
│       └── thumbnail-profile-pic-150x150.webp
└── manifest.json
```

### 3. Implement in Your Application

#### Vue.js 3 + Tailwind CSS 4 Component

```vue
<template>
  <picture class="block">
    <!-- Mobile -->
    <source 
      :srcset="getVariant(768)" 
      media="(max-width: 768px)"
    />
    <!-- Tablet -->
    <source 
      :srcset="getVariant(1200)" 
      media="(max-width: 1200px)"
    />
    <!-- Desktop fallback -->
    <img 
      :src="fallbackSrc"
      :alt="alt"
      loading="lazy"
      class="size-full object-cover"
    />
  </picture>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import manifest from '@/assets/images/manifest.json'

interface Props {
  imageName: string
  alt: string
}

const props = defineProps<Props>()

const imageData = computed(() => manifest.images[props.imageName])

const variants = computed(() => 
  imageData.value?.variants.filter(v => v.type === 'standard') || []
)

const fallbackSrc = computed(() => {
  const largest = variants.value.reduce((max, current) => 
    current.width > max.width ? current : max
  , variants.value[0])
  return `/images/${largest?.path}`
})

const getVariant = (maxWidth: number) => {
  const variant = variants.value
    .filter(v => v.width <= maxWidth)
    .sort((a, b) => b.width - a.width)[0]
  return variant ? `/images/${variant.path}` : fallbackSrc.value
}
</script>
```

Usage in your Vue template:
```vue
<ResponsiveImage 
  image-name="hero-image.jpg" 
  alt="Hero image"
/>
```

#### FastAPI Backend Integration

Process images on-demand or in batch using FastAPI:

```python
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import img_velocity
import aiofiles
import uuid

app = FastAPI()

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("static/images")

@app.post("/api/images/process")
async def process_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Process single image upload."""
    # Save uploaded file
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    async with aiofiles.open(input_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Process image immediately
    result = img_velocity.process_single_image(
        input_path,
        OUTPUT_DIR,
        thumbnails=True
    )
    
    # Clean up original after processing
    background_tasks.add_task(input_path.unlink)
    
    return JSONResponse(content=result)

@app.post("/api/images/batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...)
):
    """Process multiple images in batch."""
    batch_id = str(uuid.uuid4())
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(exist_ok=True)
    
    # Save all uploaded files
    for file in files:
        file_path = batch_dir / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    
    # Process in background
    background_tasks.add_task(
        process_batch_images,
        batch_dir,
        OUTPUT_DIR / batch_id
    )
    
    return {"batch_id": batch_id, "status": "processing"}

def process_batch_images(input_dir: Path, output_dir: Path):
    """Background task to process images."""
    results = img_velocity.process_images(
        input_dir,
        output_dir,
        thumbnails=True,
        workers=4
    )
    # Could save results to database or cache here
    # Clean up input directory after processing
    import shutil
    shutil.rmtree(input_dir)

@app.get("/api/images/{image_id}/variants")
async def get_image_variants(image_id: str):
    """Get all variants for a processed image."""
    manifest_path = OUTPUT_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"error": "No processed images found"}
    
    import json
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Find image by ID or name
    for image_name, data in manifest["images"].items():
        if image_id in image_name:
            return data
    
    return {"error": "Image not found"}
```

Then in your Vue.js app, fetch and display images:

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const imageVariants = ref(null)

async function uploadAndProcess(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await fetch('/api/images/process', {
    method: 'POST',
    body: formData
  })
  
  const result = await response.json()
  imageVariants.value = result.variants
}

// Use processed images
const getImageUrl = (variant) => {
  return `/static/images/${variant.path}`
}
</script>
```

#### Plain HTML Example

```html
<picture>
  <source media="(max-width: 768px)" 
          srcset="/images/landscape-16-9/hero/hero-1024x576.webp">
  <source media="(max-width: 1200px)" 
          srcset="/images/landscape-16-9/hero/hero-1920x1080.webp">
  <img src="/images/landscape-16-9/hero/hero-3840x2160.webp" 
       alt="Hero image" 
       loading="lazy">
</picture>
```

#### CSS Background Images

```css
.hero-section {
  background-image: url('/images/landscape-16-9/hero/hero-1024x576.webp');
}

@media (min-width: 769px) {
  .hero-section {
    background-image: url('/images/landscape-16-9/hero/hero-1920x1080.webp');
  }
}

@media (min-width: 1201px) {
  .hero-section {
    background-image: url('/images/landscape-16-9/hero/hero-3840x2160.webp');
  }
}
```

## Advanced Usage

### Override Default Requirements

Sometimes you want to process images that don't meet the default size requirements:

```bash
# Accept any image, regardless of size
img-velocity input/ output/ --override

# Only process 16:9 images
img-velocity input/ output/ --override aspect-ratio="16:9"

# Set custom minimum resolution
img-velocity input/ output/ --override resolution="1920x1080"

# Combine requirements
img-velocity input/ output/ --override aspect-ratio="21:9" resolution="2560x1080"
```

### Find Your Optimal Settings

```bash
# Benchmark different worker counts
img-velocity --benchmark input/
```

This will test 1, 2, 4, 8+ workers and tell you which gives the best performance on your system.

### Logging and Debugging

Control the verbosity of output with the `--log-level` flag:

```bash
# Show only errors
img-velocity input/ output/ --log-level ERROR

# Normal operation (default)
img-velocity input/ output/ --log-level INFO

# Verbose output for debugging
img-velocity input/ output/ --log-level DEBUG
```

### Supported Image Types & Requirements

| Aspect Ratio | Min Resolution | Output Folder | Best For |
|--------------|----------------|---------------|----------|
| **1:1** | 1600×1600 | `square-1-1` | Avatars, logos, product shots |
| **16:9** | 3840×2160 | `landscape-16-9` | Hero images, videos, banners |
| **4:3** | 2048×1536 | `landscape-4-3` | Traditional photos |
| **3:2** | 3456×2304 | `landscape-3-2` | DSLR photos |
| **9:16** | 810×1440 | `portrait-9-16` | Mobile-first content |
| **3:4** | 1536×2048 | `portrait-3-4` | Portrait photos |
| **2:3** | 1024×1536 | `portrait-2-3` | Book covers, posters |
| **5:1** | 3840×768 | `wide-banner-5-1` | Wide banners |
| **8:1** | 3840×480 | `slim-banner-8-1` | Very wide headers |

**Input formats**: JPEG, PNG, WebP

## Understanding the Output

### Generated Directory Structure

```
output/
├── landscape-16-9/           # Aspect ratio folder
│   ├── my-hero-image/        # Sanitized filename folder
│   │   ├── my-hero-image-3840x2160.webp    # Largest size
│   │   ├── my-hero-image-1920x1080.webp    # Desktop
│   │   ├── my-hero-image-1024x576.webp     # Tablet
│   │   ├── my-hero-image-428x241.webp      # Mobile
│   │   ├── thumbnail-my-hero-image-320x180.webp  # Thumbnail
│   │   └── thumbnail-my-hero-image-160x90.webp   # Small thumb
│   └── another-image/
│       └── (similar structure)
├── square-1-1/
│   └── (square images)
├── portrait-9-16/
│   └── (portrait images)
└── manifest.json             # JSON index of all variants
```

### Manifest File Structure

The `manifest.json` makes it easy to integrate with any web framework:

```json
{
  "version": "1.0",
  "images": {
    "hero-image.jpg": {
      "aspect_ratio": "16:9",
      "variants": [
        {
          "path": "landscape-16-9/hero-image/hero-image-3840x2160.webp",
          "width": 3840,
          "height": 2160,
          "size": 245680,
          "type": "standard"
        },
        {
          "path": "landscape-16-9/hero-image/thumbnail-hero-image-320x180.webp",
          "width": 320,
          "height": 180,
          "size": 12340,
          "type": "thumbnail"
        }
      ]
    }
  }
}
```

## Customizing the Configuration

Want different output sizes or aspect ratios? You can modify the configuration:

### Adding New Aspect Ratios

```python
# In img_velocity/core/config.py

# 1. Add minimum requirements
MIN_REQUIREMENTS = {
    # ... existing ratios ...
    (21, 9): (3440, 1440),  # Ultra-wide monitors
}

# 2. Add output configuration
OUTPUT_CONFIGS = {
    # ... existing configs ...
    (21, 9): {
        'folder': 'ultrawide-21-9',
        'sizes': [
            (3440, 1440),   # Native ultrawide
            (2560, 1097),   # Scaled ultrawide
            (1920, 823),    # Standard scaled
            (1024, 439)     # Mobile scaled
        ],
        'thumbnail_sizes': [(320, 137), (160, 69)]
    },
}
```

### Adjusting Quality Settings

```python
# In Configuration.get_webp_quality()
@staticmethod
def get_webp_quality(width: int, height: int, is_thumbnail: bool = False) -> int:
    max_dim = max(width, height)
    
    if is_thumbnail:
        return 65  # Higher quality for thumbs
    elif max_dim <= 800:
        return 85  # High quality for small images
    elif max_dim <= 2000:
        return 90  # Premium quality for medium
    else:
        return 82  # Balanced for large images
```

### Custom Size Variants

```python
# Modify any aspect ratio's output sizes
OUTPUT_CONFIGS = {
    (16, 9): {
        'folder': 'landscape-16-9',
        'sizes': [
            (3840, 2160),  # 4K
            (2560, 1440),  # 1440p
            (1920, 1080),  # 1080p
            (1366, 768),   # Common laptop resolution
            (768, 432),    # Tablet landscape
            (428, 241),    # iPhone 14 Pro Max width
        ],
        'thumbnail_sizes': [(320, 180), (160, 90)]
    }
}
```

## Project Architecture

```
img-velocity/
├── img_velocity/                # Main package directory
│   ├── __init__.py              # Package exports and library API
│   ├── main.py                  # CLI entry point
│   ├── cli/                     # Command-line interface
│   │   ├── __init__.py          # CLI module exports
│   │   └── parser.py            # Argument parsing and validation
│   ├── core/                    # Core processing logic
│   │   ├── __init__.py          # Core module exports
│   │   ├── batch.py             # Parallel batch processing orchestration
│   │   ├── config.py            # Aspect ratios, sizes, and quality settings
│   │   ├── processor.py         # Image processing and WebP conversion
│   │   └── validator.py         # Image validation and requirements checking
│   └── utils/                   # Utility modules
│       ├── __init__.py          # Utils module exports
│       ├── filesystem.py        # File operations and manifest generation
│       ├── helpers.py           # General utility functions
│       ├── logging.py           # Logging configuration and handlers
│       ├── progress.py          # Progress bar and ETA tracking
│       └── security.py          # Input validation and path sanitization
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration and fixtures
│   ├── test_batch.py           # Batch processor tests
│   ├── test_cli.py             # CLI tests
│   ├── test_config.py          # Configuration tests
│   ├── test_integration.py     # Integration tests
│   ├── test_processor.py       # Image processor tests
│   ├── test_utils.py           # Utility function tests
│   └── test_validator.py       # Validator tests
├── .github/
│   └── workflows/
│       ├── build.yml           # Build and release workflow
│       └── ci.yml              # Continuous integration workflow
├── LICENSE                     # MIT license
├── Makefile                    # Development convenience commands
├── README.md                   # This file
├── pyproject.toml              # Package configuration and metadata
├── pytest.ini                  # Pytest configuration
└── requirements.txt            # Production dependency (Pillow)
```

### Key Components

- **`Configuration`**: Manages aspect ratios, minimum requirements, and output sizes
- **`ImageValidator`**: Checks if images meet requirements and handles overrides
- **`ImageProcessor`**: Core image processing with smart sharpening and WebP conversion
- **`BatchProcessor`**: Orchestrates parallel processing and progress tracking
- **`ProgressTracker`**: Real-time progress bars with ETA calculations
- **`SecurityValidator`**: Input validation and path sanitization for security
- **Logging System**: Structured logging with configurable levels

## Contributing

I'd love your help making this tool even better! Here's how to get started:

### Development Setup

```bash
git clone https://github.com/supergenlabs/img-velocity.git
cd img-velocity

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Optional: Install test dependencies
pip install -e .[test]
```

**Note**: There's a `Makefile` included for development convenience (e.g., `make format`, `make test`), but it's completely optional. The package works perfectly fine with standard Python tools.

### Code Quality Standards

I'm pretty particular about code quality. Here's what I expect:

```bash
# Format your code
make format  # or: black img_velocity/ && ruff format img_velocity/

# Lint everything  
make lint    # or: ruff check img_velocity/ && mypy img_velocity/

# Run security checks
make security  # or: bandit -r img_velocity/ -ll

# Before you commit
make pre-commit  # Runs format, lint, and fast tests
```

### Testing Requirements

**This is non-negotiable: minimum 90% test coverage.** I've built a comprehensive test suite, and I expect contributions to maintain this standard.

```bash
# Run all tests with coverage
make test  # or: pytest --cov=img_velocity --cov-fail-under=80

# Fast tests during development
make test-fast  # or: pytest -x -q --tb=short
```

### Test Structure

```python
# Example test structure
class TestImageProcessor:
    def test_smart_sharpening_logic(self):
        """Test sharpening is applied correctly based on downscale factor."""
        # Test implementation
        
    def test_transparency_preservation(self):
        """Test PNG alpha channels are preserved in WebP output."""
        # Test implementation
```

### Pull Request Process

1. **Fork and branch**: Create a feature branch from `main`
2. **Code**: Write your changes following the coding standards
3. **Test**: Ensure 90%+ coverage and all tests pass
4. **Document**: Update docs if you're changing behavior
5. **PR**: Submit with a clear description of what and why

#### PR Title Format
```
Type: Brief description

Examples:
Add: Support for AVIF format
Fix: Memory leak in batch processing  
Docs: Update configuration examples
Perf: Optimize image processing pipeline
```

## Security Features

img-velocity includes comprehensive security measures:

- **Path Traversal Protection**: All file paths are validated and sanitized
- **Input Validation**: Resolution limits (1-50,000px) prevent resource exhaustion
- **Safe Filename Handling**: Automatic sanitization of filenames
- **No Command Injection**: No shell commands or dynamic code execution
- **Resource Limits**: Worker count limits prevent system overload

## Performance Tips

### Optimal Worker Counts
- **CPU-bound systems**: Start with `--workers 4-8`
- **High-core systems**: Try `--workers 16` or run `--benchmark`
- **I/O-bound systems**: Often benefit from more workers than CPU cores

### Processing Large Batches
```bash
# For 100+ images, use benchmarking to find optimal settings
img-velocity --benchmark large-batch/

# Then use the recommended worker count
img-velocity large-batch/ output/ --workers 12 --thumbnails
```

### Memory Considerations
- Processing very large images (8K+) can use significant RAM
- Consider processing in smaller batches if you hit memory limits
- The tool automatically handles cleanup, but watch your system resources

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:
- [Pillow](https://pillow.readthedocs.io/) for rock-solid image processing
- Python's multiprocessing for speed
- A lot of coffee and frustration with manual image optimization

---

**Questions? Issues? Want to chat about web performance?** 

Open an issue or start a discussion. I love talking about making the web faster!