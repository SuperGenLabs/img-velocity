# Makefile for img-velocity development

.PHONY: help install install-dev test test-unit test-integration test-performance lint format type-check security clean build docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install          Install package in development mode"
	@echo "  install-dev      Install with all development dependencies"
	@echo "  test             Run all tests with coverage"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests"
	@echo "  lint             Run all linting tools"
	@echo "  format           Format code with Black and isort"
	@echo "  type-check       Run mypy type checking"
	@echo "  security         Run security scans"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  build            Build distribution packages"
	@echo "  docs             Generate documentation"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .
	pip install -r requirements-test.txt

# Testing targets
test:
	pytest --cov=img_velocity --cov-report=term-missing --cov-report=html --cov-fail-under=80

test-unit:
	pytest -m "unit or not integration" -v

test-integration:
	pytest -m integration -v

test-performance:
	pytest -m performance -v --benchmark-only

test-fast:
	pytest -m "not slow" -x -q

test-parallel:
	pytest -n auto

# Code quality targets
lint: flake8 mypy bandit

flake8:
	flake8 img_velocity/ tests/

mypy:
	mypy img_velocity/

bandit:
	bandit -r img_velocity/ -ll

format:
	black img_velocity/ tests/
	isort img_velocity/ tests/

format-check:
	black --check img_velocity/ tests/
	isort --check-only img_velocity/ tests/

type-check:
	mypy img_velocity/

security:
	bandit -r img_velocity/
	safety check

# Development workflow targets
pre-commit: format lint test-fast
	@echo "✅ Pre-commit checks passed!"

ci: format-check lint test
	@echo "✅ CI pipeline passed!"

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

# Documentation targets
docs:
	@echo "Documentation generation not yet implemented"

# Benchmarking and profiling
benchmark:
	python -m img_velocity benchmark tests/fixtures/sample_images/ /tmp/benchmark_output/

profile:
	python -m cProfile -o profile_output.prof -m img_velocity tests/fixtures/sample_images/ /tmp/profile_output/

# Release targets
version-patch:
	bump2version patch

version-minor:
	bump2version minor

version-major:
	bump2version major

# Docker targets (if you add Docker support later)
docker-build:
	docker build -t img-velocity .

docker-test:
	docker run --rm img-velocity pytest

# Utility targets
deps-update:
	pip list --outdated
	@echo "Run 'pip install --upgrade <package>' to update specific packages"

deps-tree:
	pipdeptree

check-deps:
	safety check
	pip-audit