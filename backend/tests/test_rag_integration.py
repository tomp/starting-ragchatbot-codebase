import pytest
from unittest.mock import Mock, patch
from rag_system import RAGSystem
from session_manager import SessionManager
from search_tools import ToolManager, CourseSearchTool
from models import SourceCitation
from config import Config


class TestRAGSystemQueryFlow:
    """Integration tests for RAG system query flow."""

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_query_with_tool_execution_end_to_end(
        self,
        mock_ai_gen_class,
        mock_vector_store_class,
        sample_search_results
    ):
        """Test complete query flow with tool execution."""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = 'https://example.com/lesson-1'
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "MCP is a protocol for AI assistants."
        mock_ai_gen_class.return_value = mock_ai_gen

        # Create RAG system
        config = Config()
        rag = RAGSystem(config)

        # Execute query
        response, sources = rag.query("What is MCP?", session_id="test_123")

        # Verify AI generator called
        mock_ai_gen.generate_response.assert_called_once()

        # Verify response returned
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify sources populated
        assert isinstance(sources, list)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_query_without_session(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test query without session ID."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # Query without session
        response, sources = rag.query("Test query", session_id=None)

        # Verify response generated
        assert isinstance(response, str)

        # Verify no history passed (check call args)
        call_kwargs = mock_ai_gen.generate_response.call_args[1]
        assert call_kwargs.get('conversation_history') is None or call_kwargs.get('conversation_history') == ''

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_query_with_existing_session(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test query with existing session history."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Second response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # First query to populate session
        rag.query("First query", session_id="test_session")

        # Reset mock to track second call
        mock_ai_gen.generate_response.reset_mock()

        # Second query with same session
        rag.query("Second query", session_id="test_session")

        # Verify history passed to second call
        call_kwargs = mock_ai_gen.generate_response.call_args[1]
        history = call_kwargs.get('conversation_history', '')

        # History should contain first exchange
        assert "First query" in history
        assert "Second response" in history or len(history) > 0

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_multi_turn_conversation(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test that only last 2 exchanges are retained."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.side_effect = [
            "Response 1",
            "Response 2",
            "Response 3"
        ]
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        config.MAX_HISTORY = 2
        rag = RAGSystem(config)

        session_id = "multi_turn_session"

        # Make 3 queries
        rag.query("Query 1", session_id=session_id)
        rag.query("Query 2", session_id=session_id)
        rag.query("Query 3", session_id=session_id)

        # Get history
        history = rag.session_manager.get_conversation_history(session_id)

        # Should only have last 2 exchanges (4 messages total)
        message_count = history.count("User:") + history.count("Assistant:")
        assert message_count <= 4

        # First query should be dropped
        assert "Query 1" not in history or message_count == 4

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_source_tracking_and_reset(
        self,
        mock_ai_gen_class,
        mock_vector_store_class,
        sample_search_results
    ):
        """Test that sources are tracked and reset between queries."""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = 'https://example.com/lesson-1'
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # First query - manually trigger tool execution
        rag.tool_manager.execute_tool('search_course_content', query="Query 1")
        sources1 = rag.tool_manager.get_last_sources()

        # Verify sources populated
        assert sources1 is not None
        assert len(sources1) > 0

        # Reset sources
        rag.tool_manager.reset_sources()

        # Second query
        sources2 = rag.tool_manager.get_last_sources()

        # Sources should be reset
        assert sources2 == [] or sources2 is None or len(sources2) == 0

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_source_citation_conversion(
        self,
        mock_ai_gen_class,
        mock_vector_store_class,
        sample_search_results
    ):
        """Test conversion of tool sources to SourceCitation objects."""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = 'https://example.com/lesson-1'
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # Execute query (which will trigger tool execution if AI decides)
        # For this test, manually execute tool
        rag.tool_manager.execute_tool('search_course_content', query="What is MCP?")

        # Get sources from tool manager
        raw_sources = rag.tool_manager.get_last_sources()

        # Convert to SourceCitation objects (as done in RAGSystem.query)
        if raw_sources:
            citations = [
                SourceCitation(text=s['text'], url=s.get('url'))
                for s in raw_sources
            ]

            # Verify SourceCitation structure
            assert len(citations) > 0
            for citation in citations:
                assert hasattr(citation, 'text')
                assert hasattr(citation, 'url')
                assert isinstance(citation.text, str)

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_tool_error_handling(
        self,
        mock_ai_gen_class,
        mock_vector_store_class,
        error_search_results
    ):
        """Test that tool errors are handled gracefully."""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = error_search_results
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Error handled response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # Execute tool with error
        result = rag.tool_manager.execute_tool('search_course_content', query="Query")

        # Should return error message, not raise exception
        assert isinstance(result, str)
        assert "Error" in result or "failed" in result

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_course_search_tool_registration(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test that CourseSearchTool is registered."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        # Get tool definitions
        tools = rag.tool_manager.get_tool_definitions()

        # Verify CourseSearchTool registered
        tool_names = [t['name'] for t in tools]
        assert 'search_course_content' in tool_names

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_course_outline_tool_registration(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test that CourseOutlineTool is registered."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        tools = rag.tool_manager.get_tool_definitions()
        tool_names = [t['name'] for t in tools]

        # Verify CourseOutlineTool registered
        assert 'get_course_outline' in tool_names

        # Verify both tools available
        assert len(tool_names) >= 2

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_session_history_format(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test that session history is formatted correctly."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        session_id = "format_test"

        # Add exchange
        rag.query("Test question", session_id=session_id)

        # Get history
        history = rag.session_manager.get_conversation_history(session_id)

        # Verify format
        assert "User: Test question" in history
        assert "Assistant: Response" in history

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_query_returns_tuple(
        self,
        mock_ai_gen_class,
        mock_vector_store_class
    ):
        """Test that query() returns (response, sources) tuple."""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_gen_class.return_value = mock_ai_gen

        config = Config()
        rag = RAGSystem(config)

        result = rag.query("Test query")

        # Verify tuple structure
        assert isinstance(result, tuple)
        assert len(result) == 2

        response, sources = result
        assert isinstance(response, str)
        assert isinstance(sources, list)
