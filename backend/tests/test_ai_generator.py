import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool


class TestAIGeneratorToolCalling:
    """Tests for AIGenerator tool calling behavior."""

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tool_use(
        self,
        mock_anthropic_class,
        mock_anthropic_tool_use_response,
        mock_anthropic_final_response
    ):
        """Test that tool execution is triggered when Claude returns tool_use."""
        # Setup mock client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # First call returns tool_use, second call returns final response
        mock_client.messages.create.side_effect = [
            mock_anthropic_tool_use_response,
            mock_anthropic_final_response
        ]

        # Create tool manager with mock tool
        tool_manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {
            'name': 'search_course_content',
            'description': 'Search course content',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'}
                },
                'required': ['query']
            }
        }
        mock_tool.execute.return_value = "Mocked search results"
        tool_manager.register_tool(mock_tool)

        # Create AI generator
        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        response = ai_gen.generate_response(
            "What is MCP?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        # Verify tool executed
        mock_tool.execute.assert_called_once()

        # Verify two API calls made
        assert mock_client.messages.create.call_count == 2

        # Verify first call included tools
        first_call_kwargs = mock_client.messages.create.call_args_list[0][1]
        assert 'tools' in first_call_kwargs
        assert len(first_call_kwargs['tools']) > 0

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_no_tool_use(
        self,
        mock_anthropic_class,
        mock_anthropic_final_response
    ):
        """Test direct response when Claude doesn't use tools."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_anthropic_final_response

        tool_manager = ToolManager()
        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        response = ai_gen.generate_response(
            "Hello",
            tool_manager=tool_manager
        )

        # Verify only one API call
        assert mock_client.messages.create.call_count == 1

        # Verify response returned
        assert isinstance(response, str)
        assert len(response) > 0

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_flow(
        self,
        mock_anthropic_class,
        mock_anthropic_tool_use_response,
        mock_anthropic_final_response
    ):
        """Test the two-call flow with tool execution."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            mock_anthropic_tool_use_response,
            mock_anthropic_final_response
        ]

        # Setup tool manager
        tool_manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {
            'name': 'search_course_content',
            'description': 'Search',
            'input_schema': {'type': 'object', 'properties': {}}
        }
        mock_tool.execute.return_value = "Tool result content"
        tool_manager.register_tool(mock_tool)

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        response = ai_gen.generate_response(
            "Test query",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        # Verify second API call structure
        second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
        messages = second_call_kwargs['messages']

        # Should have: user message, assistant tool_use, user tool_result
        assert len(messages) >= 2
        assert messages[0]['role'] == 'user'

        # Find assistant message with tool_use
        assistant_msg = next(m for m in messages if m['role'] == 'assistant')
        assert assistant_msg is not None

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_result_message_format(
        self,
        mock_anthropic_class,
        mock_anthropic_tool_use_response,
        mock_anthropic_final_response
    ):
        """Test that tool_result message has correct structure."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            mock_anthropic_tool_use_response,
            mock_anthropic_final_response
        ]

        tool_manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {
            'name': 'search_course_content',
            'description': 'Search',
            'input_schema': {'type': 'object', 'properties': {}}
        }
        mock_tool.execute.return_value = "Tool result"
        tool_manager.register_tool(mock_tool)

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        ai_gen.generate_response(
            "Query",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        # Check second call for tool_result structure
        second_call = mock_client.messages.create.call_args_list[1][1]
        messages = second_call['messages']

        # Find tool_result in user message
        user_messages = [m for m in messages if m['role'] == 'user']
        assert len(user_messages) >= 1

    @patch('ai_generator.anthropic.Anthropic')
    def test_multiple_tool_calls_in_response(
        self,
        mock_anthropic_class,
        mock_anthropic_final_response
    ):
        """Test handling multiple tool_use blocks in one response."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create response with multiple tool uses
        tool_use_1 = Mock()
        tool_use_1.type = 'tool_use'
        tool_use_1.id = 'tool1'
        tool_use_1.name = 'search_course_content'
        tool_use_1.input = {'query': 'q1'}

        tool_use_2 = Mock()
        tool_use_2.type = 'tool_use'
        tool_use_2.id = 'tool2'
        tool_use_2.name = 'search_course_content'
        tool_use_2.input = {'query': 'q2'}

        multi_tool_response = Mock()
        multi_tool_response.content = [tool_use_1, tool_use_2]
        multi_tool_response.stop_reason = 'tool_use'

        mock_client.messages.create.side_effect = [
            multi_tool_response,
            mock_anthropic_final_response
        ]

        tool_manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {
            'name': 'search_course_content',
            'description': 'Search',
            'input_schema': {'type': 'object', 'properties': {}}
        }
        mock_tool.execute.return_value = "Result"
        tool_manager.register_tool(mock_tool)

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        ai_gen.generate_response(
            "Query",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        # Both tools should be executed
        assert mock_tool.execute.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_conversation_history_injection(
        self,
        mock_anthropic_class,
        mock_anthropic_final_response
    ):
        """Test that conversation history is injected into system prompt."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_anthropic_final_response

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        conversation_history = "User: Previous question\nAssistant: Previous answer"

        ai_gen.generate_response(
            "New question",
            conversation_history=conversation_history
        )

        # Check that system prompt includes history
        call_kwargs = mock_client.messages.create.call_args[1]
        system_prompt = call_kwargs['system']

        assert "Previous conversation:" in system_prompt
        assert "Previous question" in system_prompt
        assert "Previous answer" in system_prompt

    @patch('ai_generator.anthropic.Anthropic')
    def test_tools_parameter_passed_correctly(
        self,
        mock_anthropic_class,
        mock_anthropic_tool_use_response,
        mock_anthropic_final_response
    ):
        """Test that tools are passed to first call but not second."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            mock_anthropic_tool_use_response,
            mock_anthropic_final_response
        ]

        tool_manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {
            'name': 'search_course_content',
            'description': 'Search',
            'input_schema': {'type': 'object', 'properties': {}}
        }
        mock_tool.execute.return_value = "Result"
        tool_manager.register_tool(mock_tool)

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        ai_gen.generate_response(
            "Query",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )

        # First call should have tools
        first_call = mock_client.messages.create.call_args_list[0][1]
        assert 'tools' in first_call
        assert first_call['tool_choice'] == {"type": "auto"}

        # Second call should NOT have tools
        second_call = mock_client.messages.create.call_args_list[1][1]
        assert 'tools' not in second_call
        assert 'tool_choice' not in second_call

    @patch('ai_generator.anthropic.Anthropic')
    def test_api_call_parameters(
        self,
        mock_anthropic_class,
        mock_anthropic_final_response
    ):
        """Test that API calls use correct base parameters."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_anthropic_final_response

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        ai_gen.generate_response("Test query")

        call_kwargs = mock_client.messages.create.call_args[1]

        # Verify base parameters
        assert call_kwargs['model'] == "claude-sonnet-4-20250514"
        assert call_kwargs['temperature'] == 0
        assert call_kwargs['max_tokens'] == 800

        # Verify messages format
        messages = call_kwargs['messages']
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Test query'

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_tools(
        self,
        mock_anthropic_class,
        mock_anthropic_final_response
    ):
        """Test generate_response when no tool_manager provided."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_anthropic_final_response

        ai_gen = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")
        response = ai_gen.generate_response("Test query")

        # Should not include tools parameter
        call_kwargs = mock_client.messages.create.call_args[1]
        assert 'tools' not in call_kwargs
        assert 'tool_choice' not in call_kwargs

        # Should still return response
        assert isinstance(response, str)
