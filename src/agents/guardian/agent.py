"""LegalGuardian Agent - Analyzes contracts for legal risks and red flags.

This agent uses LLM-based analysis to detect problematic clauses in contracts
that could affect M&A transactions, such as Change of Control provisions,
non-compete clauses, termination rights, and more.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

from .mock_data import (
    MOCK_CONTRACTS,
    ContractType,
    MockContract,
    RiskLevel,
    get_contract_by_id,
)

logger = logging.getLogger(__name__)


@dataclass
class LegalFlag:
    """Represents a legal risk flag identified in a contract."""
    clause_type: str
    risk_level: RiskLevel
    description: str
    excerpt: str
    page_reference: Optional[str]
    recommendation: str
    deal_impact: str


@dataclass
class ContractAnalysis:
    """Complete analysis of a contract."""
    contract_id: str
    contract_name: str
    contract_type: str
    counterparty: str
    flags: list[LegalFlag]
    overall_risk: RiskLevel
    summary: str
    key_dates: dict[str, str]
    financial_exposure: Optional[float]
    requires_review: bool

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "contract_name": self.contract_name,
            "contract_type": self.contract_type,
            "counterparty": self.counterparty,
            "flags": [
                {
                    "clause_type": f.clause_type,
                    "risk_level": f.risk_level.value,
                    "description": f.description,
                    "excerpt": f.excerpt,
                    "page_reference": f.page_reference,
                    "recommendation": f.recommendation,
                    "deal_impact": f.deal_impact,
                }
                for f in self.flags
            ],
            "overall_risk": self.overall_risk.value,
            "summary": self.summary,
            "key_dates": self.key_dates,
            "financial_exposure": self.financial_exposure,
            "requires_review": self.requires_review,
            "flag_count": len(self.flags),
            "critical_flags": len([f for f in self.flags if f.risk_level == RiskLevel.CRITICAL]),
            "high_flags": len([f for f in self.flags if f.risk_level == RiskLevel.HIGH]),
        }


# Clause types to detect
CLAUSE_TYPES = [
    "change_of_control",
    "assignment_restriction",
    "termination_rights",
    "non_compete",
    "non_solicitation",
    "exclusivity",
    "most_favored_nation",
    "audit_rights",
    "indemnification",
    "liability_cap",
    "personal_guarantee",
    "material_adverse_change",
    "consent_requirements",
    "acceleration_clause",
    "covenant_restrictions",
]


class LegalGuardianAgent(BaseAgent):
    """
    Autonomous agent for analyzing contracts and identifying legal risks.

    Capabilities:
    - Detects Change of Control clauses and their implications
    - Identifies assignment restrictions
    - Finds termination rights that could affect an acquisition
    - Highlights non-compete and non-solicitation provisions
    - Calculates potential financial exposure
    - Generates risk-scored analysis with recommendations

    Workflow:
    1. Parse contract text
    2. Use LLM to identify clause types and risks
    3. Score risks by severity
    4. Generate recommendations
    5. Flag items requiring human review
    """

    def __init__(self):
        """Initialize the LegalGuardian agent."""
        super().__init__(
            name="LegalGuardian",
            description="Analyzes contracts for legal risks and M&A red flags",
            max_iterations=3,
        )

    def get_system_prompt(self) -> str:
        """System prompt for legal analysis."""
        return """You are a Legal Due Diligence Analyst at a private equity firm.
Your role is to analyze contracts and identify legal risks that could affect M&A transactions.

Focus on these critical clause types:
1. Change of Control - provisions that trigger upon ownership change
2. Assignment Restrictions - limits on transferring the contract
3. Termination Rights - counterparty's ability to exit upon transaction
4. Non-Compete/Non-Solicitation - restrictions on competition
5. Consent Requirements - approvals needed for transaction
6. Financial Covenants - obligations that could be affected
7. Personal Guarantees - individual liability provisions
8. Indemnification - liability assumptions
9. Acceleration Clauses - early payment triggers

