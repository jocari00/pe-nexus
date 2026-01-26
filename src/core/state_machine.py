"""Deal Pipeline State Machine for managing deal stage transitions."""

import logging
import threading
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID

from src.schemas.deal import DealStage, MasterDeal, StateTransition
from src.schemas.events import EventType

logger = logging.getLogger(__name__)

# Valid state transitions
DEAL_TRANSITIONS: dict[DealStage, list[DealStage]] = {
    DealStage.SOURCING: [DealStage.TRIAGE, DealStage.REJECTED],
    DealStage.TRIAGE: [DealStage.DILIGENCE, DealStage.REJECTED],
    DealStage.DILIGENCE: [DealStage.IC_REVIEW, DealStage.REJECTED],
    DealStage.IC_REVIEW: [DealStage.CLOSING, DealStage.REJECTED],
    DealStage.CLOSING: [DealStage.PORTFOLIO, DealStage.REJECTED],
    DealStage.PORTFOLIO: [DealStage.EXITED],
    DealStage.EXITED: [],  # Terminal state
    DealStage.REJECTED: [],  # Terminal state
}

# Event types emitted on state transitions
TRANSITION_EVENTS: dict[DealStage, EventType] = {
    DealStage.SOURCING: EventType.DEAL_CREATED,
    DealStage.TRIAGE: EventType.DEAL_TRIAGED,
    DealStage.DILIGENCE: EventType.DEAL_DILIGENCE_STARTED,
    DealStage.IC_REVIEW: EventType.DEAL_IC_SUBMITTED,
    DealStage.CLOSING: EventType.DEAL_APPROVED,
    DealStage.PORTFOLIO: EventType.DEAL_CLOSED,
    DealStage.EXITED: EventType.DEAL_EXITED,
    DealStage.REJECTED: EventType.DEAL_REJECTED,
}

# Type for transition hooks
TransitionHook = Callable[[MasterDeal, DealStage, DealStage], bool]


