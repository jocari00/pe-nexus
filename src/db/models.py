"""SQLAlchemy ORM models for PE-Nexus."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.schemas.deal import DealStage

from .database import Base


def generate_uuid() -> str:
    """Generate UUID as string for SQLite compatibility."""
    return str(uuid4())


class DealModel(Base):
    """SQLAlchemy model for deals."""

    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    deal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Pipeline State
    stage: Mapped[str] = mapped_column(
        String(50), default=DealStage.SOURCING.value, nullable=False
    )
    sub_stage: Mapped[Optional[str]] = mapped_column(String(100))

    # Target Company (embedded as JSON for simplicity)
    target_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_legal_name: Mapped[Optional[str]] = mapped_column(String(255))
    target_headquarters: Mapped[str] = mapped_column(String(255), nullable=False)
    target_description: Mapped[str] = mapped_column(Text, default="")
    target_website: Mapped[Optional[str]] = mapped_column(String(500))
    target_employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    target_founded_year: Mapped[Optional[int]] = mapped_column(Integer)

    # Industry
    industry_sector: Mapped[str] = mapped_column(String(100), nullable=False)
    industry_sub_sector: Mapped[str] = mapped_column(String(100), nullable=False)
    industry_sic_code: Mapped[Optional[str]] = mapped_column(String(10))
    industry_naics_code: Mapped[Optional[str]] = mapped_column(String(10))

    # Geography
    geography: Mapped[list] = mapped_column(JSON, default=list)

    # Deal Metrics
    enterprise_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    equity_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    entry_multiple: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Sourcing
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_description: Mapped[Optional[str]] = mapped_column(Text)
    deal_score: Mapped[Optional[float]] = mapped_column(Float)

    # Data Room
    data_room_id: Mapped[Optional[str]] = mapped_column(String(100))

    # JSON fields for complex nested data
    state_history: Mapped[list] = mapped_column(JSON, default=list)
    adjustments: Mapped[list] = mapped_column(JSON, default=list)
    model_outputs: Mapped[Optional[dict]] = mapped_column(JSON)
    warm_paths: Mapped[list] = mapped_column(JSON, default=list)
    deal_team: Mapped[list] = mapped_column(JSON, default=list)
    legal_flags: Mapped[list] = mapped_column(JSON, default=list)
    diligence_checklist: Mapped[dict] = mapped_column(JSON, default=dict)
    investment_memo: Mapped[Optional[dict]] = mapped_column(JSON)
    bear_case: Mapped[Optional[dict]] = mapped_column(JSON)
    ic_decision: Mapped[Optional[dict]] = mapped_column(JSON)
    portfolio_kpis: Mapped[list] = mapped_column(JSON, default=list)
    lp_reports: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    documents: Mapped[list["DocumentModel"]] = relationship(
        "DocumentModel", back_populates="deal", cascade="all, delete-orphan"
    )
    financials: Mapped[list["FinancialModel"]] = relationship(
        "FinancialModel", back_populates="deal", cascade="all, delete-orphan"
    )
    extractions: Mapped[list["ExtractionModel"]] = relationship(
        "ExtractionModel", back_populates="deal", cascade="all, delete-orphan"
    )


class DocumentModel(Base):
    """SQLAlchemy model for documents."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    deal: Mapped["DealModel"] = relationship("DealModel", back_populates="documents")
    extractions: Mapped[list["ExtractionModel"]] = relationship(
        "ExtractionModel", back_populates="document", cascade="all, delete-orphan"
    )


class FinancialModel(Base):
    """SQLAlchemy model for financial data with traceability."""

    __tablename__ = "financials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(10), default="FY")

    # Income Statement
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    revenue_source: Mapped[Optional[dict]] = mapped_column(JSON)
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    gross_profit_source: Mapped[Optional[dict]] = mapped_column(JSON)
    ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    ebitda_source: Mapped[Optional[dict]] = mapped_column(JSON)
    ebit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    ebit_source: Mapped[Optional[dict]] = mapped_column(JSON)
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    net_income_source: Mapped[Optional[dict]] = mapped_column(JSON)

    # Balance Sheet
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_assets_source: Mapped[Optional[dict]] = mapped_column(JSON)
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_liabilities_source: Mapped[Optional[dict]] = mapped_column(JSON)
    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_equity_source: Mapped[Optional[dict]] = mapped_column(JSON)
    cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    cash_source: Mapped[Optional[dict]] = mapped_column(JSON)
    total_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_debt_source: Mapped[Optional[dict]] = mapped_column(JSON)

    # Cash Flow
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    operating_cash_flow_source: Mapped[Optional[dict]] = mapped_column(JSON)
    capex: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    capex_source: Mapped[Optional[dict]] = mapped_column(JSON)
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    free_cash_flow_source: Mapped[Optional[dict]] = mapped_column(JSON)

    # Calculated Metrics
    revenue_growth: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    ebitda_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    net_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # Relationships
    deal: Mapped["DealModel"] = relationship("DealModel", back_populates="financials")


class ExtractionModel(Base):
    """SQLAlchemy model for traced extractions."""

    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )

    # Extraction Details
    extraction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)  # decimal, string, date
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Source Tracing
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON)
    text_snippet: Mapped[str] = mapped_column(Text, default="")

    # Reproducibility
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Verification
    verified_by: Mapped[Optional[str]] = mapped_column(String(100))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    deal: Mapped["DealModel"] = relationship("DealModel", back_populates="extractions")
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel", back_populates="extractions"
    )


class PersonModel(Base):
    """SQLAlchemy model for people in the relationship graph."""

    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    is_firm_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class RelationshipModel(Base):
    """SQLAlchemy model for relationships between people."""

    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    person_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("persons.id"), nullable=False, index=True
    )
    person_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("persons.id"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    context: Mapped[Optional[str]] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    person_a: Mapped["PersonModel"] = relationship(
        "PersonModel",
        foreign_keys=[person_a_id],
        backref="relationships_as_person_a",
    )
    person_b: Mapped["PersonModel"] = relationship(
        "PersonModel",
        foreign_keys=[person_b_id],
        backref="relationships_as_person_b",
    )


class EventLogModel(Base):
    """SQLAlchemy model for event audit log."""

    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    deal_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("deals.id"), index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(String(36))
    agent_name: Mapped[Optional[str]] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    causation_id: Mapped[Optional[str]] = mapped_column(String(36))
