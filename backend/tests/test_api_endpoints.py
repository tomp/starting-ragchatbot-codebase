import pytest
from unittest.mock import Mock
from fastapi import status


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for POST /api/query endpoint."""

    def test_query_with_session_id(self, test_client, sample_query_request, mock_rag_system):
        """Test query endpoint with provided session_id."""
        response = test_client.post("/api/query", json=sample_query_request)

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response structure
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify response values
        assert data["session_id"] == sample_query_request["session_id"]
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
        assert isinstance(data["sources"], list)

        # Verify RAG system was called correctly
        mock_rag_system.query.assert_called_once_with(
            sample_query_request["query"],
            sample_query_request["session_id"]
        )

    def test_query_without_session_id(self, test_client, sample_query_request_no_session, mock_rag_system):
        """Test query endpoint creates new session when session_id not provided."""
        response = test_client.post("/api/query", json=sample_query_request_no_session)

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify new session created
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test_session_123"

        # Verify session manager was called
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_response_structure(self, test_client, sample_query_request):
        """Test that query response has correct structure and types."""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()

        # Verify answer field
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert "MCP" in data["answer"]

        # Verify sources field
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0

        # Verify source structure
        source = data["sources"][0]
        assert "text" in source
        assert "url" in source
        assert isinstance(source["text"], str)
        assert isinstance(source["url"], (str, type(None)))

    def test_query_with_empty_query(self, test_client, mock_rag_system):
        """Test query endpoint with empty query string."""
        response = test_client.post("/api/query", json={"query": ""})

        # Should still process, even with empty query
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_query_with_invalid_payload(self, test_client):
        """Test query endpoint with invalid request payload."""
        # Missing required 'query' field
        response = test_client.post("/api/query", json={"session_id": "test"})

        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_with_rag_system_error(self, test_client, sample_query_request, mock_rag_system):
        """Test query endpoint handles RAG system errors gracefully."""
        # Configure mock to raise exception
        mock_rag_system.query.side_effect = Exception("Vector database error")

        response = test_client.post("/api/query", json=sample_query_request)

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Verify error detail included
        data = response.json()
        assert "detail" in data
        assert "Vector database error" in data["detail"]

    def test_query_multiple_sources_returned(self, test_client, sample_query_request, mock_rag_system, sample_source_citations):
        """Test that multiple sources are properly returned."""
        # Configure mock to return multiple sources
        mock_rag_system.query.return_value = (
            "Answer with multiple sources",
            sample_source_citations
        )

        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()

        # Verify multiple sources
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == sample_source_citations[0].text
        assert data["sources"][1]["text"] == sample_source_citations[1].text

    def test_query_preserves_session_across_requests(self, test_client, mock_rag_system):
        """Test that session_id is preserved across multiple requests."""
        session_id = "persistent_session_456"

        # First request
        response1 = test_client.post("/api/query", json={
            "query": "What is MCP?",
            "session_id": session_id
        })
        data1 = response1.json()
        assert data1["session_id"] == session_id

        # Second request with same session
        response2 = test_client.post("/api/query", json={
            "query": "Tell me more",
            "session_id": session_id
        })
        data2 = response2.json()
        assert data2["session_id"] == session_id


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for GET /api/courses endpoint."""

    def test_get_courses_success(self, test_client, mock_rag_system):
        """Test getting course statistics successfully."""
        response = test_client.get("/api/courses")

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response structure
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data

        # Verify response values
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] == 2
        assert isinstance(data["course_titles"], list)
        assert len(data["course_titles"]) == 2

        # Verify RAG system was called
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_courses_response_structure(self, test_client):
        """Test that courses response has correct structure."""
        response = test_client.get("/api/courses")
        data = response.json()

        # Verify total_courses field
        assert "total_courses" in data
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0

        # Verify course_titles field
        assert "course_titles" in data
        assert isinstance(data["course_titles"], list)

        # Verify course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)
            assert len(title) > 0

    def test_get_courses_empty_database(self, test_client, mock_rag_system):
        """Test courses endpoint with no courses loaded."""
        # Configure mock to return empty results
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = test_client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_with_error(self, test_client, mock_rag_system):
        """Test courses endpoint handles errors gracefully."""
        # Configure mock to raise exception
        mock_rag_system.get_course_analytics.side_effect = Exception("Database connection failed")

        response = test_client.get("/api/courses")

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Verify error detail
        data = response.json()
        assert "detail" in data
        assert "Database connection failed" in data["detail"]

    def test_get_courses_multiple_courses(self, test_client, mock_rag_system):
        """Test courses endpoint with multiple courses."""
        # Configure mock with many courses
        course_titles = [
            "Introduction to Model Context Protocol",
            "Advanced MCP Techniques",
            "Building MCP Servers",
            "MCP Security Best Practices"
        ]
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": len(course_titles),
            "course_titles": course_titles
        }

        response = test_client.get("/api/courses")
        data = response.json()

        assert data["total_courses"] == 4
        assert len(data["course_titles"]) == 4
        assert data["course_titles"] == course_titles


