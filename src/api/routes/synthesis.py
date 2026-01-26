"""
Synthesis API routes for the Deal Command Center.

Provides unified endpoints that aggregate data from multiple agents
into a cohesive view for the UI.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agents.scout import IntelligenceScoutAgent
from src.agents.navigator import create_navigator
from src.agents.guardian import create_guardian
from src.agents.strategist import create_strategist
from src.agents.ic import create_ic_agent
from uuid import uuid5, NAMESPACE_DNS
from src.agents.scout.mock_data import MOCK_COMPANIES
from src.agents.monitor import create_vcm

router = APIRouter(prefix="/synthesis", tags=["synthesis"])


# =============================================================================
# Request/Response Models
# =============================================================================


class NexusScoreBreakdown(BaseModel):
    """Breakdown of Nexus Score components."""

    market: float  # 0-100
    health: float  # 0-100
    risk: float  # 0-100 (lower is better)
    confidence: float  # 0-100
    returns: float  # 0-100


class NexusScore(BaseModel):
    """Unified Nexus Score for a company."""

    score: int  # 0-100
    tier: str  # HIGH, MEDIUM, LOW
    breakdown: NexusScoreBreakdown


class CompanyLeaderboardItem(BaseModel):
    """Summary item for the leaderboard view."""

    company_id: str
    company_name: str
    sector: str
    industry: str
    nexus_score: int
    score_tier: str
    revenue: float
    ebitda: float
    margin: float
    summary: str
    tags: list[str]
    status: str


class LeaderboardResponse(BaseModel):
    """Response for the high-conviction leaderboard."""

    success: bool
    companies: list[CompanyLeaderboardItem]
    total_count: int
    portfolio_summary: dict
    market_pulse: dict
    alerts_summary: dict


# =============================================================================
# Helper: Prospect Lookup
# =============================================================================

def _try_get_prospect(target_id: str) -> Optional[dict]:
    """Try to find a prospect from MOCK_COMPANIES by hashing names."""
    for company in MOCK_COMPANIES:
        # Re-compute deterministic ID
        score_id = str(uuid5(NAMESPACE_DNS, company["name"]))
        if score_id == target_id:
            return company
    return None


# =============================================================================
# Nexus Score Calculation
# =============================================================================


def calculate_nexus_score(
    scout_score: float = 0,
    monitor_health: float = 0,
    legal_risk: float = 0,
    ic_confidence: float = 0,
    returns_score: float = 0,
) -> NexusScore:
    """
    Synthesize multi-agent data into unified Nexus Score (0-100).

    Weights:
    - Scout Deal Score (30%): Market attractiveness
    - Monitor Health (30%): KPI performance
    - Guardian Risk (20%): Legal risk (inverted - lower risk = higher score)
    - IC Confidence (15%): Investment conviction
    - Strategist Returns (5%): IRR vs target
    """
    # Normalize inputs to 0-100 scale
    scout_normalized = min(max(scout_score * 10, 0), 100)  # Scout is 0-10
    health_normalized = min(max(monitor_health, 0), 100)
    risk_inverted = min(max(100 - legal_risk, 0), 100)  # Invert: low risk = good
    confidence_normalized = min(max(ic_confidence, 0), 100)
    returns_normalized = min(max(returns_score, 0), 100)

    # Calculate weighted score
    nexus_score = (
        scout_normalized * 0.30
        + health_normalized * 0.30
        + risk_inverted * 0.20
        + confidence_normalized * 0.15
        + returns_normalized * 0.05
    )

    # Determine tier
    if nexus_score >= 75:
        tier = "HIGH"
    elif nexus_score >= 50:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return NexusScore(
        score=round(nexus_score),
        tier=tier,
        breakdown=NexusScoreBreakdown(
            market=round(scout_normalized, 1),
            health=round(health_normalized, 1),
            risk=round(legal_risk, 1),  # Keep original for display
            confidence=round(confidence_normalized, 1),
            returns=round(returns_normalized, 1),
        ),
    )


def _derive_tags(
    status: str,
    revenue_growth: float = 0,
    score: float = 0,
    has_pe_interest: bool = False,
    has_legal_flags: bool = False,
) -> list[str]:
    """Derive display tags from company data."""
    tags = []

    # Status-based tags
    if status == "outperforming":
        tags.append("OUTPERFORMING")
    elif status == "at_risk":
        tags.append("AT RISK")
    elif status == "watch":
        tags.append("WATCH")

    # Growth tags
    if revenue_growth > 0.15:
        tags.append("HIGH GROWTH")
    elif revenue_growth > 0.08:
        tags.append("EXPANSION")

    # PE interest
    if has_pe_interest or score > 7.5:
        tags.append("PE INTEREST")

    # Legal concerns
    if has_legal_flags:
        tags.append("LEGAL REVIEW")

    return tags[:4]  # Limit to 4 tags


def _generate_summary(
    company_name: str,
    status: str,
    revenue_growth: float,
    margin: float,
) -> str:
    """Generate a quick-take summary for the company."""
    summaries = {
        "outperforming": f"Strong growth signals with {revenue_growth*100:.0f}% revenue growth; exceeding expectations across key metrics.",
        "on_track": f"Solid performance with {margin:.0f}% margins; meeting operational targets consistently.",
        "watch": f"Requires attention - monitoring key metrics for potential improvement opportunities.",
        "at_risk": f"Action needed - identified challenges require management focus and intervention.",
    }
    return summaries.get(status, f"Active portfolio company with {margin:.0f}% EBITDA margins.")


# =============================================================================
# Leaderboard Endpoint
# =============================================================================


@router.get("/leaderboard")
async def get_leaderboard(
    min_score: int = 0,
    limit: int = 20,
    industry: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Get the high-conviction leaderboard for the Deal Command Center.

    This endpoint synthesizes data from multiple agents to provide:
    - Ranked list of companies by Nexus Score
    - Portfolio summary statistics
    - Market pulse indicators
    - Alerts summary

    Query params:
    - min_score: Minimum Nexus Score (0-100) to include
    - limit: Maximum number of companies to return
    - industry: Filter by industry
    - status: Filter by status (on_track, watch, at_risk, outperforming)
    """
    try:
        # Get prospect companies from Scout agent
        scout = IntelligenceScoutAgent()
        # Use scan_industry to get list of potential deals
        scan_result = await scout.scan_industry(industry=industry, limit=limit)
        
        if not scan_result.success:
            # Raise error to debug why Scout failed
            error_msg = "; ".join(scan_result.errors)
            raise HTTPException(status_code=500, detail=f"Scout agent scan failed: {error_msg}")
        else:
            companies_data = scan_result.output_data.get("scored_deals", [])

        # Get alerts (keep VCM for alerts or switch to something else? For now keep VCM for global alerts)
        vcm = create_vcm()
        alerts_result = await vcm.get_alerts()
        alerts = alerts_result.output_data if alerts_result.success else {}

        # Process each company and calculate Nexus Score
        leaderboard_items = []

        for company in companies_data:
            company_id = company.get("id", "")
            company_name = company.get("company_name", "Unknown")

            # Extract financial data
            revenue = company.get("revenue", 0)
            ebitda = company.get("ebitda", 0)
            margin = (ebitda / revenue * 100) if revenue > 0 else 0
            revenue_growth = company.get("revenue_growth", 0)
            status = company.get("status", "on_track")

            # Calculate component scores for Nexus Score
            # Scout score: Use the actual Scout Agent score if available
            if "total_score" in company:
                scout_score = float(company["total_score"])
            else:
                # Fallback heuristic
                scout_score = min(10, 5 + revenue_growth * 20 + (1 if status == "outperforming" else 0))

            # Health score: based on performance vs budget
            budget_variance = company.get("budget_variance", 0)
            health_score = min(100, max(0, 70 + budget_variance * 100))

            # Risk score: placeholder (would come from Guardian agent)
            risk_score = 30 if status == "at_risk" else 15

            # IC confidence: derived from performance
            ic_confidence = 80 if status == "outperforming" else 65 if status == "on_track" else 45

            # Returns score: based on margin
            returns_score = min(100, margin * 3)

            # Calculate Nexus Score
            nexus = calculate_nexus_score(
                scout_score=scout_score,
                monitor_health=health_score,
                legal_risk=risk_score,
                ic_confidence=ic_confidence,
                returns_score=returns_score,
            )

            # Skip if below min_score
            if nexus.score < min_score:
                continue

            # Generate tags and summary
            tags = _derive_tags(
                status=status,
                revenue_growth=revenue_growth,
                score=scout_score,
                has_pe_interest=nexus.score > 75,
                has_legal_flags=risk_score > 25,
            )

            summary = _generate_summary(
                company_name=company_name,
                status=status,
                revenue_growth=revenue_growth,
                margin=margin,
            )

            leaderboard_items.append(
                CompanyLeaderboardItem(
                    company_id=company_id,
                    company_name=company_name,
                    sector=company.get("sector", company.get("industry", "Technology")),
                    industry=company.get("industry", "Technology"),
                    nexus_score=nexus.score,
                    score_tier=nexus.tier,
                    revenue=revenue,
                    ebitda=ebitda,
                    margin=round(margin, 1),
                    summary=summary,
                    tags=tags,
                    status=status,
                )
            )

        # Sort by Nexus Score descending
        leaderboard_items.sort(key=lambda x: x.nexus_score, reverse=True)

        # Limit results
        leaderboard_items = leaderboard_items[:limit]

        # Calculate portfolio summary
        total_revenue = sum(c.revenue for c in leaderboard_items)
        total_ebitda = sum(c.ebitda for c in leaderboard_items)
        avg_score = (
            sum(c.nexus_score for c in leaderboard_items) / len(leaderboard_items)
            if leaderboard_items
            else 0
        )

        portfolio_summary = {
            "active_deals": len(leaderboard_items),
            "total_revenue": round(total_revenue, 1),
            "total_ebitda": round(total_ebitda, 1),
            "avg_nexus_score": round(avg_score, 0),
            "nav_estimate": round(total_ebitda * 8, 1),  # Rough NAV estimate
        }

        # Market pulse (placeholder - could integrate real market data)
        market_pulse = {
            "vix": 18.5,
            "sp500_change": "+1.2%",
            "treasury_10y": "4.25%",
            "pe_deal_volume": "Strong",
        }

        # Alerts summary
        alerts_summary = {
            "critical": alerts.get("critical_count", 0),
            "high": alerts.get("high_count", 0),
            "total": alerts.get("total_alerts", 0),
        }

        return LeaderboardResponse(
            success=True,
            companies=[item.model_dump() for item in leaderboard_items],
            total_count=len(leaderboard_items),
            portfolio_summary=portfolio_summary,
            market_pulse=market_pulse,
            alerts_summary=alerts_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard synthesis failed: {str(e)}")


# =============================================================================
# Company Deep-Dive Synthesis
# =============================================================================


@router.get("/company/{company_id}")
async def get_company_synthesis(company_id: str):
    """
    Get unified intelligence view for a specific company.

    Synthesizes data from all agents into themed sections:
    - Market Positioning (Scout + Navigator)
    - Financial Health (Monitor + Strategist)
    - Risk Analysis (Guardian + IC Bear)
    - The Verdict (IC Synthesis)
    - Audit Trail (Agent traces)
    """
    try:
        # Initialize agents
        scout = IntelligenceScoutAgent()
        vcm = create_vcm()
        navigator = create_navigator()
        guardian = create_guardian()
        strategist = create_strategist()
        ic_agent = create_ic_agent()

        # Get company details from Monitor
        company_result = await vcm.get_company_detail(company_id=company_id)

        if not company_result.success:
            # Try to handle as a raw prospect (Scout only)
            prospect = _try_get_prospect(company_id)
            if not prospect:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Use prospect data
            company = prospect
            company_name = company.get("name", "Unknown")
            industry = company.get("industry", "Technology")
            # Create synthetic financial data for prospect
            raw_rev = company.get("revenue_estimate", 50)
            # Normalize to millions if > 1000
            revenue = raw_rev / 1_000_000 if raw_rev > 1_000 else raw_rev
            ebitda = revenue * 0.2
            margin = 20.0
            status = "watch" # Prospects are always "watch" or "on_track"
        else:
            company = company_result.output_data.get("company", {})
            company_name = company.get("name", "Unknown")
            industry = company.get("industry", "Technology")
            revenue = company.get("revenue", 0)
            ebitda = company.get("ebitda", 0)
            margin = (ebitda / revenue * 100) if revenue > 0 else 0
            status = company.get("status", "on_track")

        # Analyze company KPIs
        analysis_result = await vcm.analyze_company(company_id=company_id)
        analysis = analysis_result.output_data if analysis_result.success else {}

        # Get alerts for this company
        alerts_result = await vcm.get_alerts(company_id=company_id)
        company_alerts = alerts_result.output_data.get("alerts", []) if alerts_result.success else []

        # Build LBO model for financial projections
        lbo_result = await strategist.build_lbo(
            ltm_revenue=revenue,
            ltm_ebitda=ebitda,
            entry_multiple=8.0,
            exit_multiple=9.5,
            holding_period=5,
            leverage=4.0,
            revenue_growth=company.get("revenue_growth", 0.05),
        )
        lbo_data = lbo_result.output_data if lbo_result.success else {}
        # Extract LBO model and summary
        lbo = lbo_data.get("model", {})
        lbo_summary = lbo_data.get("summary", {})

        # Get Scout analysis
        scout_result = await scout.analyze_company(
            company_name=company_name,
            industry=industry,
            sub_sector=company.get("sub_sector", "")
        )
        scout_analysis = scout_result.output_data if scout_result.success else {}

        # Extract Scout data correctly
        scored_deal = scout_analysis.get("scored_deal", {})
        scout_score = scored_deal.get("total_score", 7.0)
        scout_priority = scored_deal.get("score_tier", "MEDIUM")
        scout_signals = []
        if "components" in scored_deal:
            for component in scored_deal.get("components", []):
                scout_signals.extend(component.get("signals_used", []))
        scout_signals = scout_signals[:3] if scout_signals else [f"{company_name} showing market activity"]

        # Get guardian analysis (use mock for now)
        guardian_result = await guardian.analyze_all()
        legal_analysis = guardian_result.output_data if guardian_result.success else {}

        # Run IC debate to get investment recommendation
        deal_context = {
            "company_name": company_name,
            "industry": industry,
            "revenue": revenue,
            "ebitda": ebitda,
            "entry_multiple": 8.0,
            "exit_multiple": 9.5,
            "irr": lbo.get("returns", {}).get("irr", "20%"),
            "moic": lbo.get("returns", {}).get("moic", "2.5x"),
            "strengths": [f"Strong margins ({margin:.1f}%)", "Proven execution"],
            "growth_rate": str(int(company.get("revenue_growth", 0.05) * 100))
        }
        ic_result = await ic_agent.run_debate(deal_context)
        ic_analysis = ic_result.output_data if ic_result.success else {}

        # Calculate Nexus Score components
        health_score = analysis.get("health_score", 70)
        risk_score = legal_analysis.get("overall_risk_score", 25)
        ic_confidence = ic_analysis.get("confidence", 75)
        # Extract IRR from LBO model for scoring
        irr_str = lbo.get("returns", {}).get("irr_formatted", "15%")
        returns_score = min(100, float(irr_str.replace("%", "")) * 4)

        nexus = calculate_nexus_score(
            scout_score=scout_score,
            monitor_health=health_score,
            legal_risk=risk_score,
            ic_confidence=ic_confidence,
            returns_score=returns_score,
        )

        # Build response structure
        response = {
            "success": True,
            "company": {
                "id": company_id,
                "name": company_name,
                "industry": industry,
                "sector": company.get("sector", industry),
                "status": status,
            },
            "nexus_score": {
                "score": nexus.score,
                "tier": nexus.tier,
                "breakdown": nexus.breakdown.model_dump(),
            },
            "market_positioning": {
                "scout_data": {
                    "deal_score": round(scout_score, 1),
                    "priority": scout_priority,
                    "industry_fit": "A" if scout_score >= 8 else "B" if scout_score >= 6 else "C",
                    "signals": scout_signals,
                },
                "navigator_data": {
                    "path_to_ceo": "2 hops",
                    "relationship_strength": 78,
                    "intro_available": True,
                    "best_path": f"You -> Board Contact -> CEO ({company_name})",
                },
            },
            "financial_health": {
                "current_performance": {
                    "revenue": revenue,
                    "ebitda": ebitda,
                    "margin": round(margin, 1),
                    "cash": company.get("cash", revenue * 0.15),
                    "revenue_yoy": f"+{company.get('revenue_growth', 0.1) * 100:.0f}%",
                    "ebitda_yoy": f"+{company.get('ebitda_growth', 0.12) * 100:.0f}%",
                    "margin_change": "+2.5pp",
                    "cash_status": "Healthy",
                },
                "returns_projection": {
                    "entry_multiple": lbo.get("assumptions", {}).get("entry_multiple", 8.0),
                    "exit_multiple": lbo.get("assumptions", {}).get("exit_multiple", 9.5),
                    "holding_period": lbo.get("assumptions", {}).get("holding_period", 5),
                    "leverage": lbo.get("assumptions", {}).get("senior_debt_multiple", 4.0),
                    "projected_irr": lbo_summary.get("returns", {}).get("irr", lbo.get("returns", {}).get("irr_formatted", "15%")),
                    "projected_moic": lbo_summary.get("returns", {}).get("moic", lbo.get("returns", {}).get("moic_formatted", "2.0x")),
                    "recommendation": lbo_summary.get("recommendation", "HOLD"),
                },
                "kpis": analysis.get("kpis", {}),
                "variances": analysis.get("variances", {}),
            },
            "risk_analysis": {
                "legal_analysis": {
                    "overall_risk": legal_analysis.get("overall_risk", "MEDIUM"),
                    "critical_flags": legal_analysis.get("critical_flags", 0),
                    "high_flags": legal_analysis.get("high_flags", 2),
                    "findings": legal_analysis.get("key_findings", [
                        {"severity": "HIGH", "text": "Change of Control clause in vendor agreement"},
                        {"severity": "MEDIUM", "text": "Assignment restriction in lease"},
                    ]),
                },
                "bear_case": {
                    "risks": [
                        "Customer concentration (top 3 = 45% revenue)",
                        "Emerging competition from cloud-native players",
                        "Key-man risk on CTO",
                    ],
                    "mitigants": [
                        "Diversification plan in progress",
                        "Technology moat via proprietary platform",
                        "Retention package proposed",
                    ],
                },
                "alerts": company_alerts,
            },
            "verdict": {
                "recommendation": ic_analysis.get("recommendation", "APPROVE WITH CONDITIONS" if nexus.score > 70 else "FURTHER ANALYSIS" if nexus.score > 50 else "PASS"),
                "confidence": ic_confidence,
                "thesis": ic_analysis.get("synthesis", f"{company_name} represents a compelling platform investment in the {industry} sector. "
                          f"Strong unit economics with {margin:.0f}% margins, proven execution, and clear path to value creation."),
                "conditions": ic_analysis.get("conditions", [
                    "Negotiate Change of Control waiver in vendor agreement",
                    "Secure 2-year retention for key executives with equity incentive",
                    "Complete customer concentration analysis",
                ]),
                "next_steps": ic_analysis.get("next_steps", [
                    "Schedule management presentation",
                    "Engage legal counsel for contract review",
                    "Build detailed 100-day plan",
                ]),
                "ic_data": {
                    "recommendation": ic_analysis.get("recommendation", "APPROVE WITH CONDITIONS"),
                    "confidence": ic_confidence,
                    "thesis": ic_analysis.get("synthesis", "Investment opportunity under review"),
                    "conditions": ic_analysis.get("conditions", []),
                    "next_steps": ic_analysis.get("next_steps", [])
                }
            },
            "audit_trail": {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "agent_traces": [
                    {"agent": "Monitor", "timestamp": datetime.now(timezone.utc).isoformat(), "action": "KPI analysis completed"},
                    {"agent": "Strategist", "timestamp": datetime.now(timezone.utc).isoformat(), "action": "LBO model v1.0 built"},
                    {"agent": "Guardian", "timestamp": datetime.now(timezone.utc).isoformat(), "action": "3 contracts analyzed"},
                ],
            },
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Company synthesis failed: {str(e)}")


# =============================================================================
# Quick Summary Endpoint (for cards)
# =============================================================================


@router.get("/company/{company_id}/summary")
async def get_company_quick_summary(company_id: str):
    """
    Get a quick summary for a company card.

    Lightweight endpoint for rendering company cards without full synthesis.
    """
    try:
        vcm = create_vcm()
        result = await vcm.get_company_detail(company_id=company_id)

        if not result.success:
            raise HTTPException(status_code=404, detail="Company not found")

        company = result.output_data.get("company", {})
        revenue = company.get("revenue", 0)
        ebitda = company.get("ebitda", 0)
        margin = (ebitda / revenue * 100) if revenue > 0 else 0
        status = company.get("status", "on_track")
        revenue_growth = company.get("revenue_growth", 0)

        # Quick Nexus Score calculation
        scout_score = min(10, 5 + revenue_growth * 20)
        health_score = 70 if status == "on_track" else 85 if status == "outperforming" else 50
        nexus = calculate_nexus_score(
            scout_score=scout_score,
            monitor_health=health_score,
            legal_risk=20,
            ic_confidence=70,
            returns_score=min(100, margin * 3),
        )

        tags = _derive_tags(status=status, revenue_growth=revenue_growth, score=scout_score)
        summary = _generate_summary(
            company_name=company.get("name", "Unknown"),
            status=status,
            revenue_growth=revenue_growth,
            margin=margin,
        )

        return {
            "success": True,
            "company_id": company_id,
            "company_name": company.get("name", "Unknown"),
            "industry": company.get("industry", "Technology"),
            "nexus_score": nexus.score,
            "score_tier": nexus.tier,
            "revenue": revenue,
            "ebitda": ebitda,
            "margin": round(margin, 1),
            "status": status,
            "tags": tags,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")
