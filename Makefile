.PHONY: help install test clean lint format

help:
	@echo "Available commands:"
	@echo "  make install    - Install the package in development mode"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code with black and isort"

install:
	pip install -e .
	pip install -e ".[dev]"

test:
	pytest -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

lint:
	flake8 obj2glb tests
	black --check obj2glb tests
	isort --check-only obj2glb tests

format:
	black obj2glb tests
	isort obj2glb tests

