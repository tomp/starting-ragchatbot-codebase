#!/bin/bash
# Script to run all code quality checks (format check, lint, tests)

set -e

echo "=== Code Quality Check ==="
echo ""

echo "Step 1: Checking code formatting..."
echo "Running isort (check only)..."
uv run isort --check-only backend/ main.py

echo "Running black (check only)..."
uv run black --check backend/ main.py

echo ""
echo "Step 2: Running linters..."
echo "Running flake8..."
uv run flake8 backend/ main.py

echo "Running mypy..."
uv run mypy backend/ main.py

echo ""
echo "Step 3: Running tests..."
cd backend && uv run pytest tests/ --cov=. --cov-report=term-missing

echo ""
echo "=== ✓ All quality checks passed! ==="
