#!/bin/bash
# Script to run linting checks on Python code

set -e

echo "Running flake8..."
uv run flake8 backend/ main.py

echo "Running mypy..."
uv run mypy backend/ main.py

echo "✓ All linting checks passed!"