class TransitionError(Exception):
    """Raised when a state transition is invalid."""

    def __init__(self, from_stage: DealStage, to_stage: DealStage, reason: str = ""):
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.reason = reason
        message = f"Invalid transition from {from_stage.value} to {to_stage.value}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class DealStateMachine:
    """
    Finite State Machine for deal pipeline management.

    Features:
    - Validates state transitions
    - Executes pre/post transition hooks
    - Records transition history
    - Integrates with event bus for notifications
    """

    def __init__(self):
        self._pre_hooks: dict[tuple[DealStage, DealStage], list[TransitionHook]] = {}
        self._post_hooks: dict[tuple[DealStage, DealStage], list[TransitionHook]] = {}
        self._global_pre_hooks: list[TransitionHook] = []
        self._global_post_hooks: list[TransitionHook] = []

    def can_transition(self, from_stage: DealStage, to_stage: DealStage) -> bool:
        """Check if a transition is valid."""
        valid_targets = DEAL_TRANSITIONS.get(from_stage, [])
        return to_stage in valid_targets

    def get_valid_transitions(self, stage: DealStage) -> list[DealStage]:
        """Get list of valid next stages from current stage."""
        return DEAL_TRANSITIONS.get(stage, [])

    def transition(
        self,
        deal: MasterDeal,
        to_stage: DealStage,
        transitioned_by: str,
        reason: str = "",
        metadata: Optional[dict] = None,
    ) -> MasterDeal:
        """
        Transition a deal to a new stage.

        Args:
            deal: The deal to transition
            to_stage: Target stage
            transitioned_by: User or agent making the transition
            reason: Reason for transition
            metadata: Additional transition metadata

        Returns:
            Updated deal with new stage

        Raises:
            TransitionError: If transition is invalid
        """
        from_stage = deal.stage

        # Validate transition
        if not self.can_transition(from_stage, to_stage):
            raise TransitionError(
                from_stage,
                to_stage,
                f"Valid transitions from {from_stage.value}: "
                f"{[s.value for s in self.get_valid_transitions(from_stage)]}",
            )

        # Execute pre-hooks
        if not self._execute_hooks(
            deal, from_stage, to_stage, is_pre=True
        ):
            raise TransitionError(
                from_stage,
                to_stage,
                "Pre-transition hook validation failed",
            )

        # Create transition record
        transition = StateTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_at=datetime.now(timezone.utc),
            transitioned_by=transitioned_by,
            reason=reason,
            metadata=metadata or {},
        )

        # Update deal using model_copy to ensure validation runs
        # and avoid direct mutation of Pydantic model
        new_state_history = list(deal.state_history) + [transition]
        deal = deal.model_copy(
            update={
                "stage": to_stage,
                "state_history": new_state_history,
                "updated_at": datetime.now(timezone.utc),
            }
        )

        # Execute post-hooks
        self._execute_hooks(deal, from_stage, to_stage, is_pre=False)

        logger.info(
            f"Deal {deal.deal_id} transitioned from "
            f"{from_stage.value} to {to_stage.value} by {transitioned_by}"
        )

        return deal

    def _execute_hooks(
        self,
        deal: MasterDeal,
        from_stage: DealStage,
        to_stage: DealStage,
        is_pre: bool,
    ) -> bool:
        """Execute transition hooks."""
        hooks_dict = self._pre_hooks if is_pre else self._post_hooks
        global_hooks = self._global_pre_hooks if is_pre else self._global_post_hooks

        # Get specific hooks for this transition
        specific_hooks = hooks_dict.get((from_stage, to_stage), [])

        # Execute global hooks first
        for hook in global_hooks:
            try:
                if not hook(deal, from_stage, to_stage):
                    return False
            except Exception as e:
                logger.error(f"Hook error: {e}")
                return False

        # Execute specific hooks
        for hook in specific_hooks:
            try:
                if not hook(deal, from_stage, to_stage):
                    return False
            except Exception as e:
                logger.error(f"Hook error: {e}")
                return False

        return True

    def add_pre_hook(
        self,
        from_stage: Optional[DealStage],
        to_stage: Optional[DealStage],
        hook: TransitionHook,
    ) -> None:
        """
        Add a pre-transition hook.

        If from_stage and to_stage are None, hook is global.
        """
        if from_stage is None or to_stage is None:
            self._global_pre_hooks.append(hook)
        else:
            key = (from_stage, to_stage)
            if key not in self._pre_hooks:
                self._pre_hooks[key] = []
            self._pre_hooks[key].append(hook)

    def add_post_hook(
        self,
        from_stage: Optional[DealStage],
        to_stage: Optional[DealStage],
        hook: TransitionHook,
    ) -> None:
        """
        Add a post-transition hook.

        If from_stage and to_stage are None, hook is global.
        """
        if from_stage is None or to_stage is None:
            self._global_post_hooks.append(hook)
        else:
            key = (from_stage, to_stage)
            if key not in self._post_hooks:
                self._post_hooks[key] = []
            self._post_hooks[key].append(hook)

    def get_transition_event(self, to_stage: DealStage) -> EventType:
        """Get the event type for a transition to a stage."""
        return TRANSITION_EVENTS.get(to_stage, EventType.DEAL_UPDATED)

    def get_stage_requirements(self, stage: DealStage) -> dict:
        """
        Get requirements that must be met to exit a stage.

        Returns a dict describing what's needed for each valid transition.
        """
        requirements = {
            DealStage.SOURCING: {
                DealStage.TRIAGE: [
                    "Basic company information captured",
                    "Initial deal score computed",
                    "At least one document uploaded",
                ],
                DealStage.REJECTED: ["Rejection reason documented"],
            },
            DealStage.TRIAGE: {
                DealStage.DILIGENCE: [
                    "Financial data extracted and validated",
                    "Initial valuation range established",
                    "Deal team assigned",
                ],
                DealStage.REJECTED: ["Rejection reason documented"],
            },
            DealStage.DILIGENCE: {
                DealStage.IC_REVIEW: [
                    "Diligence checklist complete",
                    "Legal review complete",
                    "Financial model built",
                    "Investment memo drafted",
                ],
                DealStage.REJECTED: ["Rejection reason documented"],
            },
            DealStage.IC_REVIEW: {
                DealStage.CLOSING: [
                    "IC approval obtained",
                    "Terms agreed",
                ],
                DealStage.REJECTED: ["IC rejection documented"],
            },
            DealStage.CLOSING: {
                DealStage.PORTFOLIO: [
                    "Legal documents executed",
                    "Funding complete",
                ],
                DealStage.REJECTED: ["Deal termination documented"],
            },
            DealStage.PORTFOLIO: {
                DealStage.EXITED: [
                    "Exit transaction complete",
                    "Final returns calculated",
                ],
            },
        }

        return requirements.get(stage, {})

    def validate_exit_requirements(
        self,
        deal: MasterDeal,
        to_stage: DealStage,
    ) -> tuple[bool, list[str]]:
        """
        Validate that a deal meets requirements to transition.

        Returns (is_valid, list_of_missing_requirements).
        """
        requirements = self.get_stage_requirements(deal.stage)
        stage_requirements = requirements.get(to_stage, [])

        missing = []

        # Basic validation logic based on stage
        if to_stage == DealStage.TRIAGE:
            if not deal.target.name:
                missing.append("Target company name required")
            if not deal.documents:
                missing.append("At least one document required")

        elif to_stage == DealStage.DILIGENCE:
            if not deal.financials:
                missing.append("Financial data required")
            if not deal.deal_team:
                missing.append("Deal team must be assigned")

        elif to_stage == DealStage.IC_REVIEW:
            if not deal.investment_memo:
                missing.append("Investment memo required")
            checklist = deal.diligence_checklist
            if checklist.overall_progress < 0.8:
                missing.append("Diligence checklist must be at least 80% complete")

        elif to_stage == DealStage.CLOSING:
            if not deal.ic_decision:
                missing.append("IC decision required")
            elif deal.ic_decision.decision != "APPROVED":
                missing.append("IC approval required")

        elif to_stage == DealStage.PORTFOLIO:
            # Closing requirements would be validated here
            pass

        return (len(missing) == 0, missing)


# Global state machine instance
_state_machine: Optional[DealStateMachine] = None
_state_machine_lock = threading.Lock()


def get_state_machine() -> DealStateMachine:
    """Get or create the global state machine instance (thread-safe)."""
    global _state_machine
    if _state_machine is None:
        with _state_machine_lock:
            # Double-check locking pattern
            if _state_machine is None:
                _state_machine = DealStateMachine()
    return _state_machine
