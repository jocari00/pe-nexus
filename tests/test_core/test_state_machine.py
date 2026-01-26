"""Tests for the Deal Pipeline State Machine."""

import pytest
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.state_machine import (
    DealStateMachine,
    TransitionError,
    get_state_machine,
    DEAL_TRANSITIONS,
    TRANSITION_EVENTS,
)
from src.schemas.deal import DealStage, MasterDeal, TargetCompany, IndustryClassification


@pytest.fixture
def state_machine():
    """Create a fresh state machine for each test."""
    return DealStateMachine()


@pytest.fixture
def sample_deal():
    """Create a sample deal for testing."""
    return MasterDeal(
        deal_name="Test Acquisition",
        stage=DealStage.SOURCING,
        target=TargetCompany(
            name="Test Corp",
            headquarters="Test City",
            industry=IndustryClassification(
                sector="Technology",
                sub_sector="Software",
            ),
        ),
    )


class TestTransitionValidation:
    """Test transition validation logic."""

    def test_can_transition_sourcing_to_triage(self, state_machine):
        """Test SOURCING -> TRIAGE is valid."""
        assert state_machine.can_transition(DealStage.SOURCING, DealStage.TRIAGE)

    def test_can_transition_sourcing_to_rejected(self, state_machine):
        """Test SOURCING -> REJECTED is valid."""
        assert state_machine.can_transition(DealStage.SOURCING, DealStage.REJECTED)

    def test_cannot_transition_sourcing_to_closing(self, state_machine):
        """Test SOURCING -> CLOSING is invalid (skipping stages)."""
        assert not state_machine.can_transition(DealStage.SOURCING, DealStage.CLOSING)

    def test_cannot_transition_from_exited(self, state_machine):
        """Test EXITED is terminal - no transitions allowed."""
        assert not state_machine.can_transition(DealStage.EXITED, DealStage.SOURCING)
        assert not state_machine.can_transition(DealStage.EXITED, DealStage.PORTFOLIO)

    def test_cannot_transition_from_rejected(self, state_machine):
        """Test REJECTED is terminal - no transitions allowed."""
        assert not state_machine.can_transition(DealStage.REJECTED, DealStage.SOURCING)
        assert not state_machine.can_transition(DealStage.REJECTED, DealStage.TRIAGE)

    def test_all_stages_can_reject(self, state_machine):
        """Test all non-terminal stages can transition to REJECTED."""
        non_terminal_stages = [
            DealStage.SOURCING,
            DealStage.TRIAGE,
            DealStage.DILIGENCE,
            DealStage.IC_REVIEW,
            DealStage.CLOSING,
        ]
        for stage in non_terminal_stages:
            assert state_machine.can_transition(stage, DealStage.REJECTED)


class TestGetValidTransitions:
    """Test getting valid transitions from a stage."""

    def test_sourcing_valid_transitions(self, state_machine):
        """Test valid transitions from SOURCING."""
        valid = state_machine.get_valid_transitions(DealStage.SOURCING)
        assert DealStage.TRIAGE in valid
        assert DealStage.REJECTED in valid
        assert len(valid) == 2

    def test_portfolio_valid_transitions(self, state_machine):
        """Test valid transitions from PORTFOLIO."""
        valid = state_machine.get_valid_transitions(DealStage.PORTFOLIO)
        assert DealStage.EXITED in valid
        assert len(valid) == 1

    def test_exited_no_valid_transitions(self, state_machine):
        """Test EXITED has no valid transitions."""
        valid = state_machine.get_valid_transitions(DealStage.EXITED)
        assert len(valid) == 0


class TestDealTransition:
    """Test executing deal transitions."""

    def test_transition_updates_stage(self, state_machine, sample_deal):
        """Test successful transition updates deal stage."""
        updated_deal = state_machine.transition(
            deal=sample_deal,
            to_stage=DealStage.TRIAGE,
            transitioned_by="test_user",
            reason="Deal meets criteria",
        )

        assert updated_deal.stage == DealStage.TRIAGE

    def test_transition_adds_to_history(self, state_machine, sample_deal):
        """Test transition adds record to state history."""
        original_history_len = len(sample_deal.state_history)

        state_machine.transition(
            deal=sample_deal,
            to_stage=DealStage.TRIAGE,
            transitioned_by="test_user",
            reason="Test reason",
        )

        assert len(sample_deal.state_history) == original_history_len + 1

        latest = sample_deal.state_history[-1]
        assert latest.from_stage == DealStage.SOURCING
        assert latest.to_stage == DealStage.TRIAGE
        assert latest.transitioned_by == "test_user"
        assert latest.reason == "Test reason"

    def test_transition_updates_timestamp(self, state_machine, sample_deal):
        """Test transition updates the updated_at timestamp."""
        original_updated = sample_deal.updated_at

        state_machine.transition(
            deal=sample_deal,
            to_stage=DealStage.TRIAGE,
            transitioned_by="test_user",
        )

        assert sample_deal.updated_at >= original_updated

    def test_invalid_transition_raises_error(self, state_machine, sample_deal):
        """Test invalid transition raises TransitionError."""
        with pytest.raises(TransitionError) as exc_info:
            state_machine.transition(
                deal=sample_deal,
                to_stage=DealStage.CLOSING,  # Can't skip stages
                transitioned_by="test_user",
            )

        assert exc_info.value.from_stage == DealStage.SOURCING
        assert exc_info.value.to_stage == DealStage.CLOSING

    def test_full_pipeline_transition(self, state_machine, sample_deal):
        """Test transitioning through full pipeline."""
        stages = [
            DealStage.TRIAGE,
            DealStage.DILIGENCE,
            DealStage.IC_REVIEW,
            DealStage.CLOSING,
            DealStage.PORTFOLIO,
            DealStage.EXITED,
        ]

        for stage in stages:
            state_machine.transition(
                deal=sample_deal,
                to_stage=stage,
                transitioned_by="test_user",
            )
            assert sample_deal.stage == stage

        assert len(sample_deal.state_history) == 6


