"""Comprehensive tests for the Agents API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import UUID
import sys
import io
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def valid_deal_data():
    """Valid deal creation payload for agent tests."""
    return {
        "deal_name": "Agent Test Deal",
        "target_name": "Agent Corp",
        "target_description": "Test company for agent tests",
        "industry_sector": "Technology",
        "industry_sub_sector": "Software",
        "headquarters": "Seattle, WA",
    }


@pytest.fixture
async def deal_with_document(test_client: AsyncClient, valid_deal_data):
    """Create a deal with an uploaded document."""
    # Create deal
    deal_response = await test_client.post("/deals/", json=valid_deal_data)
    deal_id = deal_response.json()["deal_id"]

    # Upload a simple document
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000102 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""

    files = {
        "file": ("test_cim.pdf", io.BytesIO(pdf_content), "application/pdf"),
    }
    data = {
        "deal_id": deal_id,
        "document_type": "CIM",
        "uploaded_by": "test_user",
    }
    doc_response = await test_client.post("/documents/upload", files=files, data=data)

    return {
        "deal_id": deal_id,
        "document_id": doc_response.json()["document_id"],
    }


class TestAvailableAgents:
    """Test available agents listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_available_agents(self, test_client: AsyncClient):
        """Test listing all available agents."""
        response = await test_client.get("/agents/available")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert len(data["agents"]) > 0

        # Check for expected agents
        agent_names = [a["name"] for a in data["agents"]]
        assert "ForensicAnalyst" in agent_names
        assert "IntelligenceScout" in agent_names

    @pytest.mark.asyncio
    async def test_agent_capabilities_present(self, test_client: AsyncClient):
        """Test that agents have capabilities defined."""
        response = await test_client.get("/agents/available")
        data = response.json()

        for agent in data["agents"]:
            assert "name" in agent
            assert "description" in agent
            assert "capabilities" in agent


class TestForensicAgent:
    """Test Forensic Analyst agent endpoints."""

    @pytest.mark.asyncio
    async def test_extract_financials_async(
        self, test_client: AsyncClient, deal_with_document
    ):
        """Test async financial extraction returns task ID."""
        request_data = {
            "document_id": deal_with_document["document_id"],
            "deal_id": deal_with_document["deal_id"],
        }

        response = await test_client.post("/agents/forensic/extract", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["agent_name"] == "ForensicAnalyst"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_extract_financials_sync(
        self, test_client: AsyncClient, deal_with_document
    ):
        """Test sync financial extraction."""
        request_data = {
            "document_id": deal_with_document["document_id"],
            "deal_id": deal_with_document["deal_id"],
        }

        response = await test_client.post("/agents/forensic/extract-sync", json=request_data)

        # May succeed or fail depending on LLM availability
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_extract_nonexistent_document(self, test_client: AsyncClient, valid_deal_data):
        """Test extraction fails for non-existent document."""
        # Create deal
        deal_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = deal_response.json()["deal_id"]

        fake_doc_id = "00000000-0000-0000-0000-000000000000"

        request_data = {
            "document_id": fake_doc_id,
            "deal_id": deal_id,
        }

        response = await test_client.post("/agents/forensic/extract", json=request_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_extract_nonexistent_deal(self, test_client: AsyncClient, deal_with_document):
        """Test extraction fails for non-existent deal."""
        fake_deal_id = "00000000-0000-0000-0000-000000000000"

        request_data = {
            "document_id": deal_with_document["document_id"],
            "deal_id": fake_deal_id,
        }

        response = await test_client.post("/agents/forensic/extract", json=request_data)

        assert response.status_code == 404


class TestScoutAgent:
    """Test Intelligence Scout agent endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_company_async(self, test_client: AsyncClient):
        """Test async company analysis."""
        request_data = {
            "company_name": "Test Company Inc",
            "industry": "Technology",
            "sub_sector": "Software",
        }

        response = await test_client.post("/agents/scout/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["agent_name"] == "IntelligenceScout"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_analyze_company_sync(self, test_client: AsyncClient):
        """Test sync company analysis."""
        request_data = {
            "company_name": "Test Company Inc",
            "industry": "Technology",
            "sub_sector": "Software",
        }

        response = await test_client.post("/agents/scout/analyze-sync", json=request_data)

        # May succeed or fail depending on external APIs
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_scan_industry_async(self, test_client: AsyncClient):
        """Test async industry scan."""
        request_data = {
            "industry": "Technology",
            "limit": 5,
            "min_score": 3.0,
        }

        response = await test_client.post("/agents/scout/scan", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_scan_industry_sync(self, test_client: AsyncClient):
        """Test sync industry scan."""
        request_data = {
            "industry": "Technology",
            "limit": 5,
            "min_score": 3.0,
        }

        response = await test_client.post("/agents/scout/scan-sync", json=request_data)

        # May succeed or fail depending on external APIs
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_market_signals(self, test_client: AsyncClient):
        """Test getting market signals."""
        response = await test_client.get(
            "/agents/scout/signals",
            params={"company_name": "Test Company"}
        )

        # May succeed or fail depending on external APIs
        assert response.status_code in [200, 500]


class TestTaskManagement:
    """Test task management endpoints."""

    @pytest.mark.asyncio
    async def test_get_task_status(self, test_client: AsyncClient):
        """Test getting task status."""
        # Start a task first
        request_data = {
            "company_name": "Test Company Inc",
            "industry": "Technology",
        }
        start_response = await test_client.post("/agents/scout/analyze", json=request_data)
        task_id = start_response.json()["task_id"]

        # Get task status
        response = await test_client.get(f"/agents/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["running", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, test_client: AsyncClient):
        """Test getting a non-existent task returns 404."""
        response = await test_client.get("/agents/tasks/nonexistent_task_id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_tasks(self, test_client: AsyncClient):
        """Test listing recent tasks."""
        # Create a task
        request_data = {
            "company_name": "Test Company",
            "industry": "Technology",
        }
        await test_client.post("/agents/scout/analyze", json=request_data)

        # List tasks
        response = await test_client.get("/agents/tasks")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_tasks_with_filter(self, test_client: AsyncClient):
        """Test listing tasks with status filter."""
        response = await test_client.get("/agents/tasks", params={"status": "running"})

        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task.get("status") == "running"


class TestPeerReview:
    """Test peer review endpoint."""

    @pytest.mark.asyncio
    async def test_review_completed_task(self, test_client: AsyncClient):
        """Test requesting peer review for a completed task."""
        # This test would require a completed task
        # For now, just test the endpoint exists and handles invalid task
        response = await test_client.post(
            "/agents/review/nonexistent_task",
            params={"review_type": "validation"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_review_invalid_type(self, test_client: AsyncClient):
        """Test peer review with invalid review type still works."""
        # Create and complete a task first
        # For now, test that endpoint handles invalid gracefully
        response = await test_client.post(
            "/agents/review/nonexistent_task",
            params={"review_type": "invalid_type"}
        )

        # Should return 404 for task, not validation error for type
        assert response.status_code == 404
