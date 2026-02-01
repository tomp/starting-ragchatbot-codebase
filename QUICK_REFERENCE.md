# Code Quality Quick Reference

## Daily Development Commands

### Format Code (Run Often!)
```bash
./scripts/format.sh
```
Automatically formats your code with Black and organizes imports with isort.

### Check Code Quality
```bash
./scripts/lint.sh
```
Runs Flake8 and mypy to check for issues without changing files.

### Full Quality Check (Before Committing)
```bash
./scripts/quality-check.sh
```
Runs formatting checks, linting, and all tests with coverage.

## What Each Tool Does

| Tool | Purpose | When It Runs |
|------|---------|--------------|
| **Black** | Code formatter | `format.sh`, `quality-check.sh` |
| **isort** | Import organizer | `format.sh`, `quality-check.sh` |
| **Flake8** | Style checker | `lint.sh`, `quality-check.sh` |
| **mypy** | Type checker | `lint.sh`, `quality-check.sh` |
| **pytest** | Test runner | `quality-check.sh` |

## Recommended Workflow

1. **Write code** as normal
2. **Run format.sh** periodically to keep code clean
3. **Before committing**, run `quality-check.sh`
4. **Fix any issues** reported
5. **Commit** your changes

## Common Issues

### Script Permission Denied
```bash
chmod +x scripts/*.sh
```

### Line Ending Issues (Windows)
```bash
sed -i 's/\r$//' scripts/*.sh
```

### Tools Not Found
```bash
uv sync  # Reinstall dependencies
```

## More Information

See [CODE_QUALITY.md](CODE_QUALITY.md) for complete documentation.
