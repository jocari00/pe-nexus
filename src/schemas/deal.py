"""Master Deal schema and related entities."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .financials import (
    EBITDAAdjustment,
    LBOModelOutput,
    SourceReference,
    TracedFinancials,
    TracedValue,
)


class DealStage(str, Enum):
    """Deal pipeline stages."""

    SOURCING = "SOURCING"
    TRIAGE = "TRIAGE"
    DILIGENCE = "DILIGENCE"
    IC_REVIEW = "IC_REVIEW"
    CLOSING = "CLOSING"
    PORTFOLIO = "PORTFOLIO"
    EXITED = "EXITED"
    REJECTED = "REJECTED"


class IndustryClassification(BaseModel):
    """Industry classification with hierarchy."""

    sector: str
    sub_sector: str
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)


class TargetCompany(BaseModel):
    """Target company profile."""

    company_id: UUID = Field(default_factory=uuid4)
    name: str
    legal_name: Optional[str] = None
    headquarters: str
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None
    description: str = ""
    industry: IndustryClassification


class TeamMember(BaseModel):
    """Deal team member."""

    user_id: UUID
    name: str
    role: str  # e.g., "Partner", "Associate", "Analyst"
    email: str
    assigned_at: datetime


class StateTransition(BaseModel):
    """Record of a stage transition."""

    transition_id: UUID = Field(default_factory=uuid4)
    from_stage: DealStage
    to_stage: DealStage
    transitioned_at: datetime
    transitioned_by: str
    reason: str = ""
    metadata: dict = Field(default_factory=dict)


class TracedDocument(BaseModel):
    """Document with metadata and traceability."""

    document_id: UUID = Field(default_factory=uuid4)
    filename: str
    document_type: str  # CIM, financials, legal, VDR, etc.
    uploaded_at: datetime
    uploaded_by: str
    file_path: str
    file_size_bytes: int
    page_count: Optional[int] = None
    checksum: str  # SHA-256 for integrity
    processed: bool = False
    extraction_status: Optional[str] = None


class ConnectionPath(BaseModel):
    """Path to a target through network connections."""

    path_id: UUID = Field(default_factory=uuid4)
    target_person: str
    target_company: str
    hops: list[dict]  # List of {person, company, relationship}
    connection_strength: float = Field(ge=0.0, le=1.0)
    suggested_intro: str = ""
    discovered_at: datetime


class LegalFlag(BaseModel):
    """Legal/contractual risk flag from diligence."""

    flag_id: UUID = Field(default_factory=uuid4)
    category: str  # CoC, non-compete, indemnity, MAC, etc.
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    source: SourceReference
    mitigation: Optional[str] = None
    reviewed_by: Optional[str] = None


class DiligenceItem(BaseModel):
    """Single diligence checklist item."""

    item_id: UUID = Field(default_factory=uuid4)
    category: str  # financial, legal, commercial, operational, etc.
    description: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    documents: list[UUID] = Field(default_factory=list)


class DiligenceChecklist(BaseModel):
    """Full diligence checklist."""

    items: list[DiligenceItem] = Field(default_factory=list)
    overall_progress: float = 0.0  # 0.0 to 1.0
    last_updated: Optional[datetime] = None


class TracedMemo(BaseModel):
    """Investment memo with source tracing."""

    memo_id: UUID = Field(default_factory=uuid4)
    memo_type: str  # "investment_memo", "bear_case", "update"
    title: str
    content: str
    sections: dict[str, str] = Field(default_factory=dict)
    sources: list[SourceReference] = Field(default_factory=list)
    generated_by: str
    generated_at: datetime
    version: int = 1


class ICDecision(BaseModel):
    """Investment Committee decision record."""

    decision_id: UUID = Field(default_factory=uuid4)
    decision: str  # APPROVED, REJECTED, MORE_INFO_REQUIRED
    decision_date: datetime
    committee_members: list[str]
    voting_record: dict[str, str] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    notes: str = ""


class PortfolioKPIs(BaseModel):
    """Portfolio company KPIs for monitoring."""

    kpi_date: datetime
    revenue_actual: Optional[Decimal] = None
    revenue_budget: Optional[Decimal] = None
    ebitda_actual: Optional[Decimal] = None
    ebitda_budget: Optional[Decimal] = None
    cash_balance: Optional[Decimal] = None
    headcount: Optional[int] = None
    custom_kpis: dict[str, Decimal] = Field(default_factory=dict)
    commentary: str = ""


class LPReport(BaseModel):
    """LP report for portfolio company."""

    report_id: UUID = Field(default_factory=uuid4)
    period: str  # e.g., "Q4 2024"
    generated_at: datetime
    narrative: str
    kpis: PortfolioKPIs
    highlights: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    outlook: str = ""


class MasterDeal(BaseModel):
    """
    Core Deal Entity - persists across entire lifecycle.

    This is the single source of truth for all deal information,
    with full traceability for every extracted value.
    """

    # Identity
    deal_id: UUID = Field(default_factory=uuid4)
    deal_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Pipeline State
    stage: DealStage = DealStage.SOURCING
    sub_stage: Optional[str] = None
    state_history: list[StateTransition] = Field(default_factory=list)

    # Company Profile
    target: TargetCompany
    geography: list[str] = Field(default_factory=list)

    # Financials (with traceability)
    financials: list[TracedFinancials] = Field(default_factory=list)
    adjustments: list[EBITDAAdjustment] = Field(default_factory=list)
    model_outputs: Optional[LBOModelOutput] = None

    # Deal Metrics
    enterprise_value: Optional[TracedValue] = None
    equity_value: Optional[TracedValue] = None
    entry_multiple: Optional[Decimal] = None

    # Documents
    documents: list[TracedDocument] = Field(default_factory=list)
    data_room_id: Optional[str] = None

    # Relationships
    warm_paths: list[ConnectionPath] = Field(default_factory=list)
    deal_team: list[TeamMember] = Field(default_factory=list)

    # Sourcing
    source_type: Optional[str] = None  # proprietary, auction, referral
    source_description: Optional[str] = None
    deal_score: Optional[float] = None

    # Diligence
    legal_flags: list[LegalFlag] = Field(default_factory=list)
    diligence_checklist: DiligenceChecklist = Field(default_factory=DiligenceChecklist)

    # IC Materials
    investment_memo: Optional[TracedMemo] = None
    bear_case: Optional[TracedMemo] = None
    ic_decision: Optional[ICDecision] = None

    # Post-Close
    portfolio_kpis: list[PortfolioKPIs] = Field(default_factory=list)
    lp_reports: list[LPReport] = Field(default_factory=list)

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    @field_serializer("deal_id")
    @staticmethod
    def serialize_uuid(v: UUID) -> str:
        return str(v)

    @field_serializer("created_at", "updated_at")
    @staticmethod
    def serialize_datetime(v: datetime) -> str:
        return v.isoformat()

    @field_serializer("entry_multiple")
    @staticmethod
    def serialize_decimal(v: Optional[Decimal]) -> Optional[str]:
        return str(v) if v is not None else None


# Request/Response models for API
class DealCreate(BaseModel):
    """Request model for creating a new deal."""

    deal_name: str
    target_name: str
    target_description: str = ""
    industry_sector: str
    industry_sub_sector: str
    headquarters: str
    source_type: Optional[str] = None
    source_description: Optional[str] = None


class DealSummary(BaseModel):
    """Summary view of a deal for list endpoints."""

    deal_id: UUID
    deal_name: str
    target_name: str
    stage: DealStage
    industry_sector: str
    created_at: datetime
    updated_at: datetime
    deal_score: Optional[float] = None