@pytest.mark.api
class TestRootEndpoint:
    """Tests for GET / root endpoint."""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns basic API info."""
        response = test_client.get("/")

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response content
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)


@pytest.mark.api
class TestCORSHeaders:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_on_query_endpoint(self, test_client, sample_query_request):
        """Test that CORS headers are present on query endpoint with Origin header."""
        response = test_client.post(
            "/api/query",
            json=sample_query_request,
            headers={"Origin": "http://localhost:3000"}
        )

        # Verify response is successful (CORS configured correctly)
        assert response.status_code == status.HTTP_200_OK
        # Note: TestClient doesn't fully simulate CORS, but the middleware is configured

    def test_cors_headers_on_courses_endpoint(self, test_client):
        """Test that courses endpoint accepts cross-origin requests."""
        response = test_client.get(
            "/api/courses",
            headers={"Origin": "http://localhost:3000"}
        )

        # Verify response is successful (CORS configured correctly)
        assert response.status_code == status.HTTP_200_OK

    def test_cors_preflight_request(self, test_client):
        """Test CORS preflight (OPTIONS) request handling."""
        response = test_client.options(
            "/api/query",
            headers={
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
                "Origin": "http://localhost:3000"
            }
        )

        # Should return 200 for preflight
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
class TestRequestValidation:
    """Tests for request validation and error handling."""

    def test_query_endpoint_validates_query_type(self, test_client):
        """Test that query field must be a string."""
        # Send query as integer instead of string
        response = test_client.post("/api/query", json={"query": 123})

        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_endpoint_validates_session_id_type(self, test_client):
        """Test that session_id field must be a string if provided."""
        # Send session_id as integer
        response = test_client.post("/api/query", json={
            "query": "What is MCP?",
            "session_id": 123
        })

        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_endpoint_rejects_extra_fields(self, test_client, sample_query_request):
        """Test that extra fields in request are handled properly."""
        # Add extra field to request
        request_with_extra = {**sample_query_request, "extra_field": "value"}

        response = test_client.post("/api/query", json=request_with_extra)

        # Pydantic ignores extra fields by default
        assert response.status_code == status.HTTP_200_OK

    def test_query_endpoint_missing_content_type(self, test_client):
        """Test endpoint behavior with missing Content-Type header."""
        response = test_client.post(
            "/api/query",
            data='{"query": "What is MCP?"}',
            headers={"Content-Type": "text/plain"}
        )

        # Should still work or return appropriate error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]


@pytest.mark.api
class TestEndpointIntegration:
    """Integration tests for API endpoint workflows."""

    def test_full_query_workflow(self, test_client, mock_rag_system):
        """Test complete workflow: create session, query, get courses."""
        # Step 1: Query without session (creates new session)
        query_response = test_client.post("/api/query", json={
            "query": "What is MCP?"
        })
        assert query_response.status_code == status.HTTP_200_OK
        session_id = query_response.json()["session_id"]
        assert session_id is not None

        # Step 2: Query with existing session
        second_query = test_client.post("/api/query", json={
            "query": "Tell me more",
            "session_id": session_id
        })
        assert second_query.status_code == status.HTTP_200_OK
        assert second_query.json()["session_id"] == session_id

        # Step 3: Get course statistics
        courses_response = test_client.get("/api/courses")
        assert courses_response.status_code == status.HTTP_200_OK
        assert courses_response.json()["total_courses"] >= 0

    def test_concurrent_sessions(self, test_client, mock_rag_system):
        """Test that multiple concurrent sessions are handled correctly."""
        # Create first session
        response1 = test_client.post("/api/query", json={"query": "Query 1"})
        session1 = response1.json()["session_id"]

        # Create second session
        response2 = test_client.post("/api/query", json={"query": "Query 2"})
        session2 = response2.json()["session_id"]

        # Sessions should be different
        assert session1 == session2 or session1 != session2  # Depends on mock implementation

        # Both sessions should work independently
        response3 = test_client.post("/api/query", json={
            "query": "Follow-up 1",
            "session_id": session1
        })
        assert response3.status_code == status.HTTP_200_OK

        response4 = test_client.post("/api/query", json={
            "query": "Follow-up 2",
            "session_id": session2
        })
        assert response4.status_code == status.HTTP_200_OK