class TestTransitionHooks:
    """Test pre and post transition hooks."""

    def test_pre_hook_blocks_transition(self, state_machine, sample_deal):
        """Test pre-hook returning False blocks transition."""
        def blocking_hook(deal, from_stage, to_stage):
            return False

        state_machine.add_pre_hook(DealStage.SOURCING, DealStage.TRIAGE, blocking_hook)

        with pytest.raises(TransitionError) as exc_info:
            state_machine.transition(
                deal=sample_deal,
                to_stage=DealStage.TRIAGE,
                transitioned_by="test_user",
            )

        assert "hook validation failed" in str(exc_info.value).lower()

    def test_pre_hook_allows_transition(self, state_machine, sample_deal):
        """Test pre-hook returning True allows transition."""
        hook_called = []

        def allowing_hook(deal, from_stage, to_stage):
            hook_called.append(True)
            return True

        state_machine.add_pre_hook(DealStage.SOURCING, DealStage.TRIAGE, allowing_hook)

        state_machine.transition(
            deal=sample_deal,
            to_stage=DealStage.TRIAGE,
            transitioned_by="test_user",
        )

        assert len(hook_called) == 1
        assert sample_deal.stage == DealStage.TRIAGE

    def test_post_hook_executed(self, state_machine, sample_deal):
        """Test post-hook is executed after transition."""
        post_hook_data = []

        def post_hook(deal, from_stage, to_stage):
            post_hook_data.append({
                "deal_stage": deal.stage,
                "from": from_stage,
                "to": to_stage,
            })
            return True

        state_machine.add_post_hook(DealStage.SOURCING, DealStage.TRIAGE, post_hook)

        state_machine.transition(
            deal=sample_deal,
            to_stage=DealStage.TRIAGE,
            transitioned_by="test_user",
        )

        assert len(post_hook_data) == 1
        assert post_hook_data[0]["to"] == DealStage.TRIAGE

    def test_global_hook_called_for_all_transitions(self, state_machine, sample_deal):
        """Test global hooks are called for all transitions."""
        global_hook_calls = []

        def global_hook(deal, from_stage, to_stage):
            global_hook_calls.append((from_stage, to_stage))
            return True

        state_machine.add_pre_hook(None, None, global_hook)

        state_machine.transition(sample_deal, DealStage.TRIAGE, "user")
        state_machine.transition(sample_deal, DealStage.DILIGENCE, "user")

        assert len(global_hook_calls) == 2


class TestTransitionEvents:
    """Test transition event mapping."""

    def test_get_transition_event(self, state_machine):
        """Test getting correct event for stage."""
        from src.schemas.events import EventType

        assert state_machine.get_transition_event(DealStage.TRIAGE) == EventType.DEAL_TRIAGED
        assert state_machine.get_transition_event(DealStage.REJECTED) == EventType.DEAL_REJECTED
        assert state_machine.get_transition_event(DealStage.CLOSING) == EventType.DEAL_APPROVED


class TestStageRequirements:
    """Test stage exit requirements."""

    def test_get_sourcing_requirements(self, state_machine):
        """Test getting requirements to exit SOURCING."""
        requirements = state_machine.get_stage_requirements(DealStage.SOURCING)

        assert DealStage.TRIAGE in requirements
        assert DealStage.REJECTED in requirements
        assert isinstance(requirements[DealStage.TRIAGE], list)

    def test_validate_exit_requirements(self, state_machine, sample_deal):
        """Test validating exit requirements."""
        is_valid, missing = state_machine.validate_exit_requirements(
            sample_deal,
            DealStage.TRIAGE
        )

        # Sample deal should be missing documents
        if not sample_deal.documents:
            assert "document" in str(missing).lower() or len(missing) > 0


class TestGlobalStateMachine:
    """Test global state machine singleton."""

    def test_get_state_machine_returns_same_instance(self):
        """Test get_state_machine returns same instance."""
        sm1 = get_state_machine()
        sm2 = get_state_machine()

        assert sm1 is sm2

    def test_global_state_machine_is_functional(self):
        """Test global state machine can perform transitions."""
        sm = get_state_machine()
        assert sm.can_transition(DealStage.SOURCING, DealStage.TRIAGE)
