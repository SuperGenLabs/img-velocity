# Development convenience targets for img-velocity
# This is NOT required to use the package - just helpful for development

.PHONY: help install install-dev test test-unit test-integration test-performance lint format type-check security clean build

# Default target
help:
	@echo "Development convenience targets:"
	@echo ""
	@echo "Installation:"
	@echo "  install          Install package in development mode"
	@echo "  install-dev      Install with test dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests with coverage"
	@echo "  test-fast        Run quick tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  format           Format code with black and ruff"
	@echo "  lint             Run linting and type checks"
	@echo "  security         Run security scans"
	@echo ""
	@echo "Build & Clean:"
	@echo "  build            Build distribution packages"
	@echo "  clean            Clean build artifacts and cache"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[test]

# Testing targets
test:
	pytest --cov=img_velocity --cov-report=term-missing --cov-report=html --cov-fail-under=80

test-fast:
	pytest -x -q --tb=short

# Code quality targets
format:
	black img_velocity/
	ruff format img_velocity/

lint:
	ruff check img_velocity/
	mypy img_velocity/ --ignore-missing-imports

format-check:
	black --check img_velocity/
	ruff check img_velocity/

type-check:
	mypy img_velocity/

security:
	bandit -r img_velocity/ -ll

# Development workflow targets
pre-commit: format lint test-fast
	@echo "Pre-commit checks passed!"

ci: format-check lint test
	@echo "CI pipeline passed!"

# Build and distribution targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

build-dev: clean
	python -m build --wheel

# Utility targets
test-install:
	@echo "Testing package installation..."
	pip uninstall -y img-velocity 2>/dev/null || true
	pip install .
	img-velocity --help
	@echo "Package installation successful!"