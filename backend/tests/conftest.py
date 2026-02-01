import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from fastapi.testclient import TestClient
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


# API Testing Fixtures

@pytest.fixture
def mock_rag_system() -> Mock:
    """Mock RAGSystem for API testing."""
    mock = Mock()

    # Mock query method
    mock.query.return_value = (
        "MCP is a protocol for connecting AI assistants to external data sources.",
        [
            SourceCitation(
                text="Introduction to Model Context Protocol - Lesson 1",
                url="https://example.com/mcp-course/lesson-1"
            )
        ]
    )

    # Mock session_manager
    mock.session_manager = Mock()
    mock.session_manager.create_session.return_value = "test_session_123"

    # Mock get_course_analytics
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": [
            "Introduction to Model Context Protocol",
            "Advanced MCP Techniques"
        ]
    }

    # Mock add_course_folder
    mock.add_course_folder.return_value = (2, 50)

    return mock


@pytest.fixture
def test_client(mock_rag_system) -> TestClient:
    """Create a TestClient with mocked RAG system to avoid static file mounting issues."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional

    # Create a test app without static file mounting
    app = FastAPI(title="Course Materials RAG System - Test")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Define request/response models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[SourceCitation]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    # Define API endpoints
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()

            answer, sources = mock_rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}

    return TestClient(app)


@pytest.fixture
def sample_query_request() -> Dict[str, Any]:
    """Sample query request payload."""
    return {
        "query": "What is MCP?",
        "session_id": "test_session_123"
    }


@pytest.fixture
def sample_query_request_no_session() -> Dict[str, Any]:
    """Sample query request without session_id."""
    return {
        "query": "What is MCP?"
    }


@pytest.fixture
def sample_source_citations() -> List[SourceCitation]:
    """Sample source citations for testing."""
    return [
        SourceCitation(
            text="Introduction to Model Context Protocol - Lesson 1",
            url="https://example.com/mcp-course/lesson-1"
        ),
        SourceCitation(
            text="Introduction to Model Context Protocol - Lesson 2",
            url="https://example.com/mcp-course/lesson-2"
        )
    ]
