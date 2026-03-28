.PHONY: help clean install dev test lint format publish

help:
	@echo "Available targets:"
	@echo "  make install       - Install dependencies from pyproject.toml using uv"
	@echo "  make clean         - Remove .venv, __pycache__, .pyc files"
	@echo "  make dev           - Install with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make publish       - Regenerate docs/synz.md from data/synz2.csv"

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

publish:
	@echo "Regenerating docs/synz.md..."
	python tests/feat.py 2>/dev/null | grep -v "^$$" | grep -A 200 "Top 100 Players Ranked" | head -60
