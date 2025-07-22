# img-velocity

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
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

## ✨ What It Does

- **🚀 Parallel Processing**: Uses all your CPU cores to process images blazingly fast
- **🎯 Smart Compression**: Automatically adjusts WebP quality based on image size
- **📱 Responsive Ready**: Generates the exact sizes you need for responsive design
- **🔧 Override Everything**: Don't like the defaults? Override aspect ratios and resolutions
- **📊 Progress Tracking**: See exactly how fast your images are processing
- **🧪 Performance Tuning**: Built-in benchmarking finds the optimal worker count
- **📝 Web Integration**: Generates a manifest.json for easy web framework integration

## 🚀 Quick Start

### Install

```bash
# From source (recommended for now)
git clone https://github.com/supergenlabs/img-velocity.git
cd img-velocity
pip install -e .

# Or grab the latest release binary
# (Linux/macOS/Windows binaries coming soon)
```

### Basic Usage

```bash
# Convert all images in a directory
img-velocity input/ output/

# Include thumbnails for lazy loading
img-velocity input/ output/ --thumbnails

# Use all your CPU cores
img-velocity input/ output/ --workers 8
```

That's it. Point it at a folder of images, and it'll organize everything by aspect ratio and generate multiple WebP sizes for each.

## 📖 How I Use It

Here's my typical workflow when building web apps:

### 1. Process Your Images

```bash
# I usually process everything with thumbnails
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

### 3. Implement Responsive Images

Here's how I use the generated images in my web apps:

#### React/Next.js Example

```jsx
import manifest from '/public/images/manifest.json';

function ResponsiveImage({ imageName, alt, className }) {
  const imageData = manifest.images[imageName];
  const variants = imageData.variants.filter(v => v.type === 'standard');
  
  // Get the largest variant as fallback
  const fallback = variants.reduce((largest, current) => 
    current.width > largest.width ? current : largest
  );

  return (
    <picture className={className}>
      {/* Mobile */}
      <source 
        media="(max-width: 768px)" 
        srcSet={`/images/${variants.find(v => v.width <= 768)?.path}`} 
      />
      {/* Tablet */}
      <source 
        media="(max-width: 1200px)" 
        srcSet={`/images/${variants.find(v => v.width <= 1200)?.path}`} 
      />
      {/* Desktop */}
      <img 
        src={`/images/${fallback.path}`} 
        alt={alt}
        loading="lazy"
      />
    </picture>
  );
}

// Usage
<ResponsiveImage 
  imageName="hero-image.jpg" 
  alt="Beautiful hero image" 
  className="w-full h-64 object-cover"
/>
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

## 🎛️ Advanced Usage

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
img-velocity input/ output/ --benchmark
```

This will test 1, 2, 4, 8+ workers and tell you which gives the best performance on your system.

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

## 🏗️ Understanding the Output

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

## ⚙️ Customizing the Configuration

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

## 🏗️ Project Architecture

```
img-velocity/
├── img_velocity/
│   ├── __init__.py              # Package exports
│   ├── main.py                  # CLI entry point
│   ├── cli/
│   │   └── parser.py            # Command line argument parsing
│   ├── core/                    # Core processing logic
│   │   ├── config.py            # Aspect ratios and output sizes
│   │   ├── validator.py         # Image validation and requirements
│   │   ├── processor.py         # Image processing and WebP conversion
│   │   └── batch.py             # Parallel processing orchestration
│   └── utils/                   # Utilities
│       ├── progress.py          # Progress tracking
│       ├── filesystem.py        # Manifest generation
│       └── helpers.py           # General utilities
├── tests/                       # Comprehensive test suite
└── pyproject.toml              # Project configuration
```

### Key Components

- **`Configuration`**: Manages aspect ratios, minimum requirements, and output sizes
- **`ImageValidator`**: Checks if images meet requirements and handles overrides
- **`ImageProcessor`**: Core image processing with smart sharpening and WebP conversion
- **`BatchProcessor`**: Orchestrates parallel processing and progress tracking
- **`ProgressTracker`**: Real-time progress bars with ETA calculations

## 🤝 Contributing

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
pip install -r requirements-test.txt
```

### Code Quality Standards

I'm pretty particular about code quality. Here's what I expect:

```bash
# Format your code
make format  # or: black img_velocity/ tests/ && isort img_velocity/ tests/

# Lint everything
make lint    # or: flake8 img_velocity/ tests/ && mypy img_velocity/

# Run security checks
make security  # or: bandit -r img_velocity/ && safety check

# Before you commit
make pre-commit  # Runs format, lint, and fast tests
```

### Testing Requirements

**This is non-negotiable: minimum 90% test coverage.** I've built a comprehensive test suite, and I expect contributions to maintain this standard.

```bash
# Run all tests with coverage
make test  # or: pytest --cov=img_velocity --cov-fail-under=90

# Run specific test types
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-performance  # Performance benchmarks

# Fast tests during development
make test-fast  # Skip slow tests
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

### Areas Where I'd Love Help

- **Format Support**: AVIF, JPEG XL support
- **Performance**: Further optimization of the processing pipeline
- **Platform Support**: Better Windows compatibility testing
- **Web Integration**: Framework-specific helper libraries
- **Documentation**: More real-world usage examples

## 🎯 Performance Tips

### Optimal Worker Counts
- **CPU-bound systems**: Start with `--workers 4-8`
- **High-core systems**: Try `--workers 16` or run `--benchmark`
- **I/O-bound systems**: Often benefit from more workers than CPU cores

### Processing Large Batches
```bash
# For 100+ images, use benchmarking to find optimal settings
img-velocity large-batch/ output/ --benchmark --thumbnails

# Then use the recommended worker count
img-velocity large-batch/ output/ --workers 12 --thumbnails
```

### Memory Considerations
- Processing very large images (8K+) can use significant RAM
- Consider processing in smaller batches if you hit memory limits
- The tool automatically handles cleanup, but watch your system resources

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [Pillow](https://pillow.readthedocs.io/) for rock-solid image processing
- Python's multiprocessing for speed
- A lot of coffee and frustration with manual image optimization

---

**Questions? Issues? Want to chat about web performance?** 

Open an issue or start a discussion. I love talking about making the web faster! 🚀