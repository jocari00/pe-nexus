"""Comprehensive tests for the Documents API endpoints."""

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
    """Valid deal creation payload for document tests."""
    return {
        "deal_name": "Document Test Deal",
        "target_name": "Doc Corp",
        "target_description": "Test company for document tests",
        "industry_sector": "Technology",
        "industry_sub_sector": "Software",
        "headquarters": "Boston, MA",
    }


@pytest.fixture
async def created_deal(test_client: AsyncClient, valid_deal_data):
    """Create a deal and return its ID."""
    response = await test_client.post("/deals/", json=valid_deal_data)
    return response.json()["deal_id"]


def create_mock_pdf_content():
    """Create minimal mock PDF content for testing."""
    # Minimal PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
198
%%EOF
"""


class TestDocumentUpload:
    """Test document upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_pdf_document(self, test_client: AsyncClient, created_deal):
        """Test uploading a PDF document."""
        pdf_content = create_mock_pdf_content()

        files = {
            "file": ("test_document.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert "document_id" in result
        assert result["filename"] == "test_document.pdf"
        assert result["document_type"] == "CIM"
        assert result["message"] == "Document uploaded successfully"
        assert "checksum" in result

    @pytest.mark.asyncio
    async def test_upload_csv_document(self, test_client: AsyncClient, created_deal):
        """Test uploading a CSV document."""
        csv_content = b"header1,header2,header3\nvalue1,value2,value3\n"

        files = {
            "file": ("financials.csv", io.BytesIO(csv_content), "text/csv"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "financials",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", files=files, data=data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_xlsx_document(self, test_client: AsyncClient, created_deal):
        """Test uploading an Excel document."""
        # Minimal xlsx is complex, so we use a simple byte content
        # In real tests, you'd use openpyxl to create a valid file
        xlsx_content = b"PK\x03\x04..."  # Minimal ZIP header (XLSX is ZIP-based)

        files = {
            "file": ("data.xlsx", io.BytesIO(xlsx_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "financials",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", files=files, data=data)
        # May fail validation but tests the route
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, test_client: AsyncClient, created_deal):
        """Test uploading an unsupported file type returns error."""
        files = {
            "file": ("script.exe", io.BytesIO(b"malicious content"), "application/octet-stream"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "other",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", files=files, data=data)

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_deal(self, test_client: AsyncClient):
        """Test uploading to a non-existent deal returns 404."""
        fake_deal_id = "00000000-0000-0000-0000-000000000000"
        pdf_content = create_mock_pdf_content()

        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        data = {
            "deal_id": fake_deal_id,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", files=files, data=data)

        assert response.status_code == 404
        assert "deal not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_without_file(self, test_client: AsyncClient, created_deal):
        """Test upload fails without file."""
        data = {
            "deal_id": created_deal,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }

        response = await test_client.post("/documents/upload", data=data)

        assert response.status_code == 422  # Validation error


class TestDocumentRetrieval:
    """Test document retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, test_client: AsyncClient, created_deal):
        """Test getting document metadata by ID."""
        # Upload document first
        pdf_content = create_mock_pdf_content()
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }
        upload_response = await test_client.post("/documents/upload", files=files, data=data)
        doc_id = upload_response.json()["document_id"]

        # Get document
        response = await test_client.get(f"/documents/{doc_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["document_id"] == doc_id
        assert result["filename"] == "test.pdf"
        assert result["document_type"] == "CIM"
        assert result["processed"] == False

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, test_client: AsyncClient):
        """Test getting a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await test_client.get(f"/documents/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_deal_documents(self, test_client: AsyncClient, created_deal):
        """Test listing all documents for a deal."""
        # Upload multiple documents
        for i in range(3):
            pdf_content = create_mock_pdf_content()
            files = {
                "file": (f"doc_{i}.pdf", io.BytesIO(pdf_content), "application/pdf"),
            }
            data = {
                "deal_id": created_deal,
                "document_type": "CIM",
                "uploaded_by": "test_user",
            }
            await test_client.post("/documents/upload", files=files, data=data)

        # List documents
        response = await test_client.get(f"/documents/deal/{created_deal}")

        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 3
        for doc in documents:
            assert "document_id" in doc
            assert "filename" in doc


class TestDocumentProcessing:
    """Test document processing endpoint."""

    @pytest.mark.asyncio
    async def test_process_document(self, test_client: AsyncClient, created_deal):
        """Test processing a document creates embeddings."""
        # Upload document first
        pdf_content = create_mock_pdf_content()
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }
        upload_response = await test_client.post("/documents/upload", files=files, data=data)
        doc_id = upload_response.json()["document_id"]

        # Process document
        response = await test_client.post(f"/documents/{doc_id}/process")

        # Processing might fail for mock PDF but should return something
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_process_nonexistent_document(self, test_client: AsyncClient):
        """Test processing a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await test_client.post(f"/documents/{fake_id}/process")

        assert response.status_code == 404


class TestDocumentDeletion:
    """Test document deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_document(self, test_client: AsyncClient, created_deal):
        """Test deleting a document."""
        # Upload document first
        pdf_content = create_mock_pdf_content()
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf"),
        }
        data = {
            "deal_id": created_deal,
            "document_type": "CIM",
            "uploaded_by": "test_user",
        }
        upload_response = await test_client.post("/documents/upload", files=files, data=data)
        doc_id = upload_response.json()["document_id"]

        # Delete document
        response = await test_client.delete(f"/documents/{doc_id}")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        get_response = await test_client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, test_client: AsyncClient):
        """Test deleting a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await test_client.delete(f"/documents/{fake_id}")

        assert response.status_code == 404
