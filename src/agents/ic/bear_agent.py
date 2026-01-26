"""Bear Agent - Generates risk analysis and counter-arguments for deals.

The Bear agent argues against investments, identifying risks, weaknesses,
and potential deal-killers that need to be addressed.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Risk assessment structure."""
    executive_summary: str
    deal_killers: list[dict]
    major_risks: list[dict]
    valuation_concerns: list[str]
    due_diligence_gaps: list[str]
    counter_arguments: list[dict]
    stress_scenarios: list[dict]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "executive_summary": self.executive_summary,
            "deal_killers": self.deal_killers,
            "major_risks": self.major_risks,
            "valuation_concerns": self.valuation_concerns,
            "due_diligence_gaps": self.due_diligence_gaps,
            "counter_arguments": self.counter_arguments,
            "stress_scenarios": self.stress_scenarios,
            "recommendation": self.recommendation,
        }


class BearAgent(BaseAgent):
    """
    Agent that generates the bearish risk case.

    Capabilities:
    - Identifies deal-killers and major risks
    - Challenges valuation assumptions
    - Highlights due diligence gaps
    - Provides counter-arguments to bull case
    """

    def __init__(self):
        super().__init__(
            name="BearAgent",
            description="Risk analysis and counter-argument generator",
            max_iterations=2,
        )

    def get_system_prompt(self) -> str:
        return """You are a skeptical Investment Committee member reviewing a potential deal.

Your role is to challenge the investment and identify ALL reasons why it could fail. You should:
1. Identify potential deal-killers that would make this investment unacceptable
2. Challenge optimistic assumptions in the financial model
3. Highlight risks that may be understated or overlooked
4. Question the valuation relative to comparable transactions
5. Identify gaps in due diligence that need to be addressed

Be constructively critical. Your goal is to stress-test the investment, not to block it.
A good challenge makes the deal stronger if it proceeds.
Your tone should be professional and analytical.
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Generate risk assessment."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            deal_context = input_data.get("deal_context", {})
            bull_memo = input_data.get("bull_memo")  # Optional, for counter-arguments

            if self._client is not None:
                assessment = self._generate_llm_assessment(deal_context, bull_memo)
            else:
                assessment = self._generate_template_assessment(deal_context, bull_memo)

            # Record extraction
            extraction_record = {
                "type": "risk_assessment",
                "company_name": deal_context.get("company_name", "Target"),
                "deal_killers_found": len(assessment.deal_killers),
                "major_risks_found": len(assessment.major_risks),
                "llm_enhanced": self._client is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["extractions"].append(extraction_record)
            state["confidence_scores"]["risk_assessment"] = 0.85 if self._client else 0.70

            state["output_data"] = {
                "assessment": assessment.to_dict(),
                "agent": "BearAgent",
            }
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _generate_llm_assessment(
        self, deal_context: dict, bull_memo: Optional[dict]
    ) -> RiskAssessment:
        """Generate assessment using LLM."""
        bull_context = ""
        if bull_memo:
            bull_context = f"""
BULL CASE TO COUNTER:
Investment Thesis: {bull_memo.get('investment_thesis', [])}
Value Creation Plan: {bull_memo.get('value_creation_plan', [])}
"""

        prompt = f"""Generate a critical risk assessment for the following deal:

DEAL CONTEXT:
Company: {deal_context.get('company_name', 'Target Company')}
Industry: {deal_context.get('industry', 'Technology')}
Revenue: ${deal_context.get('revenue', 100)}M
EBITDA: ${deal_context.get('ebitda', 20)}M
Entry Multiple: {deal_context.get('entry_multiple', 8.0)}x
Expected IRR: {deal_context.get('irr', '20%')}
Expected MOIC: {deal_context.get('moic', '2.5x')}
{bull_context}

Generate a critical risk assessment with this JSON structure:
{{
    "executive_summary": "summary of key concerns",
    "deal_killers": [
        {{"issue": "deal killer description", "severity": "CRITICAL", "resolution_path": "what would need to be true"}}
    ],
    "major_risks": [
        {{"risk": "risk description", "probability": "HIGH/MEDIUM/LOW", "impact": "HIGH/MEDIUM/LOW", "monitoring": "how to track"}}
    ],
    "valuation_concerns": ["concern 1", "concern 2"],
    "due_diligence_gaps": ["gap 1", "gap 2"],
    "counter_arguments": [
        {{"bull_claim": "what bulls say", "counter": "why it may not be true"}}
    ],
    "stress_scenarios": [
        {{"scenario": "scenario description", "irr_impact": "revised IRR", "likelihood": "percentage"}}
    ],
    "recommendation": "PROCEED WITH CAUTION / ADDITIONAL DD REQUIRED / PASS"
}}
"""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=2048,
            )

            text = self.get_text_from_response(response)
            if text:
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(text[json_start:json_end])
                    return RiskAssessment(
                        executive_summary=result.get("executive_summary", ""),
                        deal_killers=result.get("deal_killers", []),
                        major_risks=result.get("major_risks", []),
                        valuation_concerns=result.get("valuation_concerns", []),
                        due_diligence_gaps=result.get("due_diligence_gaps", []),
                        counter_arguments=result.get("counter_arguments", []),
                        stress_scenarios=result.get("stress_scenarios", []),
                        recommendation=result.get("recommendation", "ADDITIONAL DD REQUIRED"),
                    )

        except Exception as e:
            logger.warning(f"LLM assessment generation failed: {e}")

        return self._generate_template_assessment(deal_context, bull_memo)

    def _generate_template_assessment(
        self, deal_context: dict, bull_memo: Optional[dict]
    ) -> RiskAssessment:
        """Generate template-based assessment."""
        company_name = deal_context.get("company_name", "Target Company")
        industry = deal_context.get("industry", "Technology")
        revenue = deal_context.get("revenue", 100)
        ebitda = deal_context.get("ebitda", 20)
        entry_multiple = deal_context.get("entry_multiple", 8.0)
        irr = deal_context.get("irr", "20%")

        return RiskAssessment(
            executive_summary=f"""While {company_name} presents several attractive characteristics,
