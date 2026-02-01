#!/bin/bash
# Script to format Python code using Black and isort

set -e

echo "Running isort..."
uv run isort backend/ main.py

echo "Running black..."
uv run black backend/ main.py

echo "✓ Code formatting complete!"
