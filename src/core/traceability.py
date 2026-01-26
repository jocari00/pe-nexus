"""Traceability Engine for grounding all LLM extractions to source documents."""

import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.schemas.financials import BoundingBox, SourceReference


class BoundedCache:
    """A simple bounded LRU cache with maximum size."""

    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache, moving it to the end (most recent)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache, evicting oldest if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)  # Remove oldest
        self._cache[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def __len__(self) -> int:
        return len(self._cache)


@dataclass(frozen=True)
class ExtractionRecord:
    """
    Immutable record of an extraction with full provenance.

    This record cannot be modified after creation, ensuring
    audit trail integrity.
    """

    extraction_id: UUID
    source_document_id: UUID
    source_document_name: str
    source_page: int
    source_coordinates: Optional[BoundingBox]
    text_snippet: str
    extracted_value: Any
    value_type: str  # "decimal", "string", "date", "integer"
    confidence: float
    prompt_hash: str
    model_version: str
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TracedExtraction(BaseModel):
    """
    Pydantic model for traced extractions.

    Every LLM extraction includes grounding information
    for full reproducibility and auditability.
    """

    extraction_id: UUID = Field(default_factory=uuid4)
    value: Any
    value_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: SourceReference
    extraction_prompt: str
    prompt_hash: str
    model_version: str
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional verification
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: str = ""


class DualVerification(BaseModel):
    """
    Dual-agent verification for critical financial metrics.

    Compares extractions from two independent agents and
    flags discrepancies for human review.
    """

    primary: TracedExtraction
    secondary: TracedExtraction
    variance_threshold: Decimal = Decimal("0.01")  # 1%
    requires_human_review: bool = False
    variance_amount: Optional[Decimal] = None
    reconciled_value: Optional[Any] = None
    reconciliation_notes: str = ""

    def check_variance(self) -> bool:
        """
        Check if the primary and secondary extractions are within tolerance.

        Returns True if variance is acceptable, False if human review needed.
        """
        if self.primary.value_type != "decimal" or self.secondary.value_type != "decimal":
            # Non-numeric values require exact match
            self.requires_human_review = self.primary.value != self.secondary.value
            return not self.requires_human_review

        try:
            primary_val = Decimal(str(self.primary.value))
            secondary_val = Decimal(str(self.secondary.value))

            if primary_val == 0 and secondary_val == 0:
                self.variance_amount = Decimal("0")
                return True

            # Calculate percentage variance
            avg = (primary_val + secondary_val) / 2
            if avg != 0:
                self.variance_amount = abs(primary_val - secondary_val) / abs(avg)
            else:
                self.variance_amount = Decimal("0")

            self.requires_human_review = self.variance_amount > self.variance_threshold
            return not self.requires_human_review

        except (ValueError, TypeError):
            self.requires_human_review = True
            return False


class TraceabilityEngine:
    """
    Engine for managing extraction traceability across the system.

    Provides methods for:
    - Creating traced extractions with proper grounding
    - Generating prompt hashes for reproducibility
    - Managing dual verification for critical values
    - Audit trail maintenance
    """

    def __init__(
        self,
        model_version: str = "claude-sonnet-4-20250514",
        cache_maxsize: int = 1000,
    ):
        self.model_version = model_version
        # Use bounded cache to prevent memory leaks
        self._extraction_cache: BoundedCache = BoundedCache(maxsize=cache_maxsize)

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Generate SHA-256 hash of extraction prompt for reproducibility."""
        return hashlib.sha256(prompt.encode()).hexdigest()

    def create_extraction(
        self,
        value: Any,
        value_type: str,
        confidence: float,
        document_id: UUID,
        document_name: str,
        page_number: int,
        text_snippet: str,
        extraction_prompt: str,
        bounding_box: Optional[BoundingBox] = None,
        url: Optional[str] = None,
    ) -> TracedExtraction:
        """
        Create a new traced extraction with full provenance.

        Args:
            value: The extracted value
            value_type: Type of value ("decimal", "string", "date", "integer")
            confidence: Model confidence score (0.0 to 1.0)
            document_id: Source document UUID
            document_name: Source document filename
            page_number: Page number in source document
            text_snippet: Relevant text context
            extraction_prompt: The prompt used for extraction
            bounding_box: Optional PDF coordinates
            url: Optional source URL

        Returns:
            TracedExtraction with full grounding information
        """
        source = SourceReference(
            document_id=document_id,
            document_name=document_name,
            page_number=page_number,
            bounding_box=bounding_box,
            text_snippet=text_snippet[:500] if text_snippet else "",
            url=url,
        )

        extraction = TracedExtraction(
            value=value,
            value_type=value_type,
            confidence=confidence,
            source=source,
            extraction_prompt=extraction_prompt,
            prompt_hash=self.hash_prompt(extraction_prompt),
            model_version=self.model_version,
        )

        # Cache for potential dual verification (bounded to prevent memory leaks)
        cache_key = f"{document_id}:{page_number}:{value_type}"
        self._extraction_cache.set(cache_key, extraction)

        return extraction

    def create_dual_verification(
        self,
        primary: TracedExtraction,
        secondary: TracedExtraction,
        variance_threshold: Decimal = Decimal("0.01"),
    ) -> DualVerification:
        """
        Create a dual verification record for critical values.

        Args:
            primary: First extraction (typically from main agent)
            secondary: Second extraction (from verification agent)
            variance_threshold: Maximum allowed variance (default 1%)

        Returns:
            DualVerification record with variance analysis
        """
        verification = DualVerification(
            primary=primary,
            secondary=secondary,
            variance_threshold=variance_threshold,
        )

        # Automatically check variance
        verification.check_variance()

        return verification

    def verify_extraction(
        self,
        extraction: TracedExtraction,
        verified_by: str,
        notes: str = "",
    ) -> TracedExtraction:
        """
        Mark an extraction as verified by a human or agent.

        Args:
            extraction: The extraction to verify
            verified_by: Name/ID of verifier
            notes: Optional verification notes

        Returns:
            New extraction instance with verification info
        """
        return extraction.model_copy(
            update={
                "verified_by": verified_by,
                "verified_at": datetime.now(timezone.utc),
                "verification_notes": notes,
            }
        )

    def to_immutable_record(self, extraction: TracedExtraction) -> ExtractionRecord:
        """
        Convert a TracedExtraction to an immutable ExtractionRecord.

        Use this for permanent storage in the audit trail.
        """
        return ExtractionRecord(
            extraction_id=extraction.extraction_id,
            source_document_id=extraction.source.document_id,
            source_document_name=extraction.source.document_name,
            source_page=extraction.source.page_number,
            source_coordinates=extraction.source.bounding_box,
            text_snippet=extraction.source.text_snippet,
            extracted_value=extraction.value,
            value_type=extraction.value_type,
            confidence=extraction.confidence,
            prompt_hash=extraction.prompt_hash,
            model_version=extraction.model_version,
            extracted_at=extraction.extracted_at,
        )

    def format_citation(self, extraction: TracedExtraction) -> str:
        """
        Format a human-readable citation for an extraction.

        Returns a string like: "[Document.pdf, p.15, confidence: 0.95]"
        """
        return (
            f"[{extraction.source.document_name}, "
            f"p.{extraction.source.page_number}, "
            f"confidence: {extraction.confidence:.2f}]"
        )

    def get_source_highlight(self, extraction: TracedExtraction) -> dict:
        """
        Get highlighting information for UI display.

        Returns coordinates and context for highlighting the source
        in a document viewer.
        """
        return {
            "document_id": str(extraction.source.document_id),
            "page": extraction.source.page_number,
            "bounding_box": (
                extraction.source.bounding_box.model_dump()
                if extraction.source.bounding_box
                else None
            ),
            "text_snippet": extraction.source.text_snippet,
            "value": extraction.value,
            "confidence": extraction.confidence,
        }


# Global traceability engine instance
_traceability_engine: Optional[TraceabilityEngine] = None
_traceability_engine_lock = threading.Lock()


def get_traceability_engine() -> TraceabilityEngine:
    """Get or create the global traceability engine (thread-safe)."""
    global _traceability_engine
    if _traceability_engine is None:
        with _traceability_engine_lock:
            # Double-check locking pattern
            if _traceability_engine is None:
                _traceability_engine = TraceabilityEngine()
    return _traceability_engine