For each identified risk:
- Classify severity: critical, high, medium, low, info
- Extract the relevant clause text
- Explain the deal impact
- Provide a recommendation

Be thorough but prioritize issues that would materially affect a transaction.
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for the Guardian agent."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "analyze")

            if mode == "analyze":
                result = self._analyze_contract(input_data, state)
            elif mode == "analyze_all":
                result = self._analyze_all_contracts(input_data, state)
            elif mode == "check_clause":
                result = self._check_specific_clause(input_data, state)
            elif mode == "list_contracts":
                result = self._list_contracts(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _analyze_contract(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Analyze a single contract for legal risks."""
        contract_id = input_data.get("contract_id")
        contract_text = input_data.get("contract_text")

        if contract_id:
            contract = get_contract_by_id(contract_id)
            if not contract:
                state["errors"].append(f"Contract not found: {contract_id}")
                return {}
            contract_text = contract.content
            contract_name = contract.name
            contract_type = contract.contract_type.value
            counterparty = contract.counterparty
        elif contract_text:
            contract_name = input_data.get("contract_name", "Unknown Contract")
            contract_type = input_data.get("contract_type", "unknown")
            counterparty = input_data.get("counterparty", "Unknown")
            contract_id = f"custom-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        else:
            state["errors"].append("Either contract_id or contract_text is required")
            return {}

        # Analyze contract using LLM or rule-based approach
        if self._client is not None:
            analysis = self._analyze_with_llm(
                contract_id, contract_name, contract_type, counterparty, contract_text
            )
        else:
            analysis = self._analyze_rule_based(
                contract_id, contract_name, contract_type, counterparty, contract_text
            )

        # Record extraction
        extraction_record = {
            "type": "contract_analysis",
            "contract_id": contract_id,
            "contract_name": contract_name,
            "flags_found": len(analysis.flags),
            "overall_risk": analysis.overall_risk.value,
            "llm_enhanced": self._client is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Set confidence based on analysis quality
        if analysis.overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            state["requires_review"] = True
        state["confidence_scores"]["legal_analysis"] = 0.85 if self._client else 0.70

        return {
            "mode": "analyze",
            "analysis": analysis.to_dict(),
        }

    def _analyze_with_llm(
        self,
        contract_id: str,
        contract_name: str,
        contract_type: str,
        counterparty: str,
        contract_text: str,
    ) -> ContractAnalysis:
        """Use LLM to analyze contract for legal risks."""
        prompt = f"""Analyze this contract for legal risks that could affect an M&A transaction.

Contract: {contract_name}
Type: {contract_type}
Counterparty: {counterparty}

CONTRACT TEXT:
{contract_text}

Identify all legal risks and return a JSON object with this structure:
{{
    "flags": [
        {{
            "clause_type": "change_of_control|assignment_restriction|termination_rights|non_compete|etc",
            "risk_level": "critical|high|medium|low|info",
            "description": "Brief description of the risk",
            "excerpt": "Relevant quote from the contract",
            "recommendation": "What to do about this",
            "deal_impact": "How this affects an acquisition"
        }}
    ],
    "overall_risk": "critical|high|medium|low",
    "summary": "Executive summary of key risks",
    "key_dates": {{
        "effective_date": "date",
        "expiration_date": "date or null",
        "notice_periods": "any notice requirements"
    }},
    "financial_exposure": null or estimated dollar amount
}}

Focus on clauses that would be triggered by or affect an acquisition.
"""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=2048,
            )

            text = self.get_text_from_response(response)
            if text:
                # Extract JSON
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(text[json_start:json_end])
                    return self._parse_llm_result(
                        contract_id, contract_name, contract_type, counterparty, result
                    )

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, falling back to rule-based")

        return self._analyze_rule_based(
            contract_id, contract_name, contract_type, counterparty, contract_text
        )

    def _parse_llm_result(
        self,
        contract_id: str,
        contract_name: str,
        contract_type: str,
        counterparty: str,
        result: dict,
    ) -> ContractAnalysis:
        """Parse LLM result into ContractAnalysis."""
        flags = []
        for f in result.get("flags", []):
            try:
                risk_level = RiskLevel(f.get("risk_level", "medium"))
            except ValueError:
                risk_level = RiskLevel.MEDIUM

            flags.append(LegalFlag(
                clause_type=f.get("clause_type", "unknown"),
                risk_level=risk_level,
                description=f.get("description", ""),
                excerpt=f.get("excerpt", ""),
                page_reference=f.get("page_reference"),
                recommendation=f.get("recommendation", ""),
                deal_impact=f.get("deal_impact", ""),
            ))

        try:
            overall_risk = RiskLevel(result.get("overall_risk", "medium"))
        except ValueError:
            overall_risk = RiskLevel.MEDIUM

        return ContractAnalysis(
            contract_id=contract_id,
            contract_name=contract_name,
            contract_type=contract_type,
            counterparty=counterparty,
            flags=flags,
            overall_risk=overall_risk,
            summary=result.get("summary", "Analysis complete."),
            key_dates=result.get("key_dates", {}),
            financial_exposure=result.get("financial_exposure"),
            requires_review=overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH],
        )

    def _analyze_rule_based(
        self,
        contract_id: str,
        contract_name: str,
        contract_type: str,
        counterparty: str,
        contract_text: str,
    ) -> ContractAnalysis:
        """Rule-based contract analysis for when LLM is unavailable."""
        flags = []
        text_lower = contract_text.lower()

        # Change of Control detection
        coc_patterns = [
            "change of control",
            "change in control",
            "change-of-control",
            "ownership change",
        ]
        for pattern in coc_patterns:
            if pattern in text_lower:
                # Find the section
                idx = text_lower.find(pattern)
                excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]

                # Determine severity
                if any(x in text_lower for x in ["terminate", "termination right", "may terminate"]):
                    risk_level = RiskLevel.CRITICAL
                    deal_impact = "Counterparty may terminate agreement upon transaction closing"
                elif any(x in text_lower for x in ["consent", "approval", "notify"]):
                    risk_level = RiskLevel.HIGH
                    deal_impact = "Transaction may require counterparty consent or notification"
                else:
                    risk_level = RiskLevel.MEDIUM
                    deal_impact = "Change of Control provisions may affect transaction"

                flags.append(LegalFlag(
                    clause_type="change_of_control",
                    risk_level=risk_level,
                    description="Change of Control clause detected",
                    excerpt=excerpt.strip(),
                    page_reference=None,
                    recommendation="Review CoC clause carefully; may need counterparty consent or carve-out",
                    deal_impact=deal_impact,
                ))
                break

        # Assignment restriction detection
        if "assignment" in text_lower and any(x in text_lower for x in ["consent", "prohibited", "shall not assign", "may not assign"]):
            idx = text_lower.find("assignment")
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="assignment_restriction",
                risk_level=RiskLevel.HIGH,
                description="Assignment restriction requires counterparty consent",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Obtain assignment consent or negotiate carve-out for M&A transactions",
                deal_impact="Contract may not transfer automatically in acquisition",
            ))

        # Non-compete detection
        if "non-compete" in text_lower or "noncompete" in text_lower or "not compete" in text_lower:
            idx = max(text_lower.find("non-compete"), text_lower.find("noncompete"), text_lower.find("not compete"))
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="non_compete",
                risk_level=RiskLevel.HIGH,
                description="Non-compete restriction identified",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Assess scope and duration; may limit post-acquisition operations",
                deal_impact="Could restrict acquirer's business activities",
            ))

        # Personal guarantee detection
        if "personal guarantee" in text_lower or "personally guarantee" in text_lower:
            idx = max(text_lower.find("personal guarantee"), text_lower.find("personally guarantee"))
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="personal_guarantee",
                risk_level=RiskLevel.HIGH,
                description="Personal guarantee by executive or owner",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Negotiate release of personal guarantee at closing",
                deal_impact="Seller may have ongoing personal liability post-close",
            ))

        # Acceleration clause detection (for loans)
        if any(x in text_lower for x in ["acceleration", "immediately due", "mandatory prepayment"]):
            idx = text_lower.find("acceleration") if "acceleration" in text_lower else text_lower.find("immediately due")
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="acceleration_clause",
                risk_level=RiskLevel.CRITICAL,
                description="Loan acceleration upon Change of Control",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Budget for debt payoff at closing or negotiate lender consent",
                deal_impact="Outstanding debt may become immediately payable",
            ))

        # Golden parachute / severance detection
        if "golden parachute" in text_lower or "enhanced severance" in text_lower or "double trigger" in text_lower:
            idx = max(
                text_lower.find("golden parachute") if "golden parachute" in text_lower else -1,
                text_lower.find("enhanced severance") if "enhanced severance" in text_lower else -1,
                text_lower.find("double trigger") if "double trigger" in text_lower else -1,
            )
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="golden_parachute",
                risk_level=RiskLevel.HIGH,
                description="Enhanced severance or golden parachute provision",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Factor executive payouts into transaction costs",
                deal_impact="May trigger significant payments to executives at close",
            ))

        # MFN clause detection
        if "most favored" in text_lower or "most-favored" in text_lower:
            idx = max(text_lower.find("most favored"), text_lower.find("most-favored"))
            excerpt = contract_text[max(0, idx - 50):min(len(contract_text), idx + 200)]
            flags.append(LegalFlag(
                clause_type="most_favored_nation",
                risk_level=RiskLevel.MEDIUM,
                description="Most Favored Nation pricing clause",
                excerpt=excerpt.strip(),
                page_reference=None,
                recommendation="Verify pricing compliance; may affect pricing flexibility",
                deal_impact="May limit ability to offer different terms to other customers",
            ))

        # Determine overall risk
        if any(f.risk_level == RiskLevel.CRITICAL for f in flags):
            overall_risk = RiskLevel.CRITICAL
        elif any(f.risk_level == RiskLevel.HIGH for f in flags):
            overall_risk = RiskLevel.HIGH
        elif any(f.risk_level == RiskLevel.MEDIUM for f in flags):
            overall_risk = RiskLevel.MEDIUM
        elif flags:
            overall_risk = RiskLevel.LOW
        else:
            overall_risk = RiskLevel.INFO

        # Generate summary
        if flags:
            critical_count = len([f for f in flags if f.risk_level == RiskLevel.CRITICAL])
            high_count = len([f for f in flags if f.risk_level == RiskLevel.HIGH])
            summary = f"Identified {len(flags)} legal risks: {critical_count} critical, {high_count} high priority. "
            if critical_count > 0:
                summary += "Immediate attention required for critical issues."
        else:
            summary = "No significant legal risks identified in this contract."

        return ContractAnalysis(
            contract_id=contract_id,
            contract_name=contract_name,
            contract_type=contract_type,
            counterparty=counterparty,
            flags=flags,
            overall_risk=overall_risk,
            summary=summary,
            key_dates={},
            financial_exposure=None,
            requires_review=overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH],
        )

    def _analyze_all_contracts(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Analyze all available contracts."""
        contract_type_filter = input_data.get("contract_type")
        analyses = []

        for contract in MOCK_CONTRACTS:
            if contract_type_filter and contract.contract_type.value != contract_type_filter:
                continue

            if self._client is not None:
                analysis = self._analyze_with_llm(
                    contract.id,
                    contract.name,
                    contract.contract_type.value,
                    contract.counterparty,
                    contract.content,
                )
            else:
                analysis = self._analyze_rule_based(
                    contract.id,
                    contract.name,
                    contract.contract_type.value,
                    contract.counterparty,
                    contract.content,
                )
            analyses.append(analysis.to_dict())

        # Calculate aggregate risk
        critical_total = sum(a["critical_flags"] for a in analyses)
        high_total = sum(a["high_flags"] for a in analyses)

        return {
            "mode": "analyze_all",
            "contracts_analyzed": len(analyses),
            "total_critical_flags": critical_total,
            "total_high_flags": high_total,
            "analyses": analyses,
        }

    def _check_specific_clause(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Check for a specific clause type across contracts."""
        clause_type = input_data.get("clause_type", "change_of_control")
        results = []

        for contract in MOCK_CONTRACTS:
            if self._client is not None:
                analysis = self._analyze_with_llm(
                    contract.id,
                    contract.name,
                    contract.contract_type.value,
                    contract.counterparty,
                    contract.content,
                )
            else:
                analysis = self._analyze_rule_based(
                    contract.id,
                    contract.name,
                    contract.contract_type.value,
                    contract.counterparty,
                    contract.content,
                )

            matching_flags = [f for f in analysis.flags if f.clause_type == clause_type]
            if matching_flags:
                results.append({
                    "contract_id": contract.id,
                    "contract_name": contract.name,
                    "counterparty": contract.counterparty,
                    "flags": [
                        {
                            "risk_level": f.risk_level.value,
                            "description": f.description,
                            "excerpt": f.excerpt,
                            "deal_impact": f.deal_impact,
                        }
                        for f in matching_flags
                    ],
                })

        return {
            "mode": "check_clause",
            "clause_type": clause_type,
            "contracts_with_clause": len(results),
            "results": results,
        }

    def _list_contracts(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """List all available contracts."""
        contracts = []
        for contract in MOCK_CONTRACTS:
            contracts.append({
                "id": contract.id,
                "name": contract.name,
                "type": contract.contract_type.value,
                "counterparty": contract.counterparty,
                "effective_date": contract.effective_date,
                "expiration_date": contract.expiration_date,
                "value": contract.value,
            })

        return {
            "mode": "list_contracts",
            "total_contracts": len(contracts),
            "contracts": contracts,
        }

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if processing is complete."""
        return bool(state.get("output_data")) or bool(state.get("errors"))

    # Convenience methods

    async def analyze_contract(
        self,
        contract_id: Optional[str] = None,
        contract_text: Optional[str] = None,
        contract_name: str = "Unknown",
        contract_type: str = "unknown",
        counterparty: str = "Unknown",
    ) -> AgentOutput:
        """
        Analyze a contract for legal risks.

        Args:
            contract_id: ID of a mock contract to analyze
            contract_text: Raw contract text to analyze
            contract_name: Name of the contract (if using contract_text)
            contract_type: Type of contract (if using contract_text)
            counterparty: Counterparty name (if using contract_text)

        Returns:
            AgentOutput with analysis results
        """
        input_data = {
            "mode": "analyze",
            "contract_id": contract_id,
            "contract_text": contract_text,
            "contract_name": contract_name,
            "contract_type": contract_type,
            "counterparty": counterparty,
        }
        return await self.run(input_data=input_data)

    async def analyze_all(
        self,
        contract_type: Optional[str] = None,
    ) -> AgentOutput:
        """
        Analyze all contracts, optionally filtered by type.

        Args:
            contract_type: Optional filter by contract type

        Returns:
            AgentOutput with all analyses
        """
        input_data = {
            "mode": "analyze_all",
            "contract_type": contract_type,
        }
        return await self.run(input_data=input_data)

    async def check_clause(
        self,
        clause_type: str = "change_of_control",
    ) -> AgentOutput:
        """
        Check for a specific clause type across all contracts.

        Args:
            clause_type: Type of clause to search for

        Returns:
            AgentOutput with contracts containing the clause
        """
        input_data = {
            "mode": "check_clause",
            "clause_type": clause_type,
        }
        return await self.run(input_data=input_data)

    async def list_contracts(self) -> AgentOutput:
        """
        List all available contracts.

        Returns:
            AgentOutput with contract list
        """
        return await self.run(input_data={"mode": "list_contracts"})


def create_guardian() -> LegalGuardianAgent:
    """Factory function to create a LegalGuardian agent."""
    return LegalGuardianAgent()
