"""Bull Agent - Generates investment thesis and positive case for deals.

The Bull agent argues for why an investment should be made, highlighting
strengths, opportunities, and potential value creation.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class InvestmentMemo:
    """Investment memorandum structure."""
    executive_summary: str
    investment_thesis: list[str]
    company_overview: dict
    market_opportunity: str
    competitive_position: str
    value_creation_plan: list[str]
    financial_highlights: dict
    key_risks_mitigants: list[dict]
    transaction_summary: dict
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "executive_summary": self.executive_summary,
            "investment_thesis": self.investment_thesis,
            "company_overview": self.company_overview,
            "market_opportunity": self.market_opportunity,
            "competitive_position": self.competitive_position,
            "value_creation_plan": self.value_creation_plan,
            "financial_highlights": self.financial_highlights,
            "key_risks_mitigants": self.key_risks_mitigants,
            "transaction_summary": self.transaction_summary,
            "recommendation": self.recommendation,
        }


class BullAgent(BaseAgent):
    """
    Agent that generates the bullish investment case.

    Capabilities:
    - Creates investment memoranda
    - Articulates investment thesis
    - Highlights value creation opportunities
    - Addresses risks with mitigants
    """

    def __init__(self):
        super().__init__(
            name="BullAgent",
            description="Investment thesis and positive case generator",
            max_iterations=2,
        )

    def get_system_prompt(self) -> str:
        return """You are a senior Private Equity investment professional presenting a deal to the Investment Committee.

Your role is to make the strongest possible case FOR the investment. You should:
1. Lead with a compelling investment thesis
2. Highlight the company's strengths and competitive advantages
3. Articulate clear value creation opportunities
4. Address risks proactively with credible mitigants
5. Present financial analysis supporting attractive returns

