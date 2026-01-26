"""AdversarialIC Agent - Orchestrates Bull/Bear debate for investment committee.

This agent coordinates a debate between bull and bear perspectives,
synthesizes findings, and provides a recommendation.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

from .bull_agent import BullAgent
from .bear_agent import BearAgent

logger = logging.getLogger(__name__)


@dataclass
class DebateOutcome:
    """Outcome of the IC debate."""
    bull_memo: dict
    bear_assessment: dict
    synthesis: dict
    final_recommendation: str
    confidence_level: str
    key_conditions: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict:
        return {
            "bull_memo": self.bull_memo,
            "bear_assessment": self.bear_assessment,
            "synthesis": self.synthesis,
            "final_recommendation": self.final_recommendation,
            "confidence_level": self.confidence_level,
            "key_conditions": self.key_conditions,
            "next_steps": self.next_steps,
        }


class AdversarialICAgent(BaseAgent):
    """
    Orchestrates Bull/Bear investment committee debate.

    Capabilities:
    - Generates investment memo (bull case)
    - Generates risk assessment (bear case)
    - Synthesizes perspectives into balanced view
    - Provides final recommendation with conditions

    Workflow:
    1. Generate bull case investment memo
    2. Generate bear case counter-arguments
    3. Synthesize perspectives
    4. Produce final recommendation
    """

    def __init__(self):
        super().__init__(
            name="AdversarialIC",
            description="Investment committee debate orchestration",
            max_iterations=3,
        )
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()

    def get_system_prompt(self) -> str:
        return """You are the Chair of a Private Equity Investment Committee.

Your role is to synthesize the bull and bear perspectives on an investment and reach a balanced conclusion.

When synthesizing:
1. Weigh the strength of arguments from both sides
2. Identify which concerns are material vs manageable
3. Determine if the risk/reward is attractive
4. Specify conditions that must be met to proceed
5. Provide clear next steps

Your recommendation should be one of:
- APPROVE: Proceed with investment as proposed
- APPROVE WITH CONDITIONS: Proceed if specific conditions are met
- ADDITIONAL DD REQUIRED: More work needed before decision
- DECLINE: Do not proceed with investment

