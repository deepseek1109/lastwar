.PHONY: help clean install dev test lint format

help:
	@echo "Available targets:"
	@echo "  make install       - Install dependencies from pyproject.toml using uv"
	@echo "  make clean         - Remove .venv, __pycache__, .pyc files"
	@echo "  make dev           - Install with dev dependencies"
	@echo "  make test          - Run tests"

install:
	@echo "Installing dependencies using uv..."
	uv sync

clean:
	@echo "Cleaning up..."
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "Clean complete"

dev: install
	@echo "Dev environment ready"

test:
	@echo "Running tests..."
	python -m pytest tests/ -v
