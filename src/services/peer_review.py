"""Peer Review Service for cross-agent validation.

Implements the peer review protocol where agent outputs are validated
by another agent before stage transitions, ensuring quality control
and reducing errors.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4

from src.agents.base import AgentOutput, BaseAgent
from src.core.events import get_event_bus
from src.schemas.events import EventType

logger = logging.getLogger(__name__)


class ReviewType(str, Enum):
    """Types of peer review."""

    VALIDATION = "validation"  # Check for errors/issues
    VERIFICATION = "verification"  # Confirm extracted values
    APPROVAL = "approval"  # Approve for stage transition


class ReviewDecision(str, Enum):
    """Possible review decisions."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ESCALATE = "escalate"


@dataclass
class ReviewIssue:
    """Issue identified during review."""

    issue_id: UUID = field(default_factory=uuid4)
    severity: str = "medium"  # low, medium, high, critical
    category: str = ""  # data_quality, calculation, missing_info, etc.
    description: str = ""
    field_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggested_fix: Optional[str] = None


@dataclass
class ReviewResult:
    """Result of a peer review."""

    review_id: UUID = field(default_factory=uuid4)
    reviewed_agent: str = ""
    reviewer_agent: str = ""
    review_type: ReviewType = ReviewType.VALIDATION
    decision: ReviewDecision = ReviewDecision.APPROVED
    issues: list[ReviewIssue] = field(default_factory=list)
    notes: str = ""
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0
    output: Optional[AgentOutput] = None

    @property
    def approved(self) -> bool:
        """Check if review was approved."""
        return self.decision == ReviewDecision.APPROVED

    @property
    def needs_revision(self) -> bool:
        """Check if revision is required."""
        return self.decision == ReviewDecision.NEEDS_REVISION

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "review_id": str(self.review_id),
            "reviewed_agent": self.reviewed_agent,
            "reviewer_agent": self.reviewer_agent,
            "review_type": self.review_type.value,
            "decision": self.decision.value,
            "issues": [
                {
                    "issue_id": str(i.issue_id),
                    "severity": i.severity,
                    "category": i.category,
                    "description": i.description,
                    "field_name": i.field_name,
                    "suggested_fix": i.suggested_fix,
                }
                for i in self.issues
            ],
            "notes": self.notes,
            "reviewed_at": self.reviewed_at.isoformat(),
            "confidence": self.confidence,
            "approved": self.approved,
        }


class ReviewerProtocol(Protocol):
    """Protocol for agents that can perform reviews."""

    name: str

    async def validate(self, output: AgentOutput) -> ReviewResult:
        """Validate another agent's output."""
        ...

    async def revise(self, issues: list[ReviewIssue]) -> AgentOutput:
        """Revise output based on review issues."""
        ...


