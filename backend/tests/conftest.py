import pytest
from unittest.mock import Mock
from typing import List, Dict, Any
from vector_store import SearchResults
from models import Course, CourseChunk, SourceCitation


@pytest.fixture
def sample_course_metadata() -> Dict[str, Any]:
    """Sample course metadata for testing."""
    return {
        'course_title': 'Introduction to Model Context Protocol',
        'course_link': 'https://example.com/mcp-course',
        'course_instructor': 'Jane Doe',
        'lesson_number': 1,
        'lesson_title': 'Getting Started with MCP',
        'lesson_link': 'https://example.com/mcp-course/lesson-1'
    }


@pytest.fixture
def sample_search_results() -> SearchResults:
    """Sample search results with valid data."""
    return SearchResults(
        documents=[
            "Model Context Protocol (MCP) is a protocol for connecting AI assistants to external data sources.",
            "MCP enables secure, controlled access to databases and APIs."
        ],
        metadata=[
            {
                'course_title': 'Introduction to Model Context Protocol',
                'lesson_number': 1,
                'chunk_index': 0,
                'lesson_link': 'https://example.com/mcp-course/lesson-1'
            },
            {
                'course_title': 'Introduction to Model Context Protocol',
                'lesson_number': 1,
                'chunk_index': 1,
                'lesson_link': 'https://example.com/mcp-course/lesson-1'
            }
        ],
        distances=[0.3, 0.4],
        error=None
    )


@pytest.fixture
def empty_search_results() -> SearchResults:
    """Empty search results for testing no-match scenarios (no error, just no matches)."""
    return SearchResults(
        documents=[],
        metadata=[],
        distances=[],
        error=None
    )


@pytest.fixture
def error_search_results() -> SearchResults:
    """Search results with error for testing error handling."""
    return SearchResults(
        documents=[],
        metadata=[],
        distances=[],
        error="Vector database connection failed"
    )


@pytest.fixture
def mock_vector_store(sample_search_results: SearchResults) -> Mock:
    """Mock VectorStore that returns sample search results by default."""
    mock = Mock()
    mock.search.return_value = sample_search_results
    mock.get_lesson_link.return_value = 'https://example.com/mcp-course/lesson-1'
    return mock


@pytest.fixture
def mock_anthropic_client() -> Mock:
    """Mock Anthropic API client."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [
        Mock(type='text', text='This is a response from Claude.')
    ]
    mock_response.stop_reason = 'end_turn'
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_anthropic_tool_use_response() -> Mock:
    """Mock Anthropic API response with tool use."""
    # Create tool use block with proper attributes
    tool_use_block = Mock()
    tool_use_block.type = 'tool_use'
    tool_use_block.id = 'toolu_123'
    tool_use_block.name = 'search_course_content'
    tool_use_block.input = {'query': 'What is MCP?'}

    mock_response = Mock()
    mock_response.content = [tool_use_block]
    mock_response.stop_reason = 'tool_use'
    return mock_response


@pytest.fixture
def mock_anthropic_final_response() -> Mock:
    """Mock Anthropic API final response after tool execution."""
    # Create text block with proper attributes
    text_block = Mock()
    text_block.type = 'text'
    text_block.text = 'MCP is a protocol for connecting AI assistants to external data sources.'

    mock_response = Mock()
    mock_response.content = [text_block]
    mock_response.stop_reason = 'end_turn'
    return mock_response


@pytest.fixture
def temp_session_id() -> str:
    """Generate a test session ID."""
    return "test_session_123"


@pytest.fixture
def sample_course() -> Course:
    """Sample course object for testing."""
    return Course(
        title="Introduction to Model Context Protocol",
        course_link="https://example.com/mcp-course",
        instructor="Jane Doe"
    )


@pytest.fixture
def sample_course_chunks(sample_course: Course) -> List[CourseChunk]:
    """Sample course chunks for testing."""
    return [
        CourseChunk(
            content="Model Context Protocol (MCP) is a protocol for connecting AI assistants.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="MCP enables secure, controlled access to databases and APIs.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=1
        )
    ]
