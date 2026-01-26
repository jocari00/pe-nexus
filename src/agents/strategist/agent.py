"""QuantStrategist Agent - Financial modeling and LBO analysis.

This agent builds financial models, calculates returns, and generates
sensitivity analyses for private equity transactions.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

from .models import LBOAssumptions, LBOModel, SensitivityTable, to_decimal

logger = logging.getLogger(__name__)


class QuantStrategistAgent(BaseAgent):
    """
    Autonomous agent for financial modeling and analysis.

    Capabilities:
    - Build LBO models from financial data
    - Calculate IRR and MOIC returns
    - Generate sensitivity tables
    - Analyze value creation drivers
    - Provide investment recommendations

    Workflow:
    1. Accept target company financials
    2. Apply transaction assumptions
    3. Build financial projections
    4. Calculate returns
    5. Generate sensitivity analysis
    """

    def __init__(self):
        """Initialize the QuantStrategist agent."""
        super().__init__(
            name="QuantStrategist",
            description="Financial modeling and LBO analysis specialist",
            max_iterations=3,
        )

    def get_system_prompt(self) -> str:
        """System prompt for financial analysis."""
        return """You are a Quantitative Strategist at a private equity firm.
Your role is to build financial models and analyze investment returns.

When analyzing LBO opportunities:
1. Evaluate entry valuation relative to comparable transactions
2. Assess debt capacity based on cash flow coverage
3. Model realistic growth scenarios
4. Calculate returns under base, upside, and downside cases
5. Identify key value creation levers

Your recommendations should be data-driven and include:
- Clear investment thesis
- Key assumptions and sensitivities
- Risk factors and mitigants
- Comparison to target return thresholds (typically 20%+ IRR, 2.5x+ MOIC)