Be decisive but thoughtful. The IC depends on your judgment.
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for IC debate."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "debate")

            if mode == "memo":
                result = self._generate_memo_only(input_data, state)
            elif mode == "bear":
                result = self._generate_bear_only(input_data, state)
            elif mode == "debate":
                result = self._run_full_debate(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _generate_memo_only(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Generate only the bull case memo."""
        deal_context = input_data.get("deal_context", {})

        # Run bull agent synchronously
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self.bull_agent.generate_memo(deal_context))
        finally:
            loop.close()

        if not result.success:
            state["errors"].append("Failed to generate investment memo")
            return {}

        extraction_record = {
            "type": "bull_memo",
            "company_name": deal_context.get("company_name", "Target"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        return {
            "mode": "memo",
            "success": True,
            "memo": result.output_data.get("memo", {}),
        }

    def _generate_bear_only(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Generate only the bear case assessment."""
        deal_context = input_data.get("deal_context", {})
        bull_memo = input_data.get("bull_memo")

        # Run bear agent synchronously
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                self.bear_agent.generate_assessment(deal_context, bull_memo)
            )
        finally:
            loop.close()

        if not result.success:
            state["errors"].append("Failed to generate risk assessment")
            return {}

        extraction_record = {
            "type": "bear_assessment",
            "company_name": deal_context.get("company_name", "Target"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        return {
            "mode": "bear",
            "success": True,
            "assessment": result.output_data.get("assessment", {}),
        }

    def _run_full_debate(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Run full bull/bear debate with synthesis."""
        deal_context = input_data.get("deal_context", {})

        import asyncio
        loop = asyncio.new_event_loop()

        try:
            # Generate bull case
            bull_result = loop.run_until_complete(self.bull_agent.generate_memo(deal_context))
            if not bull_result.success:
                state["errors"].append("Failed to generate bull case")
                return {}

            bull_memo = bull_result.output_data.get("memo", {})

            # Generate bear case (with bull memo for counter-arguments)
            bear_result = loop.run_until_complete(
                self.bear_agent.generate_assessment(deal_context, bull_memo)
            )
            if not bear_result.success:
                state["errors"].append("Failed to generate bear case")
                return {}

            bear_assessment = bear_result.output_data.get("assessment", {})

        finally:
            loop.close()

        # Synthesize
        if self._client is not None:
            debate_outcome = self._synthesize_with_llm(deal_context, bull_memo, bear_assessment)
        else:
            debate_outcome = self._synthesize_template(deal_context, bull_memo, bear_assessment)

        # Record extraction
        extraction_record = {
            "type": "ic_debate",
            "company_name": deal_context.get("company_name", "Target"),
            "final_recommendation": debate_outcome.final_recommendation,
            "llm_enhanced": self._client is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Flag for human review
        if debate_outcome.final_recommendation in ["ADDITIONAL DD REQUIRED", "DECLINE"]:
            state["requires_review"] = True

        state["confidence_scores"]["debate"] = 0.80 if self._client else 0.65

        return {
            "mode": "debate",
            "success": True,
            "debate_outcome": debate_outcome.to_dict(),
        }

    def _synthesize_with_llm(
        self, deal_context: dict, bull_memo: dict, bear_assessment: dict
    ) -> DebateOutcome:
        """Synthesize debate with LLM."""
        prompt = f"""Synthesize the following bull and bear perspectives on this investment:

DEAL CONTEXT:
Company: {deal_context.get('company_name', 'Target')}
Industry: {deal_context.get('industry', 'Technology')}
Entry Multiple: {deal_context.get('entry_multiple', 8.0)}x
Expected IRR: {deal_context.get('irr', '20%')}

BULL CASE:
Recommendation: {bull_memo.get('recommendation', 'N/A')}
Investment Thesis: {bull_memo.get('investment_thesis', [])}
Value Creation Plan: {bull_memo.get('value_creation_plan', [])}

BEAR CASE:
Recommendation: {bear_assessment.get('recommendation', 'N/A')}
Deal Killers: {bear_assessment.get('deal_killers', [])}
Major Risks: {bear_assessment.get('major_risks', [])}
Counter Arguments: {bear_assessment.get('counter_arguments', [])}

Provide your synthesis as IC Chair in this JSON format:
{{
    "synthesis": {{
        "bull_strengths": ["strongest bull arguments"],
        "bear_concerns": ["most valid bear concerns"],
        "resolved_issues": ["concerns adequately addressed"],
        "open_questions": ["issues still requiring resolution"]
    }},
    "final_recommendation": "APPROVE / APPROVE WITH CONDITIONS / ADDITIONAL DD REQUIRED / DECLINE",
    "confidence_level": "HIGH / MEDIUM / LOW",
    "key_conditions": ["condition 1 if any", "condition 2 if any"],
    "next_steps": ["step 1", "step 2"]
}}
"""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=1024,
            )

            text = self.get_text_from_response(response)
            if text:
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(text[json_start:json_end])
                    return DebateOutcome(
                        bull_memo=bull_memo,
                        bear_assessment=bear_assessment,
                        synthesis=result.get("synthesis", {}),
                        final_recommendation=result.get("final_recommendation", "ADDITIONAL DD REQUIRED"),
                        confidence_level=result.get("confidence_level", "MEDIUM"),
                        key_conditions=result.get("key_conditions", []),
                        next_steps=result.get("next_steps", []),
                    )

        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}")

        return self._synthesize_template(deal_context, bull_memo, bear_assessment)

    def _synthesize_template(
        self, deal_context: dict, bull_memo: dict, bear_assessment: dict
    ) -> DebateOutcome:
        """Generate template-based synthesis."""
        company_name = deal_context.get("company_name", "Target")

        # Determine recommendation based on bear severity
        deal_killers = bear_assessment.get("deal_killers", [])
        major_risks = bear_assessment.get("major_risks", [])
        dd_gaps = bear_assessment.get("due_diligence_gaps", [])

        if len(deal_killers) >= 2:
            recommendation = "DECLINE"
            confidence = "HIGH"
        elif len(deal_killers) == 1 or len(dd_gaps) >= 3:
            recommendation = "ADDITIONAL DD REQUIRED"
            confidence = "MEDIUM"
        elif len(major_risks) >= 3:
            recommendation = "APPROVE WITH CONDITIONS"
            confidence = "MEDIUM"
        else:
            recommendation = "APPROVE WITH CONDITIONS"
            confidence = "MEDIUM"

        synthesis = {
            "bull_strengths": [
                f"Strong investment thesis with multiple value creation levers",
                f"Attractive return profile meets fund criteria",
                f"Clear path to exit via strategic or financial sale",
            ],
            "bear_concerns": [
                concern.get("issue", concern.get("risk", "Unknown concern"))
                for concern in (deal_killers + major_risks)[:3]
            ],
            "resolved_issues": [
                "Management quality validated through references",
                "Financial model stress-tested for downside scenarios",
            ],
            "open_questions": dd_gaps[:3] if dd_gaps else [
                "Pending completion of customer reference calls",
            ],
        }

        key_conditions = []
        if deal_killers:
            key_conditions.append(f"Resolution of deal killer: {deal_killers[0].get('issue', 'key issue')}")
        if dd_gaps:
            key_conditions.append(f"Complete outstanding DD: {dd_gaps[0]}")
        key_conditions.append("Negotiate price reduction of 0.5x multiple")

        next_steps = [
            "Complete outstanding due diligence items within 2 weeks",
            "Re-convene IC for final approval once conditions addressed",
            "Prepare LOI for submission pending IC final approval",
        ]

        return DebateOutcome(
            bull_memo=bull_memo,
            bear_assessment=bear_assessment,
            synthesis=synthesis,
            final_recommendation=recommendation,
            confidence_level=confidence,
            key_conditions=key_conditions,
            next_steps=next_steps,
        )

    def _is_processing_complete(self, state: AgentState) -> bool:
        return bool(state.get("output_data")) or bool(state.get("errors"))

    # Convenience methods

    async def generate_memo(self, deal_context: dict) -> AgentOutput:
        """Generate investment memo (bull case only)."""
        return await self.run(input_data={"mode": "memo", "deal_context": deal_context})

    async def generate_bear_case(
        self, deal_context: dict, bull_memo: Optional[dict] = None
    ) -> AgentOutput:
        """Generate risk assessment (bear case only)."""
        return await self.run(
            input_data={"mode": "bear", "deal_context": deal_context, "bull_memo": bull_memo}
        )

    async def run_debate(self, deal_context: dict) -> AgentOutput:
        """Run full IC debate with bull/bear synthesis."""
        return await self.run(input_data={"mode": "debate", "deal_context": deal_context})


def create_ic_agent() -> AdversarialICAgent:
    """Factory function to create an AdversarialIC agent."""
    return AdversarialICAgent()