Be persuasive but intellectually honest. Acknowledge risks but frame them constructively.
Your tone should be confident and professional, suitable for an IC presentation.
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Generate investment memo."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            deal_context = input_data.get("deal_context", {})

            if self._client is not None:
                memo = self._generate_llm_memo(deal_context)
            else:
                memo = self._generate_template_memo(deal_context)

            # Record extraction
            extraction_record = {
                "type": "investment_memo",
                "company_name": deal_context.get("company_name", "Target"),
                "llm_enhanced": self._client is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["extractions"].append(extraction_record)
            state["confidence_scores"]["memo"] = 0.85 if self._client else 0.70

            state["output_data"] = {
                "memo": memo.to_dict(),
                "agent": "BullAgent",
            }
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _generate_llm_memo(self, deal_context: dict) -> InvestmentMemo:
        """Generate memo using LLM."""
        prompt = f"""Generate an investment memorandum for the following deal:

DEAL CONTEXT:
Company: {deal_context.get('company_name', 'Target Company')}
Industry: {deal_context.get('industry', 'Technology')}
Revenue: ${deal_context.get('revenue', 100)}M
EBITDA: ${deal_context.get('ebitda', 20)}M
Entry Multiple: {deal_context.get('entry_multiple', 8.0)}x
Expected IRR: {deal_context.get('irr', '20%')}
Expected MOIC: {deal_context.get('moic', '2.5x')}
Key Strengths: {deal_context.get('strengths', ['Market leader', 'Strong margins', 'Recurring revenue'])}

Generate a compelling investment memo with this JSON structure:
{{
    "executive_summary": "2-3 paragraph summary",
    "investment_thesis": ["thesis point 1", "thesis point 2", "thesis point 3"],
    "company_overview": {{
        "description": "company description",
        "founded": "year or 'N/A'",
        "employees": "count or 'N/A'",
        "headquarters": "location or 'N/A'"
    }},
    "market_opportunity": "market analysis paragraph",
    "competitive_position": "competitive analysis paragraph",
    "value_creation_plan": ["initiative 1", "initiative 2", "initiative 3"],
    "financial_highlights": {{
        "revenue": "revenue with growth",
        "ebitda": "ebitda with margin",
        "growth_rate": "growth rate"
    }},
    "key_risks_mitigants": [
        {{"risk": "risk description", "mitigant": "mitigant description"}}
    ],
    "transaction_summary": {{
        "enterprise_value": "EV",
        "equity_check": "equity amount",
        "leverage": "debt/ebitda"
    }},
    "recommendation": "APPROVE / APPROVE WITH CONDITIONS / DECLINE"
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
                    return InvestmentMemo(
                        executive_summary=result.get("executive_summary", ""),
                        investment_thesis=result.get("investment_thesis", []),
                        company_overview=result.get("company_overview", {}),
                        market_opportunity=result.get("market_opportunity", ""),
                        competitive_position=result.get("competitive_position", ""),
                        value_creation_plan=result.get("value_creation_plan", []),
                        financial_highlights=result.get("financial_highlights", {}),
                        key_risks_mitigants=result.get("key_risks_mitigants", []),
                        transaction_summary=result.get("transaction_summary", {}),
                        recommendation=result.get("recommendation", "APPROVE WITH CONDITIONS"),
                    )

        except Exception as e:
            logger.warning(f"LLM memo generation failed: {e}")

        return self._generate_template_memo(deal_context)

    def _generate_template_memo(self, deal_context: dict) -> InvestmentMemo:
        """Generate template-based memo."""
        company_name = deal_context.get("company_name", "Target Company")
        industry = deal_context.get("industry", "Technology")
        revenue = deal_context.get("revenue", 100)
        ebitda = deal_context.get("ebitda", 20)
        entry_multiple = deal_context.get("entry_multiple", 8.0)
        irr = deal_context.get("irr", "20%")
        moic = deal_context.get("moic", "2.5x")

        return InvestmentMemo(
            executive_summary=f"""We recommend the acquisition of {company_name}, a leading player in the {industry} sector.
The company demonstrates strong financial performance with ${revenue}M in revenue and ${ebitda}M in EBITDA,
representing a {ebitda/revenue*100:.0f}% margin. At an entry multiple of {entry_multiple}x EBITDA,
we project returns of {irr} IRR and {moic} MOIC over a 5-year hold period.

The investment thesis is anchored on (1) market leadership in a growing sector,
(2) multiple value creation levers including operational improvements and strategic M&A,
and (3) a clear path to exit through sale to strategics or financial sponsors.""",

            investment_thesis=[
                f"Market Leadership: {company_name} holds a #1/#2 position in its core market with strong brand recognition",
                "Attractive Financial Profile: High-margin, recurring revenue business with strong cash conversion",
                "Multiple Value Creation Levers: Organic growth, operational improvements, and tuck-in M&A opportunities",
                "Clear Exit Path: Multiple strategic and financial buyers have expressed interest in the space",
            ],

            company_overview={
                "description": f"{company_name} is a leading provider in the {industry} sector",
                "founded": "N/A",
                "employees": "N/A",
                "headquarters": "N/A",
            },

            market_opportunity=f"""The {industry} market is experiencing strong growth driven by digital transformation
and increasing enterprise adoption. The market is expected to grow at 10%+ annually over the next 5 years.
{company_name} is well-positioned to capture this growth through its established customer base and product portfolio.""",

            competitive_position=f"""{company_name} benefits from several competitive advantages including:
- Strong brand and reputation built over years of consistent delivery
- Proprietary technology platform with significant switching costs
- Deep customer relationships with Fortune 500 enterprises
- Experienced management team with track record of execution""",

            value_creation_plan=[
                "Revenue Growth: Expand into adjacent markets and cross-sell to existing customers",
                "Margin Improvement: Operational efficiency initiatives and procurement optimization",
                "Strategic M&A: Identify and execute 2-3 tuck-in acquisitions to expand capabilities",
                "Management Enhancement: Bring in operating partners with relevant industry experience",
            ],

            financial_highlights={
                "revenue": f"${revenue}M (growing at {deal_context.get('growth_rate', '5')}% annually)",
                "ebitda": f"${ebitda}M ({ebitda/revenue*100:.0f}% margin)",
                "growth_rate": f"{deal_context.get('growth_rate', '5')}% organic growth",
            },

            key_risks_mitigants=[
                {
                    "risk": "Customer concentration in top 10 accounts",
                    "mitigant": "Long-term contracts with 95%+ renewal rates; diversified pipeline",
                },
                {
                    "risk": "Competitive pressure from larger players",
                    "mitigant": "Differentiated product and strong customer relationships create moat",
                },
                {
                    "risk": "Key person risk with management team",
                    "mitigant": "Retention packages in place; bench strength identified for critical roles",
                },
            ],

            transaction_summary={
                "enterprise_value": f"${ebitda * entry_multiple:.0f}M ({entry_multiple}x EBITDA)",
                "equity_check": f"~${ebitda * entry_multiple * 0.4:.0f}M",
                "leverage": f"{entry_multiple * 0.5:.1f}x EBITDA senior debt",
            },

            recommendation="APPROVE - Attractive returns profile with multiple value creation levers and clear exit path",
        )

    def _is_processing_complete(self, state: AgentState) -> bool:
        return bool(state.get("output_data")) or bool(state.get("errors"))

    async def generate_memo(self, deal_context: dict) -> AgentOutput:
        """Generate an investment memo for a deal."""
        return await self.run(input_data={"deal_context": deal_context})
