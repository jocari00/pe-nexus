"""Pytest configuration and fixtures for PE-Nexus tests."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CHROMA_PERSIST_DIR"] = "/tmp/pe_nexus_test_chroma"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    from src.db.database import Base

    # Create in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_deal_data() -> dict:
    """Sample deal data for testing."""
    return {
        "deal_name": "Test Acquisition",
        "target_name": "Test Company",
        "target_description": "A test company for unit tests",
        "industry_sector": "Technology",
        "industry_sub_sector": "Software",
        "headquarters": "Test City, TC",
        "source_type": "proprietary",
    }


@pytest.fixture
def sample_document_path(tmp_path: Path) -> Path:
    """Create a sample PDF for testing."""
    # Create a minimal PDF-like file (not a real PDF, but sufficient for path testing)
    pdf_path = tmp_path / "test_document.pdf"
    pdf_path.write_text("Mock PDF content for testing")
    return pdf_path


@pytest.fixture
def sample_financial_data() -> dict:
    """Sample financial data for testing."""
    return {
        "fiscal_year": 2023,
        "fiscal_period": "FY",
        "revenue": 125000000,
        "ebitda": 25000000,
        "net_income": 15000000,
        "total_assets": 200000000,
        "total_liabilities": 80000000,
        "total_equity": 120000000,
    }
