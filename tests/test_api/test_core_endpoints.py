"""Tests for core API endpoints (root, health, config)."""

import pytest
from httpx import ASGITransport, AsyncClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestRootEndpoint:
    """Test root endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_api_info(self, test_client: AsyncClient):
        """Test root endpoint returns API information."""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "PE-Nexus"
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data
        assert data["docs"] == "/docs"

    @pytest.mark.asyncio
    async def test_root_endpoints_list(self, test_client: AsyncClient):
        """Test root endpoint contains all main endpoints."""
        response = await test_client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "deals" in endpoints
        assert "documents" in endpoints
        assert "agents" in endpoints


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, test_client: AsyncClient):
        """Test health check returns healthy status."""
        response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "database" in data
        assert data["vector_store"] == "chromadb"

    @pytest.mark.asyncio
    async def test_health_check_format(self, test_client: AsyncClient):
        """Test health check response format."""
        response = await test_client.get("/health")
        data = response.json()

        # All expected fields present
        expected_fields = ["status", "database", "vector_store"]
        for field in expected_fields:
            assert field in data


class TestConfigEndpoint:
    """Test configuration endpoint."""

    @pytest.mark.asyncio
    async def test_config_returns_non_sensitive_info(self, test_client: AsyncClient):
        """Test config endpoint returns non-sensitive configuration."""
        response = await test_client.get("/config")

        assert response.status_code == 200
        data = response.json()

        assert "app_name" in data
        assert "debug" in data
        assert "log_level" in data
        assert "claude_model" in data
        assert "database_type" in data

    @pytest.mark.asyncio
    async def test_config_does_not_expose_secrets(self, test_client: AsyncClient):
        """Test config endpoint does not expose sensitive data."""
        response = await test_client.get("/config")
        data = response.json()

        # Should not contain sensitive keys
        sensitive_keys = ["api_key", "secret", "password", "token", "anthropic_api_key"]
        for key in sensitive_keys:
            assert key not in str(data).lower()


class TestDocumentation:
    """Test documentation endpoints."""

    @pytest.mark.asyncio
    async def test_docs_endpoint_accessible(self, test_client: AsyncClient):
        """Test OpenAPI docs endpoint is accessible."""
        response = await test_client.get("/docs")

        # Should return HTML page
        assert response.status_code == 200
        # Content type should be HTML
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_redoc_endpoint_accessible(self, test_client: AsyncClient):
        """Test ReDoc endpoint is accessible."""
        response = await test_client.get("/redoc")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_schema_accessible(self, test_client: AsyncClient):
        """Test OpenAPI JSON schema is accessible."""
        response = await test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestCORS:
    """Test CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, test_client: AsyncClient):
        """Test CORS headers are present in response."""
        response = await test_client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # CORS should be configured
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_404_for_unknown_route(self, test_client: AsyncClient):
        """Test 404 for non-existent routes."""
        response = await test_client.get("/nonexistent/route")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, test_client: AsyncClient):
        """Test method not allowed for wrong HTTP methods."""
        # Try to POST to a GET-only endpoint
        response = await test_client.post("/health")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_invalid_json_body(self, test_client: AsyncClient):
        """Test invalid JSON body returns validation error."""
        response = await test_client.post(
            "/deals/",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422