Format financial values clearly with appropriate precision.
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for the Strategist agent."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "build_lbo")

            if mode == "build_lbo":
                result = self._build_lbo_model(input_data, state)
            elif mode == "sensitivity":
                result = self._generate_sensitivity(input_data, state)
            elif mode == "quick_returns":
                result = self._quick_returns_calc(input_data, state)
            elif mode == "analyze":
                result = self._full_analysis(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _build_lbo_model(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Build a full LBO model."""
        try:
            assumptions = self._parse_assumptions(input_data)
            model = LBOModel(assumptions)

            # Record extraction
            extraction_record = {
                "type": "lbo_model",
                "ltm_revenue": float(assumptions.ltm_revenue),
                "ltm_ebitda": float(assumptions.ltm_ebitda),
                "entry_multiple": float(assumptions.entry_multiple),
                "exit_multiple": float(assumptions.exit_multiple),
                "irr": float(model.returns.irr),
                "moic": float(model.returns.moic),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["extractions"].append(extraction_record)

            # Set confidence
            state["confidence_scores"]["lbo_model"] = 0.90

            return {
                "mode": "build_lbo",
                "success": True,
                "model": model.to_dict(),
                "summary": self._generate_model_summary(model, assumptions),
            }

        except ValueError as e:
            state["errors"].append(f"Invalid assumptions: {str(e)}")
            return {"mode": "build_lbo", "success": False, "error": str(e)}

    def _generate_sensitivity(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Generate sensitivity tables."""
        try:
            assumptions = self._parse_assumptions(input_data)
            sensitivity = SensitivityTable(assumptions)

            sensitivity_type = input_data.get("sensitivity_type", "entry_exit")
            metric = input_data.get("metric", "irr")

            if sensitivity_type == "entry_exit":
                table = sensitivity.generate_entry_exit_sensitivity(metric=metric)
            elif sensitivity_type == "growth_leverage":
                table = sensitivity.generate_growth_leverage_sensitivity(metric=metric)
            else:
                # Both tables
                entry_exit = sensitivity.generate_entry_exit_sensitivity(metric=metric)
                growth_leverage = sensitivity.generate_growth_leverage_sensitivity(metric=metric)
                table = {
                    "entry_exit": entry_exit,
                    "growth_leverage": growth_leverage,
                }

            # Record extraction
            extraction_record = {
                "type": "sensitivity_analysis",
                "sensitivity_type": sensitivity_type,
                "metric": metric,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["extractions"].append(extraction_record)

            return {
                "mode": "sensitivity",
                "success": True,
                "sensitivity_type": sensitivity_type,
                "metric": metric,
                "tables": table,
            }

        except ValueError as e:
            state["errors"].append(f"Invalid assumptions: {str(e)}")
            return {"mode": "sensitivity", "success": False, "error": str(e)}

    def _quick_returns_calc(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Quick IRR/MOIC calculation without full model."""
        entry_equity = to_decimal(input_data.get("entry_equity", 0))
        exit_equity = to_decimal(input_data.get("exit_equity", 0))
        holding_period = input_data.get("holding_period", 5)

        if entry_equity <= 0:
            state["errors"].append("Entry equity must be positive")
            return {}

        if exit_equity <= 0:
            state["errors"].append("Exit equity must be positive")
            return {}

        # MOIC
        moic = exit_equity / entry_equity

        # IRR
        n = Decimal(str(holding_period))
        irr = (moic ** (Decimal("1") / n)) - 1

        return {
            "mode": "quick_returns",
            "success": True,
            "entry_equity": float(entry_equity),
            "exit_equity": float(exit_equity),
            "holding_period": holding_period,
            "moic": float(moic.quantize(Decimal("0.01"))),
            "moic_formatted": f"{float(moic):.2f}x",
            "irr": float(irr.quantize(Decimal("0.0001"))),
            "irr_formatted": f"{float(irr) * 100:.1f}%",
        }

    def _full_analysis(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Full analysis with model, sensitivity, and LLM commentary."""
        try:
            assumptions = self._parse_assumptions(input_data)
            model = LBOModel(assumptions)
            sensitivity = SensitivityTable(assumptions)

            # Generate sensitivity tables
            entry_exit_irr = sensitivity.generate_entry_exit_sensitivity(metric="irr")
            entry_exit_moic = sensitivity.generate_entry_exit_sensitivity(metric="moic")
            growth_leverage = sensitivity.generate_growth_leverage_sensitivity(metric="irr")

            # Generate commentary
            if self._client is not None:
                commentary = self._generate_llm_commentary(model, assumptions)
            else:
                commentary = self._generate_template_commentary(model, assumptions)

            # Record extraction
            extraction_record = {
                "type": "full_analysis",
                "company_name": input_data.get("company_name", "Target"),
                "irr": float(model.returns.irr),
                "moic": float(model.returns.moic),
                "llm_enhanced": self._client is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["extractions"].append(extraction_record)
            state["confidence_scores"]["full_analysis"] = 0.85 if self._client else 0.75

            # Flag for review if returns are marginal
            if model.returns.irr < Decimal("0.15"):
                state["requires_review"] = True

            return {
                "mode": "analyze",
                "success": True,
                "company_name": input_data.get("company_name", "Target"),
                "model": model.to_dict(),
                "sensitivity": {
                    "entry_exit_irr": entry_exit_irr,
                    "entry_exit_moic": entry_exit_moic,
                    "growth_leverage_irr": growth_leverage,
                },
                "commentary": commentary,
                "recommendation": self._generate_recommendation(model),
            }

        except ValueError as e:
            state["errors"].append(f"Analysis failed: {str(e)}")
            return {"mode": "analyze", "success": False, "error": str(e)}

    def _parse_assumptions(self, input_data: dict[str, Any]) -> LBOAssumptions:
        """Parse input data into LBO assumptions."""
        return LBOAssumptions(
            ltm_revenue=to_decimal(input_data.get("ltm_revenue", input_data.get("revenue", 100))),
            ltm_ebitda=to_decimal(input_data.get("ltm_ebitda", input_data.get("ebitda", 20))),
            net_debt=to_decimal(input_data.get("net_debt", 0)),
            entry_multiple=to_decimal(input_data.get("entry_multiple", 8.0)),
            exit_multiple=to_decimal(input_data.get("exit_multiple", 8.0)),
            holding_period=input_data.get("holding_period", 5),
            revenue_growth_rate=to_decimal(input_data.get("revenue_growth", input_data.get("revenue_growth_rate", 0.05))),
            ebitda_margin=to_decimal(input_data.get("ebitda_margin")) if input_data.get("ebitda_margin") else None,
            senior_debt_multiple=to_decimal(input_data.get("leverage", input_data.get("senior_debt_multiple", 4.0))),
            senior_interest_rate=to_decimal(input_data.get("interest_rate", input_data.get("senior_interest_rate", 0.08))),
            mandatory_amortization=to_decimal(input_data.get("amortization", 0.05)),
            cash_sweep_percentage=to_decimal(input_data.get("cash_sweep", 0.50)),
            tax_rate=to_decimal(input_data.get("tax_rate", 0.25)),
        )

    def _generate_model_summary(self, model: LBOModel, assumptions: LBOAssumptions) -> dict:
        """Generate a summary of the LBO model."""
        return {
            "transaction": {
                "enterprise_value": float(assumptions.ltm_ebitda * assumptions.entry_multiple),
                "equity_check": float(model.sources_and_uses.equity),
                "debt": float(model.sources_and_uses.senior_debt),
                "leverage_ratio": f"{float(assumptions.senior_debt_multiple):.1f}x EBITDA",
            },
            "returns": {
                "irr": f"{float(model.returns.irr) * 100:.1f}%",
                "moic": f"{float(model.returns.moic):.2f}x",
                "holding_period": f"{assumptions.holding_period} years",
            },
            "value_creation": {
                "ebitda_growth": f"${float(model.returns.ebitda_growth_contribution):.1f}M",
                "multiple_expansion": f"${float(model.returns.multiple_expansion_contribution):.1f}M",
                "deleveraging": f"${float(model.returns.deleveraging_contribution):.1f}M",
            },
            "exit": {
                "exit_ebitda": float(model.projections[-1].ebitda),
                "exit_ev": float(model.projections[-1].ebitda * assumptions.exit_multiple),
                "remaining_debt": float(model.projections[-1].debt_balance),
                "exit_equity": float(model.returns.exit_equity),
            },
        }

    def _generate_llm_commentary(self, model: LBOModel, assumptions: LBOAssumptions) -> dict:
        """Generate LLM-enhanced investment commentary."""
        prompt = f"""Analyze this LBO investment and provide commentary.

TRANSACTION SUMMARY:
- Entry Multiple: {assumptions.entry_multiple}x EBITDA
- Exit Multiple: {assumptions.exit_multiple}x EBITDA
- Leverage: {assumptions.senior_debt_multiple}x EBITDA
- Revenue Growth: {float(assumptions.revenue_growth_rate) * 100:.1f}% annually
- Holding Period: {assumptions.holding_period} years

RETURNS:
- IRR: {float(model.returns.irr) * 100:.1f}%
- MOIC: {float(model.returns.moic):.2f}x
- Entry Equity: ${float(model.returns.entry_equity):.1f}M
- Exit Equity: ${float(model.returns.exit_equity):.1f}M

VALUE CREATION:
- EBITDA Growth: ${float(model.returns.ebitda_growth_contribution):.1f}M
- Multiple Expansion: ${float(model.returns.multiple_expansion_contribution):.1f}M
- Deleveraging: ${float(model.returns.deleveraging_contribution):.1f}M

Provide a JSON response with:
{{
    "investment_thesis": "2-3 sentence thesis",
    "key_strengths": ["strength 1", "strength 2", "strength 3"],
    "key_risks": ["risk 1", "risk 2", "risk 3"],
    "sensitivity_notes": "Key assumptions to stress test",
    "verdict": "ATTRACTIVE / MARGINAL / UNATTRACTIVE"
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
                # Extract JSON
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(text[json_start:json_end])
                    result["llm_generated"] = True
                    return result

        except Exception as e:
            logger.warning(f"LLM commentary failed: {e}")

        return self._generate_template_commentary(model, assumptions)

    def _generate_template_commentary(self, model: LBOModel, assumptions: LBOAssumptions) -> dict:
        """Generate template-based commentary."""
        irr = float(model.returns.irr)
        moic = float(model.returns.moic)

        # Determine verdict
        if irr >= 0.25 and moic >= 2.5:
            verdict = "ATTRACTIVE"
            thesis = f"Strong returns of {irr * 100:.1f}% IRR and {moic:.2f}x MOIC exceed target thresholds."
        elif irr >= 0.20 and moic >= 2.0:
            verdict = "ATTRACTIVE"
            thesis = f"Returns of {irr * 100:.1f}% IRR and {moic:.2f}x MOIC meet investment criteria."
        elif irr >= 0.15:
            verdict = "MARGINAL"
            thesis = f"Returns of {irr * 100:.1f}% IRR are below target but may be acceptable with upside potential."
        else:
            verdict = "UNATTRACTIVE"
            thesis = f"Returns of {irr * 100:.1f}% IRR are below minimum thresholds."

        return {
            "investment_thesis": thesis,
            "key_strengths": [
                f"Base case IRR of {irr * 100:.1f}% with {moic:.2f}x MOIC",
                f"Manageable leverage at {float(assumptions.senior_debt_multiple):.1f}x EBITDA",
                "Clear value creation path through growth and deleveraging",
            ],
            "key_risks": [
                "Entry multiple sensitivity - each 0.5x impacts returns significantly",
                "Revenue growth execution risk",
                "Interest rate exposure on floating rate debt",
            ],
            "sensitivity_notes": "Focus on entry/exit multiple scenarios and growth rate achievability",
            "verdict": verdict,
            "llm_generated": False,
        }

    def _generate_recommendation(self, model: LBOModel) -> dict:
        """Generate investment recommendation."""
        irr = float(model.returns.irr)
        moic = float(model.returns.moic)

        if irr >= 0.25 and moic >= 2.5:
            return {
                "decision": "PROCEED",
                "confidence": "HIGH",
                "rationale": "Returns significantly exceed hurdle rates",
                "next_steps": [
                    "Complete detailed due diligence",
                    "Engage legal counsel for LOI",
                    "Finalize debt commitment letters",
                ],
            }
        elif irr >= 0.20 and moic >= 2.0:
            return {
                "decision": "PROCEED_WITH_CAUTION",
                "confidence": "MEDIUM",
                "rationale": "Returns meet minimum thresholds",
                "next_steps": [
                    "Stress test key assumptions",
                    "Identify value creation initiatives",
                    "Consider negotiating lower entry price",
                ],
            }
        elif irr >= 0.15:
            return {
                "decision": "CONDITIONAL",
                "confidence": "LOW",
                "rationale": "Returns are marginal; requires upside to justify",
                "next_steps": [
                    "Identify specific upside opportunities",
                    "Negotiate better terms (price, structure)",
                    "Consider passing unless compelling strategic rationale",
                ],
            }
        else:
            return {
                "decision": "PASS",
                "confidence": "HIGH",
                "rationale": "Returns below minimum acceptable thresholds",
                "next_steps": [
                    "Communicate feedback to seller on pricing",
                    "Archive for potential future opportunity",
                ],
            }

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if processing is complete."""
        return bool(state.get("output_data")) or bool(state.get("errors"))

    # Convenience methods

    async def build_lbo(
        self,
        ltm_revenue: float,
        ltm_ebitda: float,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        holding_period: int = 5,
        leverage: float = 4.0,
        revenue_growth: float = 0.05,
        **kwargs,
    ) -> AgentOutput:
        """
        Build an LBO model with specified assumptions.

        Args:
            ltm_revenue: Last twelve months revenue
            ltm_ebitda: Last twelve months EBITDA
            entry_multiple: Purchase price / EBITDA
            exit_multiple: Exit price / EBITDA
            holding_period: Years to exit
            leverage: Debt / EBITDA multiple
            revenue_growth: Annual revenue growth rate

        Returns:
            AgentOutput with LBO model
        """
        input_data = {
            "mode": "build_lbo",
            "ltm_revenue": ltm_revenue,
            "ltm_ebitda": ltm_ebitda,
            "entry_multiple": entry_multiple,
            "exit_multiple": exit_multiple,
            "holding_period": holding_period,
            "leverage": leverage,
            "revenue_growth": revenue_growth,
            **kwargs,
        }
        return await self.run(input_data=input_data)

    async def generate_sensitivity(
        self,
        ltm_revenue: float,
        ltm_ebitda: float,
        sensitivity_type: str = "entry_exit",
        metric: str = "irr",
        **kwargs,
    ) -> AgentOutput:
        """
        Generate sensitivity tables.

        Args:
            ltm_revenue: Last twelve months revenue
            ltm_ebitda: Last twelve months EBITDA
            sensitivity_type: "entry_exit", "growth_leverage", or "all"
            metric: "irr" or "moic"

        Returns:
            AgentOutput with sensitivity tables
        """
        input_data = {
            "mode": "sensitivity",
            "ltm_revenue": ltm_revenue,
            "ltm_ebitda": ltm_ebitda,
            "sensitivity_type": sensitivity_type,
            "metric": metric,
            **kwargs,
        }
        return await self.run(input_data=input_data)

    async def analyze(
        self,
        company_name: str,
        ltm_revenue: float,
        ltm_ebitda: float,
        entry_multiple: float = 8.0,
        exit_multiple: float = 8.0,
        **kwargs,
    ) -> AgentOutput:
        """
        Full analysis with model, sensitivity, and commentary.

        Args:
            company_name: Target company name
            ltm_revenue: Last twelve months revenue
            ltm_ebitda: Last twelve months EBITDA
            entry_multiple: Purchase price / EBITDA
            exit_multiple: Exit price / EBITDA

        Returns:
            AgentOutput with complete analysis
        """
        input_data = {
            "mode": "analyze",
            "company_name": company_name,
            "ltm_revenue": ltm_revenue,
            "ltm_ebitda": ltm_ebitda,
            "entry_multiple": entry_multiple,
            "exit_multiple": exit_multiple,
            **kwargs,
        }
        return await self.run(input_data=input_data)

    async def quick_calc(
        self,
        entry_equity: float,
        exit_equity: float,
        holding_period: int = 5,
    ) -> AgentOutput:
        """
        Quick IRR/MOIC calculation.

        Args:
            entry_equity: Initial equity investment
            exit_equity: Expected equity value at exit
            holding_period: Years

        Returns:
            AgentOutput with IRR and MOIC
        """
        input_data = {
            "mode": "quick_returns",
            "entry_equity": entry_equity,
            "exit_equity": exit_equity,
            "holding_period": holding_period,
        }
        return await self.run(input_data=input_data)


def create_strategist() -> QuantStrategistAgent:
    """Factory function to create a QuantStrategist agent."""
    return QuantStrategistAgent()