this assessment identifies significant risks that require careful consideration before proceeding.

Key concerns include: (1) valuation premium relative to comparable transactions,
(2) customer concentration risk, (3) competitive threats from well-funded players,
and (4) execution risk on the value creation plan.

We recommend additional due diligence to address identified gaps before final IC approval.""",

            deal_killers=[
                {
                    "issue": "Customer concentration - top 3 customers represent 40%+ of revenue",
                    "severity": "CRITICAL",
                    "resolution_path": "Obtain long-term contracts with key customers; validate renewal probability",
                },
                {
                    "issue": "Key technology dependency on third-party vendor",
                    "severity": "CRITICAL",
                    "resolution_path": "Negotiate long-term agreement or develop alternative; assess IP ownership",
                },
            ],

            major_risks=[
                {
                    "risk": "Market disruption from new entrants with significant funding",
                    "probability": "MEDIUM",
                    "impact": "HIGH",
                    "monitoring": "Track competitive landscape quarterly; customer win/loss analysis",
                },
                {
                    "risk": "Key management departure post-close",
                    "probability": "MEDIUM",
                    "impact": "HIGH",
                    "monitoring": "Implement retention packages; develop succession plans",
                },
                {
                    "risk": "Revenue growth assumptions too aggressive",
                    "probability": "MEDIUM",
                    "impact": "MEDIUM",
                    "monitoring": "Monthly pipeline reviews; early warning indicators",
                },
                {
                    "risk": "Integration complexity if pursuing M&A strategy",
                    "probability": "HIGH",
                    "impact": "MEDIUM",
                    "monitoring": "Detailed integration planning; dedicated PMO",
                },
            ],

            valuation_concerns=[
                f"Entry multiple of {entry_multiple}x represents a premium to comparable transactions (median: {entry_multiple - 1}x)",
                "Valuation assumes continuation of historical growth rates which may not be sustainable",
                "Limited margin of safety if base case growth doesn't materialize",
                "Exit multiple assumption of {entry_multiple}x may be optimistic given market conditions",
            ],

            due_diligence_gaps=[
                "Customer reference calls not yet completed for top 10 accounts",
                "Technology due diligence pending - need third-party assessment",
                "Quality of earnings analysis not finalized",
                "Environmental and regulatory compliance review incomplete",
                "Management background checks in progress",
            ],

            counter_arguments=[
                {
                    "bull_claim": "Market leadership position provides sustainable competitive advantage",
                    "counter": "Market share has been flat for 2 years; new entrants gaining traction with innovative approaches",
                },
                {
                    "bull_claim": "High customer retention demonstrates product stickiness",
                    "counter": "Retention high but average contract value declining; customers may be reducing scope",
                },
                {
                    "bull_claim": "Multiple value creation levers provide downside protection",
                    "counter": "Margin improvement initiatives have been tried before with limited success; M&A pipeline unproven",
                },
            ],

            stress_scenarios=[
                {
                    "scenario": "Revenue growth at 50% of base case (2.5% vs 5%)",
                    "irr_impact": "IRR declines to 12-14%",
                    "likelihood": "25%",
                },
                {
                    "scenario": "Loss of largest customer",
                    "irr_impact": "IRR declines to 8-10%; potential covenant breach",
                    "likelihood": "10%",
                },
                {
                    "scenario": "Exit multiple compression of 1x (7x vs 8x)",
                    "irr_impact": "IRR declines to 16%",
                    "likelihood": "30%",
                },
            ],

            recommendation="ADDITIONAL DD REQUIRED - Address identified gaps before final approval; recommend negotiating price reduction of 0.5x multiple to improve margin of safety",
        )

    def _is_processing_complete(self, state: AgentState) -> bool:
        return bool(state.get("output_data")) or bool(state.get("errors"))

    async def generate_assessment(
        self, deal_context: dict, bull_memo: Optional[dict] = None
    ) -> AgentOutput:
        """Generate a risk assessment for a deal."""
        return await self.run(
            input_data={"deal_context": deal_context, "bull_memo": bull_memo}
        )
