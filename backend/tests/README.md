# Testing Infrastructure

This directory contains the comprehensive test suite for the RAG System.

## Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_api_endpoints.py    # API endpoint tests
├── test_ai_generator.py     # AI generator unit tests
├── test_search_tools.py     # Search tools unit tests
├── test_rag_integration.py  # Integration tests
└── README.md               # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
uv run pytest backend/tests/

# Run with verbose output
uv run pytest backend/tests/ -v

# Run specific test file
uv run pytest backend/tests/test_api_endpoints.py -v

# Run specific test class
uv run pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint -v

# Run specific test
uv run pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint::test_query_with_session_id -v
```

### Using Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only API tests
uv run pytest -m api

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Exclude integration tests
uv run pytest -m "not integration"
```

### Coverage Reports

```bash
# Generate coverage report
uv run pytest backend/tests/ --cov=backend --cov-report=term-missing

# Generate HTML coverage report
uv run pytest backend/tests/ --cov=backend --cov-report=html

# Open HTML report (after generating)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Categories

### 1. API Endpoint Tests (`test_api_endpoints.py`)

Tests for FastAPI REST API endpoints.

**Coverage:**
- POST `/api/query` - Query processing with RAG
- GET `/api/courses` - Course statistics
- GET `/` - Root endpoint
- CORS configuration
- Request validation
- Error handling

**Test Classes:**
- `TestQueryEndpoint` - Query endpoint tests (8 tests)
- `TestCoursesEndpoint` - Courses endpoint tests (5 tests)
- `TestRootEndpoint` - Root endpoint test (1 test)
- `TestCORSHeaders` - CORS middleware tests (3 tests)
- `TestRequestValidation` - Request validation tests (4 tests)
- `TestEndpointIntegration` - Integration workflow tests (2 tests)

**Total: 23 tests**

Example:
```bash
uv run pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint -v
```

### 2. AI Generator Tests (`test_ai_generator.py`)

Tests for Claude API integration and tool calling behavior.

**Coverage:**
- Tool-based RAG flow (two-call pattern)
- Tool execution handling
- Conversation history injection
- API parameter configuration
- Multi-tool execution

**Test Classes:**
- `TestAIGeneratorToolCalling` - Claude API tool calling (9 tests)

**Total: 9 tests**

Example:
```bash
uv run pytest backend/tests/test_ai_generator.py -v
```

### 3. Search Tools Tests (`test_search_tools.py`)

Tests for search tool abstraction and vector store integration.

**Coverage:**
- CourseSearchTool execution with filters
- Result formatting
- Source tracking
- Error handling
- ToolManager registry

**Test Classes:**
- `TestCourseSearchTool` - Search tool tests (11 tests)
- `TestToolManager` - Tool manager tests (5 tests)

**Total: 16 tests**

Example:
```bash
uv run pytest backend/tests/test_search_tools.py::TestCourseSearchTool -v
```

### 4. Integration Tests (`test_rag_integration.py`)

End-to-end tests for the complete RAG system workflow.

**Coverage:**
- Full query processing pipeline
- Session management
- Course loading
- Multi-turn conversations

**Note:** Integration tests may require environment setup (ChromaDB, API keys).

Example:
```bash
uv run pytest backend/tests/test_rag_integration.py -v
```

## Fixtures

### Core Fixtures (from `conftest.py`)

#### Mock Objects
- `mock_vector_store` - Mocked VectorStore with sample search results
- `mock_anthropic_client` - Mocked Anthropic API client
- `mock_anthropic_tool_use_response` - Mock tool_use response
- `mock_anthropic_final_response` - Mock final text response
- `mock_rag_system` - Complete mocked RAG system

#### API Testing
- `test_client` - FastAPI TestClient with mocked dependencies
- `sample_query_request` - Sample query request with session
- `sample_query_request_no_session` - Query request without session
- `sample_source_citations` - List of source citations

#### Data Fixtures
- `sample_course` - Sample Course object
- `sample_course_chunks` - List of CourseChunk objects
- `sample_search_results` - SearchResults with valid data
- `empty_search_results` - Empty SearchResults
- `error_search_results` - SearchResults with error
- `temp_session_id` - Test session ID

## Writing New Tests

### Test Naming Conventions

```python
# Test files: test_*.py
# Test classes: Test*
# Test functions: test_*

class TestMyFeature:
    def test_feature_works_correctly(self):
        """Test that feature behaves as expected."""
        pass

    def test_feature_handles_errors(self):
        """Test error handling in feature."""
        pass
```

### Using Fixtures

```python
def test_with_mock_rag_system(mock_rag_system):
    """Example test using mock RAG system."""
    result = mock_rag_system.query("test query", "session_id")
    assert result is not None
```

### Adding Test Markers

```python
import pytest

@pytest.mark.api
def test_api_endpoint():
    """API endpoint test."""
    pass

@pytest.mark.unit
def test_unit_component():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration_flow():
    """Integration test."""
    pass
```

### Mocking Best Practices

```python
from unittest.mock import Mock, patch

# Mock at the right level
@patch('ai_generator.anthropic.Anthropic')
def test_with_mocked_api(mock_anthropic_class):
    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client
    # ... test code
```

## Test Configuration

Configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",                      # Verbose output
    "--strict-markers",        # Enforce marker registration
    "--tb=short",             # Short traceback format
    "--cov=backend",          # Coverage for backend
    "--cov-report=term-missing",  # Show missing lines
    "--cov-report=html",      # Generate HTML report
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "api: API endpoint tests",
]
```

## Continuous Integration

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
uv run pytest backend/tests/ -v
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install uv
      - run: uv sync
      - run: uv run pytest backend/tests/ -v --cov=backend
```

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running from the project root:

```bash
cd /path/to/project
uv run pytest backend/tests/
```

### Mock Issues

If mocks aren't working, verify the patch path matches the import:

```python
# If code imports: from ai_generator import AIGenerator
# Then patch: @patch('ai_generator.anthropic.Anthropic')
```

### Fixture Not Found

Ensure `conftest.py` is in the `backend/tests/` directory and pytest can discover it.

### Coverage Issues

To exclude specific files from coverage:

```bash
uv run pytest --cov=backend --cov-report=term --cov-config=.coveragerc
```

## Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use descriptive names** - Test names should explain what they test
3. **Test one thing** - Each test should verify a single behavior
4. **Use fixtures** - Reuse setup code via fixtures
5. **Mock external dependencies** - Don't call real APIs or databases in unit tests
6. **Test error cases** - Don't just test the happy path
7. **Keep tests fast** - Unit tests should run in milliseconds
8. **Document complex tests** - Add docstrings explaining what's being tested

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

## Test Statistics

Current test coverage (as of last run):

- **Total Tests:** 48 passing
- **API Tests:** 23 tests (100% pass rate)
- **AI Generator Tests:** 9 tests (100% pass rate)
- **Search Tools Tests:** 16 tests (100% pass rate)
- **Overall Coverage:** 57% of backend code
- **Test Execution Time:** ~1.5 seconds

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add tests for new functionality
4. Aim for >80% code coverage
5. Update this README if adding new test categories
