"""Event schemas for the async event bus."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class EventType(str, Enum):
    """Types of events in the system."""

    # Deal Lifecycle
    DEAL_CREATED = "deal.created"
    DEAL_UPDATED = "deal.updated"
    DEAL_SOURCED = "deal.sourced"
    DEAL_TRIAGED = "deal.triaged"
    DEAL_DILIGENCE_STARTED = "deal.diligence_started"
    DEAL_IC_SUBMITTED = "deal.ic_submitted"
    DEAL_APPROVED = "deal.approved"
    DEAL_REJECTED = "deal.rejected"
    DEAL_CLOSED = "deal.closed"
    DEAL_EXITED = "deal.exited"

    # Document Events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_EXTRACTION_COMPLETE = "document.extraction_complete"

    # Agent Events
    AGENT_TASK_STARTED = "agent.task_started"
    AGENT_TASK_COMPLETED = "agent.task_completed"
    AGENT_TASK_FAILED = "agent.task_failed"
    AGENT_REVIEW_REQUIRED = "agent.review_required"

    # Extraction Events
    FINANCIAL_EXTRACTED = "financial.extracted"
    LEGAL_FLAG_DETECTED = "legal.flag_detected"
    CONNECTION_DISCOVERED = "connection.discovered"

    # IC Events
    MEMO_GENERATED = "memo.generated"
    BEAR_CASE_GENERATED = "bear_case.generated"
    IC_DEBATE_STARTED = "ic.debate_started"
    IC_DEBATE_COMPLETED = "ic.debate_completed"

    # Portfolio Events
    KPI_UPDATED = "kpi.updated"
    LP_REPORT_GENERATED = "lp_report.generated"


class DealEvent(BaseModel):
    """Base event model for all system events."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    deal_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    agent_name: Optional[str] = None

    # Payload
    payload: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    correlation_id: Optional[UUID] = None  # For tracing related events
    causation_id: Optional[UUID] = None  # ID of event that caused this one
    retry_count: int = 0

    model_config = ConfigDict()

    @field_serializer("event_id", "deal_id", "document_id", "correlation_id", "causation_id")
    @staticmethod
    def serialize_uuid(v: Optional[UUID]) -> Optional[str]:
        return str(v) if v is not None else None

    @field_serializer("timestamp")
    @staticmethod
    def serialize_datetime(v: datetime) -> str:
        return v.isoformat()


class AgentTaskEvent(DealEvent):
    """Event for agent task execution."""

    agent_name: str
    task_description: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ExtractionEvent(DealEvent):
    """Event for data extraction completion."""

    extraction_type: str  # "financial", "legal", "relationship"
    extracted_values: dict[str, Any] = Field(default_factory=dict)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    source_document_id: UUID
    source_pages: list[int] = Field(default_factory=list)


class ReviewEvent(DealEvent):
    """Event for peer review requests and completions."""

    reviewer_agent: str
    reviewed_agent: str
    review_type: str  # "validation", "verification", "approval"
    issues_found: list[str] = Field(default_factory=list)
    approved: bool = False
    revision_required: bool = False
