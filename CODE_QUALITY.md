# Code Quality Tools

This project uses several code quality tools to maintain consistent code formatting and catch potential issues.

## Tools Included

### 1. Black - Code Formatter
**Black** is an opinionated Python code formatter that ensures consistent code style across the project.

- **Configuration**: See `[tool.black]` in `pyproject.toml`
- **Line Length**: 88 characters (Black's default)
- **Target Python Version**: 3.13

### 2. isort - Import Organizer
**isort** automatically organizes and formats Python imports.

- **Configuration**: See `[tool.isort]` in `pyproject.toml`
- **Profile**: Black-compatible (ensures isort and Black work together)

### 3. Flake8 - Style Guide Enforcer
**Flake8** checks Python code against coding style (PEP 8) and programming errors.

- **Configuration**: See `.flake8` file
- **Max Line Length**: 88 characters (matching Black)
- **Ignored Codes**: E203, E501, W503, E402, F401, F811, F841

### 4. mypy - Static Type Checker
**mypy** performs static type checking to catch type-related errors.

- **Configuration**: See `[tool.mypy]` in `pyproject.toml`
- **Mode**: Relaxed (focused on catching major issues, not enforcing strict typing)

## Quick Start Scripts

Three convenience scripts are provided in the `scripts/` directory:

### Format Code
Automatically format all Python code:
```bash
./scripts/format.sh
```

This runs:
- `isort` - Organizes imports
- `black` - Formats code

### Run Linting
Check code quality without making changes:
```bash
./scripts/lint.sh
```

This runs:
- `flake8` - Style checks
- `mypy` - Type checks

### Full Quality Check
Run all checks including tests:
```bash
./scripts/quality-check.sh
```

This runs:
- Format checks (isort, black in check-only mode)
- Linting (flake8, mypy)
- Tests with coverage (pytest)

## Manual Usage

You can also run tools individually using `uv`:

### Black
```bash
# Format code
uv run black backend/ main.py

# Check formatting (without changing files)
uv run black --check backend/ main.py

# Show what would change
uv run black --diff backend/ main.py
```

### isort
```bash
# Organize imports
uv run isort backend/ main.py

# Check only (without changing files)
uv run isort --check-only backend/ main.py

# Show diff
uv run isort --diff backend/ main.py
```

### Flake8
```bash
# Run linter
uv run flake8 backend/ main.py

# Show statistics
uv run flake8 --statistics backend/ main.py
```

### mypy
```bash
# Run type checker
uv run mypy backend/ main.py

# Show error codes
uv run mypy --show-error-codes backend/ main.py
```

## Pre-commit Workflow (Recommended)

Before committing code:

1. **Format your code**:
   ```bash
   ./scripts/format.sh
   ```

2. **Run quality checks**:
   ```bash
   ./scripts/quality-check.sh
   ```

3. **Fix any issues** reported by the tools

4. **Commit your changes**

## CI/CD Integration

To integrate these tools into a CI/CD pipeline, add the quality check script to your workflow:

```yaml
# Example GitHub Actions workflow
- name: Run code quality checks
  run: ./scripts/quality-check.sh
```

## Configuration Files

- **pyproject.toml**: Contains configuration for Black, isort, and mypy
- **.flake8**: Contains configuration for Flake8
- **scripts/**: Contains convenience scripts for running quality tools

## Excluded Directories

The following directories are excluded from quality checks:
- `.venv/` - Virtual environment
- `chroma_db/` - Vector database storage
- `.git/` - Git metadata
- `__pycache__/` - Python cache files
- `.mypy_cache/` - mypy cache
- `.pytest_cache/` - pytest cache

## Tips

- **Run format.sh frequently**: Format your code as you work to avoid large diffs
- **Fix issues incrementally**: Don't let linting issues accumulate
- **Use IDE integration**: Many IDEs support these tools natively for real-time feedback
- **Customize as needed**: All configurations can be adjusted in `pyproject.toml` and `.flake8`

## Troubleshooting

### "Command not found" errors
Make sure you've installed dev dependencies:
```bash
uv sync
```

### Scripts have wrong line endings
If scripts fail with "bad interpreter", fix line endings:
```bash
sed -i 's/\r$//' scripts/*.sh
```

### Need to ignore specific lines
Use inline comments to ignore specific issues:
```python
# For Flake8
result = some_long_function()  # noqa: E501

# For mypy
result = some_function()  # type: ignore
```
