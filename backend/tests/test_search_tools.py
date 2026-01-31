import pytest
from unittest.mock import Mock, patch
from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchTool:
    """Tests for CourseSearchTool.execute() method."""

    def test_execute_query_only(self, mock_vector_store):
        """Test execute with query only, no filters."""
        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="What is MCP?")

        # Verify VectorStore.search called with no filters
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name=None,
            lesson_number=None
        )

        # Verify result is a string and contains content
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Model Context Protocol" in result

    def test_execute_with_course_name(self, mock_vector_store):
        """Test execute with course_name filter."""
        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(
            query="What is MCP?",
            course_name="Introduction to Model Context Protocol"
        )

        # Verify course_name passed to VectorStore
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name="Introduction to Model Context Protocol",
            lesson_number=None
        )

        # Verify result formatting includes course title
        assert "Introduction to Model Context Protocol" in result

    def test_execute_with_lesson_number(self, mock_vector_store):
        """Test execute with lesson_number filter."""
        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(
            query="What is MCP?",
            lesson_number=1
        )

        # Verify lesson_number passed to VectorStore
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name=None,
            lesson_number=1
        )

        # Verify result formatting includes lesson number
        assert "Lesson 1" in result

    def test_execute_with_both_filters(self, mock_vector_store):
        """Test execute with both course_name and lesson_number."""
        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(
            query="What is MCP?",
            course_name="Introduction to Model Context Protocol",
            lesson_number=1
        )

        # Verify both filters passed
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name="Introduction to Model Context Protocol",
            lesson_number=1
        )

        # Verify both filters in result
        assert "Introduction to Model Context Protocol" in result
        assert "Lesson 1" in result

    def test_execute_empty_results(self, mock_vector_store, empty_search_results):
        """Test execute with empty search results."""
        mock_vector_store.search.return_value = empty_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="Non-existent topic")

        # Verify "No relevant content found" message
        assert "No relevant content found" in result

    def test_execute_empty_results_with_filters(self, mock_vector_store, empty_search_results):
        """Test execute with empty results and filters shows filter info."""
        mock_vector_store.search.return_value = empty_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(
            query="Non-existent topic",
            course_name="Test Course",
            lesson_number=5
        )

        # Verify filter info in message
        assert "No relevant content found" in result
        assert "Test Course" in result or "lesson 5" in result.lower()

    def test_execute_vector_store_error(self, mock_vector_store, error_search_results):
        """Test execute when VectorStore returns error."""
        mock_vector_store.search.return_value = error_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="What is MCP?")

        # Verify error message returned
        assert "Error" in result or "failed" in result.lower()
        assert "Vector database connection failed" in result

    def test_format_results_with_metadata(self, sample_search_results):
        """Test _format_results method with valid metadata."""
        tool = CourseSearchTool(Mock())
        formatted = tool._format_results(sample_search_results)

        # Verify header format: [Course Title - Lesson N]
        assert "[Introduction to Model Context Protocol - Lesson 1]" in formatted

        # Verify document content included
        assert "Model Context Protocol (MCP) is a protocol" in formatted
        assert "MCP enables secure, controlled access" in formatted

    def test_source_tracking(self, mock_vector_store, sample_search_results):
        """Test that last_sources is populated correctly."""
        tool = CourseSearchTool(mock_vector_store)
        tool.execute(query="What is MCP?")

        # Verify last_sources populated
        assert tool.last_sources is not None
        assert len(tool.last_sources) > 0

        # Verify source structure
        for source in tool.last_sources:
            assert 'text' in source
            assert 'url' in source
            assert isinstance(source['text'], str)
            assert isinstance(source['url'], str)

    def test_lesson_link_retrieval(self, mock_vector_store, sample_search_results):
        """Test that lesson links are retrieved and included in sources."""
        tool = CourseSearchTool(mock_vector_store)
        tool.execute(query="What is MCP?")

        # Verify URLs populated in sources
        assert tool.last_sources is not None
        for source in tool.last_sources:
            # Should have URL from metadata
            assert source['url'] != ''
            assert 'https://example.com/mcp-course/lesson-1' in source['url']

    def test_multiple_results_formatting(self, mock_vector_store):
        """Test formatting with multiple search results."""
        # Create search results with multiple lessons
        multi_results = SearchResults(
            documents=["Content from lesson 1", "Content from lesson 2"],
            metadata=[
                {
                    'course_title': 'Test Course',
                    'lesson_number': 1,
                    'chunk_index': 0,
                    'lesson_link': 'https://example.com/lesson-1'
                },
                {
                    'course_title': 'Test Course',
                    'lesson_number': 2,
                    'chunk_index': 0,
                    'lesson_link': 'https://example.com/lesson-2'
                }
            ],
            distances=[0.2, 0.3],
            error=None
        )

        mock_vector_store.search.return_value = multi_results
        tool = CourseSearchTool(mock_vector_store)
        result = tool.execute(query="Test query")

        # Verify both lessons formatted
        assert "[Test Course - Lesson 1]" in result
        assert "[Test Course - Lesson 2]" in result
        assert "Content from lesson 1" in result
        assert "Content from lesson 2" in result


class TestToolManager:
    """Tests for ToolManager."""

    def test_register_tool(self):
        """Test tool registration."""
        manager = ToolManager()
        tool = CourseSearchTool(Mock())

        manager.register_tool(tool)

        # Verify tool registered
        tools = manager.get_tool_definitions()
        assert len(tools) == 1
        assert tools[0]['name'] == 'search_course_content'

    def test_execute_tool(self, mock_vector_store):
        """Test tool execution through manager."""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        result = manager.execute_tool(
            'search_course_content',
            query="What is MCP?"
        )

        # Verify tool executed
        assert isinstance(result, str)
        mock_vector_store.search.assert_called_once()

    def test_get_last_sources(self, mock_vector_store):
        """Test source retrieval from manager."""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute tool to populate sources
        manager.execute_tool('search_course_content', query="What is MCP?")

        # Get sources
        sources = manager.get_last_sources()
        assert sources is not None
        assert len(sources) > 0

    def test_reset_sources(self, mock_vector_store):
        """Test source reset."""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute tool and get sources
        manager.execute_tool('search_course_content', query="What is MCP?")
        assert manager.get_last_sources() is not None

        # Reset sources
        manager.reset_sources()
        sources = manager.get_last_sources()
        assert sources == [] or sources is None

    def test_multiple_tools_registration(self, mock_vector_store):
        """Test registering multiple tools."""
        manager = ToolManager()
        tool1 = CourseSearchTool(mock_vector_store)

        # Create a second mock tool
        mock_tool2 = Mock()
        mock_tool2.get_tool_definition.return_value = {
            'name': 'test_tool',
            'description': 'Test tool',
            'input_schema': {'type': 'object', 'properties': {}}
        }

        manager.register_tool(tool1)
        manager.register_tool(mock_tool2)

        tools = manager.get_tool_definitions()
        assert len(tools) == 2
        assert any(t['name'] == 'search_course_content' for t in tools)
        assert any(t['name'] == 'test_tool' for t in tools)