class PeerReviewService:
    """
    Service for managing peer reviews between agents.

    Implements the recursive review protocol:
    1. Original agent produces output
    2. Reviewer agent validates the output
    3. If issues found, original agent revises
    4. Review repeats until clean or max iterations reached
    """

    def __init__(self, max_review_iterations: int = 3):
        """
        Initialize the peer review service.

        Args:
            max_review_iterations: Maximum review cycles before escalation
        """
        self.max_review_iterations = max_review_iterations
        self._event_bus = None

    @property
    def event_bus(self):
        """Get the event bus."""
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    async def peer_review(
        self,
        output: AgentOutput,
        reviewer: BaseAgent,
        review_type: ReviewType = ReviewType.VALIDATION,
        deal_id: Optional[UUID] = None,
    ) -> ReviewResult:
        """
        Perform peer review with recursive revision loop.

        Args:
            output: The agent output to review
            reviewer: The agent performing the review
            review_type: Type of review to perform
            deal_id: Optional deal context

        Returns:
            ReviewResult with final decision
        """
        iteration = 0
        current_output = output

        while iteration < self.max_review_iterations:
            iteration += 1
            logger.info(
                f"Peer review iteration {iteration}: "
                f"{output.agent_name} reviewed by {reviewer.name}"
            )

            # Perform review
            review = await self._perform_review(
                current_output, reviewer, review_type
            )

            # Publish review event
            await self.event_bus.publish(
                event_type=EventType.AGENT_REVIEW_REQUIRED
                if review.needs_revision
                else EventType.AGENT_TASK_COMPLETED,
                deal_id=deal_id,
                agent_name=reviewer.name,
                payload={
                    "reviewed_agent": current_output.agent_name,
                    "review_type": review_type.value,
                    "decision": review.decision.value,
                    "issue_count": len(review.issues),
                    "iteration": iteration,
                },
            )

            # Check if approved
            if review.approved:
                review.output = current_output
                logger.info(
                    f"Peer review approved after {iteration} iteration(s)"
                )
                return review

            # Check if needs escalation
            if review.decision == ReviewDecision.ESCALATE:
                logger.warning(
                    f"Peer review escalated after {iteration} iteration(s)"
                )
                return review

            # Check if rejected (no revision possible)
            if review.decision == ReviewDecision.REJECTED:
                logger.warning(
                    f"Peer review rejected: {review.notes}"
                )
                return review

            # Attempt revision if possible
            if review.needs_revision and hasattr(output, "agent"):
                try:
                    current_output = await self._request_revision(
                        original_output=current_output,
                        issues=review.issues,
                    )
                except Exception as e:
                    logger.error(f"Revision failed: {e}")
                    review.decision = ReviewDecision.ESCALATE
                    review.notes += f"\nRevision failed: {str(e)}"
                    return review
            else:
                # Can't revise, return current state
                review.output = current_output
                return review

        # Max iterations reached - escalate
        logger.warning(
            f"Max review iterations ({self.max_review_iterations}) reached, escalating"
        )
        final_review = ReviewResult(
            reviewed_agent=output.agent_name,
            reviewer_agent=reviewer.name,
            review_type=review_type,
            decision=ReviewDecision.ESCALATE,
            notes=f"Max review iterations ({self.max_review_iterations}) reached",
            output=current_output,
        )
        return final_review

    async def _perform_review(
        self,
        output: AgentOutput,
        reviewer: BaseAgent,
        review_type: ReviewType,
    ) -> ReviewResult:
        """
        Perform a single review iteration.

        Uses the reviewer's LLM to analyze the output if available,
        otherwise performs rule-based validation.
        """
        review = ReviewResult(
            reviewed_agent=output.agent_name,
            reviewer_agent=reviewer.name,
            review_type=review_type,
        )

        # Check for errors in output
        if output.errors:
            review.decision = ReviewDecision.NEEDS_REVISION
            for error in output.errors:
                review.issues.append(
                    ReviewIssue(
                        severity="high",
                        category="error",
                        description=error,
                    )
                )

        # Check if already flagged for review
        if output.requires_review:
            review.issues.append(
                ReviewIssue(
                    severity="medium",
                    category="confidence",
                    description="Output was flagged for human review by the agent",
                )
            )

        # Validate extractions
        extraction_issues = self._validate_extractions(output.extractions)
        review.issues.extend(extraction_issues)

        # Validate output data structure
        data_issues = self._validate_output_data(output.output_data)
        review.issues.extend(data_issues)

        # Perform LLM-based review if available
        if reviewer._client is not None:
            llm_issues = await self._llm_review(output, reviewer, review_type)
            review.issues.extend(llm_issues)

        # Determine final decision
        if not review.issues:
            review.decision = ReviewDecision.APPROVED
            review.confidence = 0.95
        else:
            critical_issues = [i for i in review.issues if i.severity == "critical"]
            high_issues = [i for i in review.issues if i.severity == "high"]

            if critical_issues:
                review.decision = ReviewDecision.REJECTED
                review.notes = f"Critical issues found: {len(critical_issues)}"
                review.confidence = 0.3
            elif high_issues:
                review.decision = ReviewDecision.NEEDS_REVISION
                review.notes = f"High severity issues require revision: {len(high_issues)}"
                review.confidence = 0.5
            else:
                # Medium/low issues - approve with notes
                review.decision = ReviewDecision.APPROVED
                review.notes = f"Minor issues noted: {len(review.issues)}"
                review.confidence = 0.8

        return review

    def _validate_extractions(
        self, extractions: list[dict]
    ) -> list[ReviewIssue]:
        """Validate extracted data for quality issues."""
        issues = []

        for i, extraction in enumerate(extractions):
            # Check for missing required fields
            if "type" not in extraction:
                issues.append(
                    ReviewIssue(
                        severity="medium",
                        category="missing_info",
                        description=f"Extraction {i} missing 'type' field",
                    )
                )

            # Check for low confidence
            confidence = extraction.get("confidence", 1.0)
            if confidence < 0.5:
                issues.append(
                    ReviewIssue(
                        severity="high",
                        category="confidence",
                        description=f"Extraction {i} has low confidence: {confidence}",
                        field_name=extraction.get("type", f"extraction_{i}"),
                    )
                )
            elif confidence < 0.7:
                issues.append(
                    ReviewIssue(
                        severity="medium",
                        category="confidence",
                        description=f"Extraction {i} has moderate confidence: {confidence}",
                        field_name=extraction.get("type", f"extraction_{i}"),
                    )
                )

        return issues

    def _validate_output_data(
        self, output_data: dict[str, Any]
    ) -> list[ReviewIssue]:
        """Validate output data structure."""
        issues = []

        if not output_data:
            issues.append(
                ReviewIssue(
                    severity="high",
                    category="missing_info",
                    description="Output data is empty",
                )
            )

        return issues

    async def _llm_review(
        self,
        output: AgentOutput,
        reviewer: BaseAgent,
        review_type: ReviewType,
    ) -> list[ReviewIssue]:
        """Perform LLM-based review of the output."""
        issues = []

        try:
            prompt = f"""Review this agent output for quality and correctness.

Agent: {output.agent_name}
Task ID: {output.task_id}
Success: {output.success}
Duration: {output.duration_seconds}s
Requires Review: {output.requires_review}

Output Data:
{output.output_data}

Extractions ({len(output.extractions)}):
{output.extractions[:5]}  # First 5 only

Errors: {output.errors}

Review Type: {review_type.value}

Identify any issues with the output. For each issue, specify:
- severity: "low", "medium", "high", or "critical"
- category: "data_quality", "calculation", "missing_info", "inconsistency", or "other"
- description: Clear description of the issue

Respond with JSON array of issues, or empty array if no issues:
[{{"severity": "...", "category": "...", "description": "..."}}]
"""

            response = reviewer.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system="You are a quality assurance reviewer. Identify issues concisely.",
                max_tokens=1024,
            )

            # Parse response
            content = response["content"]
            if content and len(content) > 0:
                text = content[0].text if hasattr(content[0], "text") else str(content[0])

                # Extract JSON array from response
                import json
                json_start = text.find("[")
                json_end = text.rfind("]") + 1
                if json_start >= 0 and json_end > json_start:
                    parsed_issues = json.loads(text[json_start:json_end])
                    for item in parsed_issues:
                        issues.append(
                            ReviewIssue(
                                severity=item.get("severity", "medium"),
                                category=item.get("category", "other"),
                                description=item.get("description", ""),
                            )
                        )

        except Exception as e:
            logger.warning(f"LLM review failed: {e}")
            # Continue without LLM review

        return issues

    async def _request_revision(
        self,
        original_output: AgentOutput,
        issues: list[ReviewIssue],
    ) -> AgentOutput:
        """
        Request revision from the original agent.

        Note: This is a placeholder - actual revision would require
        the original agent instance and re-execution capability.
        """
        logger.warning(
            f"Revision requested for {original_output.agent_name} "
            f"with {len(issues)} issues. "
            "Automatic revision not yet implemented."
        )

        # For now, just mark the output as requiring review
        original_output.requires_review = True

        return original_output

    async def quick_validate(
        self,
        output: AgentOutput,
        deal_id: Optional[UUID] = None,
    ) -> ReviewResult:
        """
        Perform quick rule-based validation without a reviewer agent.

        Useful for basic quality checks before stage transitions.
        """
        review = ReviewResult(
            reviewed_agent=output.agent_name,
            reviewer_agent="system",
            review_type=ReviewType.VALIDATION,
        )

        # Check for errors
        if output.errors:
            for error in output.errors:
                review.issues.append(
                    ReviewIssue(
                        severity="high",
                        category="error",
                        description=error,
                    )
                )

        # Check output is not empty
        if not output.output_data:
            review.issues.append(
                ReviewIssue(
                    severity="high",
                    category="missing_info",
                    description="Output data is empty",
                )
            )

        # Validate extractions
        review.issues.extend(self._validate_extractions(output.extractions))

        # Determine decision
        if not review.issues:
            review.decision = ReviewDecision.APPROVED
        elif any(i.severity == "critical" for i in review.issues):
            review.decision = ReviewDecision.REJECTED
        elif any(i.severity == "high" for i in review.issues):
            review.decision = ReviewDecision.NEEDS_REVISION
        else:
            review.decision = ReviewDecision.APPROVED

        # Publish event
        await self.event_bus.publish(
            event_type=EventType.AGENT_TASK_COMPLETED,
            deal_id=deal_id,
            agent_name="PeerReviewService",
            payload={
                "reviewed_agent": output.agent_name,
                "decision": review.decision.value,
                "issue_count": len(review.issues),
            },
        )

        return review


# Singleton instance
_peer_review_service: Optional[PeerReviewService] = None


def get_peer_review_service() -> PeerReviewService:
    """Get the global peer review service instance."""
    global _peer_review_service
    if _peer_review_service is None:
        _peer_review_service = PeerReviewService()
    return _peer_review_service
