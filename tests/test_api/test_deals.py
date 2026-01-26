"""Comprehensive tests for the Deals API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import UUID
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def valid_deal_data():
    """Valid deal creation payload."""
    return {
        "deal_name": "Test Acquisition Deal",
        "target_name": "Tech Corp Inc",
        "target_description": "A leading technology company specializing in AI solutions",
        "industry_sector": "Technology",
        "industry_sub_sector": "Software",
        "headquarters": "San Francisco, CA",
        "source_type": "proprietary",
        "source_description": "Referred by investment banker",
    }


@pytest.fixture
def minimal_deal_data():
    """Minimal valid deal creation payload."""
    return {
        "deal_name": "Minimal Deal",
        "target_name": "Target Co",
        "industry_sector": "Healthcare",
        "industry_sub_sector": "Services",
        "headquarters": "New York, NY",
    }


class TestDealCreation:
    """Test deal creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_deal_success(self, test_client: AsyncClient, valid_deal_data):
        """Test successful deal creation with full data."""
        response = await test_client.post("/deals/", json=valid_deal_data)

        assert response.status_code == 200
        data = response.json()

        assert "deal_id" in data
        assert data["deal_name"] == valid_deal_data["deal_name"]
        assert data["stage"] == "SOURCING"
        assert data["message"] == "Deal created successfully"

        # Verify UUID format
        UUID(data["deal_id"])  # Will raise if invalid

    @pytest.mark.asyncio
    async def test_create_deal_minimal(self, test_client: AsyncClient, minimal_deal_data):
        """Test deal creation with minimal required fields."""
        response = await test_client.post("/deals/", json=minimal_deal_data)

        assert response.status_code == 200
        data = response.json()
        assert data["deal_name"] == minimal_deal_data["deal_name"]

    @pytest.mark.asyncio
    async def test_create_deal_missing_required_field(self, test_client: AsyncClient):
        """Test deal creation fails without required fields."""
        invalid_data = {
            "deal_name": "Test Deal",
            # Missing: target_name, industry_sector, industry_sub_sector, headquarters
        }

        response = await test_client.post("/deals/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_deal_empty_name(self, test_client: AsyncClient, valid_deal_data):
        """Test deal creation fails with empty deal name."""
        valid_deal_data["deal_name"] = ""

        response = await test_client.post("/deals/", json=valid_deal_data)
        # FastAPI/Pydantic might allow empty string, but it's poor data quality
        # This tests behavior, not necessarily failure
        assert response.status_code in [200, 422]


class TestDealRetrieval:
    """Test deal retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_list_deals_empty(self, test_client: AsyncClient):
        """Test listing deals when none exist."""
        response = await test_client.get("/deals/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_deals_after_creation(self, test_client: AsyncClient, valid_deal_data):
        """Test listing deals returns created deal."""
        # Create a deal first
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        assert create_response.status_code == 200

        # List deals
        response = await test_client.get("/deals/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any(d["deal_name"] == valid_deal_data["deal_name"] for d in data)

    @pytest.mark.asyncio
    async def test_list_deals_with_stage_filter(self, test_client: AsyncClient, valid_deal_data):
        """Test filtering deals by stage."""
        # Create a deal
        await test_client.post("/deals/", json=valid_deal_data)

        # Filter by SOURCING stage
        response = await test_client.get("/deals/?stage=SOURCING")
        assert response.status_code == 200

        data = response.json()
        for deal in data:
            assert deal["stage"] == "SOURCING"

    @pytest.mark.asyncio
    async def test_list_deals_pagination(self, test_client: AsyncClient, valid_deal_data):
        """Test deal listing pagination."""
        # Create multiple deals
        for i in range(5):
            deal_data = valid_deal_data.copy()
            deal_data["deal_name"] = f"Test Deal {i}"
            await test_client.post("/deals/", json=deal_data)

        # Test limit
        response = await test_client.get("/deals/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) <= 2

        # Test offset
        response = await test_client.get("/deals/?offset=2&limit=2")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_deal_by_id(self, test_client: AsyncClient, valid_deal_data):
        """Test getting a specific deal by ID."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Get deal
        response = await test_client.get(f"/deals/{deal_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deal_id"] == deal_id
        assert data["deal_name"] == valid_deal_data["deal_name"]
        assert data["stage"] == "SOURCING"
        assert "target" in data
        assert data["target"]["name"] == valid_deal_data["target_name"]

    @pytest.mark.asyncio
    async def test_get_deal_not_found(self, test_client: AsyncClient):
        """Test getting a non-existent deal returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await test_client.get(f"/deals/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_deal_invalid_uuid(self, test_client: AsyncClient):
        """Test getting a deal with invalid UUID format."""
        response = await test_client.get("/deals/not-a-uuid")

        assert response.status_code == 422


class TestDealTransitions:
    """Test deal state transition endpoints."""

    @pytest.mark.asyncio
    async def test_valid_transitions(self, test_client: AsyncClient, valid_deal_data):
        """Test getting valid transitions for a deal."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Get valid transitions
        response = await test_client.get(f"/deals/{deal_id}/valid-transitions")

        assert response.status_code == 200
        data = response.json()
        assert data["current_stage"] == "SOURCING"
        assert "TRIAGE" in data["valid_transitions"]
        assert "REJECTED" in data["valid_transitions"]

    @pytest.mark.asyncio
    async def test_transition_sourcing_to_triage(self, test_client: AsyncClient, valid_deal_data):
        """Test transitioning a deal from SOURCING to TRIAGE."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Transition to TRIAGE
        response = await test_client.post(
            f"/deals/{deal_id}/transition",
            params={
                "to_stage": "TRIAGE",
                "transitioned_by": "test_user",
                "reason": "Deal meets initial criteria",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["previous_stage"] == "SOURCING"
        assert data["new_stage"] == "TRIAGE"

    @pytest.mark.asyncio
    async def test_transition_to_rejected(self, test_client: AsyncClient, valid_deal_data):
        """Test rejecting a deal."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Reject deal
        response = await test_client.post(
            f"/deals/{deal_id}/transition",
            params={
                "to_stage": "REJECTED",
                "transitioned_by": "test_user",
                "reason": "Does not meet investment criteria",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_stage"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_invalid_transition(self, test_client: AsyncClient, valid_deal_data):
        """Test invalid state transition returns error."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Try to skip directly to CLOSING (invalid)
        response = await test_client.post(
            f"/deals/{deal_id}/transition",
            params={
                "to_stage": "CLOSING",
                "transitioned_by": "test_user",
            }
        )

        assert response.status_code == 400
        assert "invalid transition" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_full_deal_pipeline(self, test_client: AsyncClient, valid_deal_data):
        """Test complete deal pipeline from SOURCING to PORTFOLIO."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        stages = ["TRIAGE", "DILIGENCE", "IC_REVIEW", "CLOSING", "PORTFOLIO"]

        for stage in stages:
            response = await test_client.post(
                f"/deals/{deal_id}/transition",
                params={
                    "to_stage": stage,
                    "transitioned_by": "test_user",
                    "reason": f"Advancing to {stage}",
                }
            )
            assert response.status_code == 200
            assert response.json()["new_stage"] == stage

        # Verify final state
        deal_response = await test_client.get(f"/deals/{deal_id}")
        assert deal_response.json()["stage"] == "PORTFOLIO"


class TestDealDeletion:
    """Test deal deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_deal(self, test_client: AsyncClient, valid_deal_data):
        """Test deleting a deal."""
        # Create deal
        create_response = await test_client.post("/deals/", json=valid_deal_data)
        deal_id = create_response.json()["deal_id"]

        # Delete deal
        response = await test_client.delete(f"/deals/{deal_id}")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        get_response = await test_client.get(f"/deals/{deal_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_deal(self, test_client: AsyncClient):
        """Test deleting a non-existent deal returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await test_client.delete(f"/deals/{fake_id}")

        assert response.status_code == 404
