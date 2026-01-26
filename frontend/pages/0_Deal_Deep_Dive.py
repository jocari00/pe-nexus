"""
PE-Nexus Deal Deep Dive
Unified Intelligence View for a specific company.

Synthesizes data from all agents into themed sections:
- Market Positioning
- Financial Health
- Risk Analysis
- The Verdict
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from components.theme import apply_dark_theme, COLORS, get_score_color, get_score_tier
from components.cards import (
    render_metric_card,
    render_section_header,
    render_info_box,
    render_verdict_box,
    render_key_finding,
)
from components.charts import (
    render_score_gauge,
    render_progress_bar,
    render_score_breakdown,
    render_risk_indicator,
)

# Page configuration
st.set_page_config(
    page_title="PE-Nexus | Deal Deep Dive",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply dark theme
apply_dark_theme()

# Get API client
api = get_api_client()


def get_mock_company_data(company_id: str) -> dict:
    """Get mock data for demo when backend is offline."""
    mock_data = {
        "cyberguard": {
            "company": {
                "id": "cyberguard",
                "name": "CyberGuard Systems",
                "industry": "Technology",
                "sector": "Cybersecurity",
                "status": "outperforming",
            },
            "nexus_score": {
                "score": 91,
                "tier": "HIGH",
                "breakdown": {
                    "market": 85,
                    "health": 90,
                    "risk": 20,
                    "confidence": 88,
                    "returns": 92,
                },
            },
            "market_positioning": {
                "scout_data": {
                    "deal_score": 8.5,
                    "priority": "HIGH",
                    "industry_fit": "A",
                    "signals": [
                        "PE firm Carlyle exploring strategic review",
                        "3 leadership hires in past 90 days",
                        "Industry consolidation wave ongoing",
                    ],
                },
                "navigator_data": {
                    "path_to_ceo": "2 hops",
                    "relationship_strength": 78,
                    "intro_available": True,
                    "best_path": "You -> Robert Kim -> Jennifer Martinez (CEO)",
                },
            },
            "financial_health": {
                "current_performance": {
                    "revenue": 85.2,
                    "ebitda": 21.3,
                    "margin": 25.0,
                    "cash": 12.4,
                    "revenue_yoy": "+12%",
                    "ebitda_yoy": "+18%",
                    "margin_change": "+2.5pp",
                    "cash_status": "Healthy",
                },
                "returns_projection": {
                    "entry_multiple": 8.0,
                    "exit_multiple": 9.5,
                    "holding_period": 5,
                    "leverage": 4.0,
                    "projected_irr": "24.5%",
                    "projected_moic": "2.8x",
                    "recommendation": "BUY",
                },
                "kpis": {
                    "arr_growth": "+28%",
                    "nrr": "118%",
                    "cac_payback": "14 months",
                    "ltv_cac": "4.2x",
                },
            },
            "risk_analysis": {
                "legal_analysis": {
                    "overall_risk": "MEDIUM",
                    "critical_flags": 0,
                    "high_flags": 2,
                    "findings": [
                        {"severity": "HIGH", "text": "Change of Control clause in vendor agreement"},
                        {"severity": "MEDIUM", "text": "Assignment restriction in lease"},
                    ],
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
                "alerts": [],
            },
            "verdict": {
                "recommendation": "APPROVE WITH CONDITIONS",
                "confidence": 78,
                "thesis": "CyberGuard represents a compelling platform investment in the high-growth cybersecurity sector. Strong unit economics, proven management team, and clear path to 2.5x+ returns.",
                "conditions": [
                    "Negotiate Change of Control waiver in vendor agreement",
                    "Secure 2-year retention for CTO with equity incentive",
                    "Complete customer concentration analysis",
                ],
                "next_steps": [
                    "Schedule management presentation",
                    "Engage legal counsel for contract review",
                    "Build detailed 100-day plan",
                ],
            },
            "audit_trail": {
                "last_updated": "2026-01-22T10:30:00Z",
                "agent_traces": [
                    {"agent": "Scout", "timestamp": "2026-01-22T09:00:00Z", "action": "Market analysis completed"},
                    {"agent": "Guardian", "timestamp": "2026-01-22T09:30:00Z", "action": "3 contracts analyzed"},
                    {"agent": "Strategist", "timestamp": "2026-01-22T10:00:00Z", "action": "LBO model v1.2 built"},
                    {"agent": "IC", "timestamp": "2026-01-22T10:30:00Z", "action": "Debate completed, 2 rounds"},
                ],
            },
        },
        "techflow": {
            "company": {
                "id": "techflow",
                "name": "TechFlow Solutions",
                "industry": "Technology",
                "sector": "B2B SaaS",
                "status": "outperforming",
            },
            "nexus_score": {
                "score": 87,
                "tier": "HIGH",
                "breakdown": {
                    "market": 80,
                    "health": 88,
                    "risk": 25,
                    "confidence": 82,
                    "returns": 85,
                },
            },
            "market_positioning": {
                "scout_data": {
                    "deal_score": 8.2,
                    "priority": "HIGH",
                    "industry_fit": "A",
                    "signals": [
                        "Strong product-market fit signals",
                        "Expanding into adjacent verticals",
                        "Key competitor recently acquired",
                    ],
                },
                "navigator_data": {
                    "path_to_ceo": "1 hop",
                    "relationship_strength": 85,
                    "intro_available": True,
                    "best_path": "You -> David Chen (CEO)",
                },
            },
            "financial_health": {
                "current_performance": {
                    "revenue": 52.0,
                    "ebitda": 13.0,
                    "margin": 25.0,
                    "cash": 8.5,
                    "revenue_yoy": "+35%",
                    "ebitda_yoy": "+42%",
                    "margin_change": "+3.0pp",
                    "cash_status": "Strong",
                },
                "returns_projection": {
                    "entry_multiple": 7.5,
                    "exit_multiple": 10.0,
                    "holding_period": 5,
                    "leverage": 3.5,
                    "projected_irr": "28.0%",
                    "projected_moic": "3.2x",
                    "recommendation": "STRONG BUY",
                },
                "kpis": {
                    "arr_growth": "+40%",
                    "nrr": "125%",
                    "cac_payback": "11 months",
                    "ltv_cac": "5.1x",
                },
            },
            "risk_analysis": {
                "legal_analysis": {
                    "overall_risk": "LOW",
                    "critical_flags": 0,
                    "high_flags": 1,
                    "findings": [
                        {"severity": "MEDIUM", "text": "Standard Change of Control provisions"},
                    ],
                },
                "bear_case": {
                    "risks": [
                        "High growth requires continued investment",
                        "Competition from larger players",
                        "Dependency on key enterprise accounts",
                    ],
                    "mitigants": [
                        "Strong unit economics support growth investment",
                        "Differentiated product with high switching costs",
                        "Diversifying customer base actively",
                    ],
                },
                "alerts": [],
            },
            "verdict": {
                "recommendation": "APPROVE",
                "confidence": 85,
                "thesis": "TechFlow is a high-growth SaaS platform with exceptional unit economics and strong market position. Clear path to significant value creation.",
                "conditions": [],
                "next_steps": [
                    "Move to LOI stage",
                    "Begin confirmatory due diligence",
                    "Finalize management incentive structure",
                ],
            },
            "audit_trail": {
                "last_updated": "2026-01-22T11:00:00Z",
                "agent_traces": [
                    {"agent": "Scout", "timestamp": "2026-01-22T08:00:00Z", "action": "Opportunity identified"},
                    {"agent": "Strategist", "timestamp": "2026-01-22T10:00:00Z", "action": "Returns model completed"},
                    {"agent": "IC", "timestamp": "2026-01-22T11:00:00Z", "action": "Strong buy recommendation"},
                ],
            },
        },
    }

    # Default mock data
    default = mock_data.get("cyberguard")
    default["company"]["id"] = company_id
    default["company"]["name"] = company_id.replace("_", " ").title()

    return mock_data.get(company_id, default)


def render_header(company_name: str, nexus_score: int, score_tier: str):
    """Render the deep dive header with back navigation."""
    score_color = get_score_color(nexus_score)
    score_class = f"nexus-score-{'high' if score_tier == 'HIGH' else 'medium' if score_tier == 'MEDIUM' else 'low'}"

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("< Back to Dashboard", key="back_btn"):
            st.session_state.selected_company = None
            st.switch_page("app.py")

        st.markdown(f"""
        <div class="command-header" style="margin-top: 1rem;">
            <h1 class="command-title">{company_name}</h1>
            <p class="command-subtitle">Unified Intelligence View</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                Nexus Score
            </div>
            <div style="font-size: 3rem; font-weight: 700; color: {score_color}; font-family: 'SF Mono', monospace;">
                {nexus_score}
            </div>
            <div style="font-size: 0.875rem; color: {score_color};">{score_tier} CONVICTION</div>
        </div>
        """, unsafe_allow_html=True)


def render_market_tab(market_data: dict):
    """Render the Market Positioning tab."""
    scout = market_data.get("scout_data", {})
    navigator = market_data.get("navigator_data", {})

    col1, col2 = st.columns(2)

    with col1:
        render_section_header("MARKET SIGNALS (Scout Agent)")

        # Key metrics row
        m1, m2, m3 = st.columns(3)
        with m1:
            render_metric_card("Deal Score", f"{scout.get('deal_score', 0)}/10")
        with m2:
            render_metric_card("Priority", scout.get("priority", "N/A"))
        with m3:
            render_metric_card("Industry Fit", scout.get("industry_fit", "N/A"))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Key Signals:**")
        for signal in scout.get("signals", []):
            st.markdown(f"- {signal}")

    with col2:
        render_section_header("RELATIONSHIP INTELLIGENCE (Navigator Agent)")

        # Path metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            render_metric_card("Path to CEO", navigator.get("path_to_ceo", "N/A"))
        with m2:
            render_metric_card("Strength", f"{navigator.get('relationship_strength', 0)}%")
        with m3:
            intro_status = "Yes" if navigator.get("intro_available") else "No"
            render_metric_card("Intro Available", intro_status)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Best Path:** {navigator.get('best_path', 'No path found')}")

        if navigator.get("intro_available"):
            if st.button("Generate Introduction Draft", key="gen_intro"):
                st.info("Introduction draft generation would be triggered here")


def render_financial_tab(financial_data: dict):
    """Render the Financial Health tab."""
    current = financial_data.get("current_performance", {})
    returns = financial_data.get("returns_projection", {})
    kpis = financial_data.get("kpis", {})

    # Current Performance Section
    render_section_header("CURRENT PERFORMANCE (Monitor Agent)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Revenue",
            f"${current.get('revenue', 0):.1f}M",
            delta=current.get("revenue_yoy"),
            delta_direction="positive" if "+" in str(current.get("revenue_yoy", "")) else "negative",
        )
    with col2:
        render_metric_card(
            "EBITDA",
            f"${current.get('ebitda', 0):.1f}M",
            delta=current.get("ebitda_yoy"),
            delta_direction="positive" if "+" in str(current.get("ebitda_yoy", "")) else "negative",
        )
    with col3:
        render_metric_card(
            "Margin",
            f"{current.get('margin', 0):.1f}%",
            delta=current.get("margin_change"),
            delta_direction="positive" if "+" in str(current.get("margin_change", "")) else "negative",
        )
    with col4:
        render_metric_card(
            "Cash",
            f"${current.get('cash', 0):.1f}M",
            delta=current.get("cash_status"),
            delta_direction="neutral",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Returns Projection Section
    render_section_header("RETURNS PROJECTION (Strategist Agent)")

    col1, col2 = st.columns(2)

    with col1:
        # LBO assumptions
        st.markdown("**Model Assumptions:**")
        assumption_data = f"""
        | Parameter | Value |
        |-----------|-------|
        | Entry Multiple | {returns.get('entry_multiple', 8.0)}x |
        | Exit Multiple | {returns.get('exit_multiple', 9.5)}x |
        | Holding Period | {returns.get('holding_period', 5)} years |
        | Leverage | {returns.get('leverage', 4.0)}x |
        """
        st.markdown(assumption_data)

    with col2:
        # Returns output
        rec = returns.get("recommendation", "HOLD")
        rec_color = COLORS["accent_green"] if "BUY" in rec else COLORS["accent_yellow"]

        st.markdown(f"""
        <div style="background: var(--bg-card); border-radius: 8px; padding: 1.5rem; text-align: center;">
            <div style="display: flex; justify-content: space-around; margin-bottom: 1rem;">
                <div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Projected IRR</div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: var(--accent-green);">{returns.get('projected_irr', 'N/A')}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Projected MOIC</div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: var(--accent-green);">{returns.get('projected_moic', 'N/A')}</div>
                </div>
            </div>
            <div style="font-size: 1.25rem; font-weight: 700; color: {rec_color};">{rec}</div>
        </div>
        """, unsafe_allow_html=True)

    # KPIs if available
    if kpis:
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("OPERATIONAL KPIs")
        kpi_cols = st.columns(len(kpis))
        for i, (key, value) in enumerate(kpis.items()):
            with kpi_cols[i]:
                label = key.upper().replace("_", " ")
                render_metric_card(label, str(value))


def render_risk_tab(risk_data: dict):
    """Render the Risk & Red-Flags tab."""
    legal = risk_data.get("legal_analysis", {})
    bear = risk_data.get("bear_case", {})
    alerts = risk_data.get("alerts", [])

    col1, col2 = st.columns(2)

    with col1:
        render_section_header("LEGAL ANALYSIS (Guardian Agent)")

        # Risk summary
        overall_risk = legal.get("overall_risk", "MEDIUM")
        risk_color = {
            "CRITICAL": COLORS["accent_red"],
            "HIGH": COLORS["accent_orange"],
            "MEDIUM": COLORS["accent_yellow"],
            "LOW": COLORS["accent_green"],
        }.get(overall_risk, COLORS["text_secondary"])

        st.markdown(f"""
        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            <div style="background: var(--bg-card); padding: 0.75rem 1rem; border-radius: 6px; flex: 1;">
                <div style="font-size: 0.75rem; color: var(--text-muted);">Overall Risk</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: {risk_color};">{overall_risk}</div>
            </div>
            <div style="background: var(--bg-card); padding: 0.75rem 1rem; border-radius: 6px; flex: 1;">
                <div style="font-size: 0.75rem; color: var(--text-muted);">Critical Flags</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">{legal.get('critical_flags', 0)}</div>
            </div>
            <div style="background: var(--bg-card); padding: 0.75rem 1rem; border-radius: 6px; flex: 1;">
                <div style="font-size: 0.75rem; color: var(--text-muted);">High Flags</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">{legal.get('high_flags', 0)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Key Findings:**")
        for finding in legal.get("findings", []):
            severity = finding.get("severity", "MEDIUM")
            icon = "!!" if severity == "CRITICAL" else "!" if severity == "HIGH" else "~"
            render_key_finding(icon, finding.get("text", ""), severity.lower())

    with col2:
        render_section_header("BEAR CASE (IC Agent)")

        st.markdown("**Key Risks:**")
        for risk in bear.get("risks", []):
            st.markdown(f"- {risk}")

        st.markdown("<br>**Mitigating Factors:**")
        for mitigant in bear.get("mitigants", []):
            st.markdown(f"- {mitigant}")

    # Alerts section
    if alerts:
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("ACTIVE ALERTS")
        for alert in alerts:
            severity = alert.get("severity", "medium")
            render_key_finding(
                "!!" if severity == "critical" else "!" if severity == "high" else "~",
                alert.get("message", ""),
                severity,
            )


def render_verdict_tab(verdict_data: dict, nexus_breakdown: dict):
    """Render The Verdict tab."""
    recommendation = verdict_data.get("recommendation", "FURTHER ANALYSIS")
    confidence = verdict_data.get("confidence", 50)
    thesis = verdict_data.get("thesis", "")
    conditions = verdict_data.get("conditions", [])
    next_steps = verdict_data.get("next_steps", [])

    # Score breakdown
    col1, col2 = st.columns([1, 2])

    with col1:
        render_section_header("SCORE BREAKDOWN")
        render_score_breakdown(nexus_breakdown)

    with col2:
        render_section_header("INVESTMENT RECOMMENDATION")
        render_verdict_box(recommendation, confidence, thesis)

    st.markdown("<br>", unsafe_allow_html=True)

    # Conditions and Next Steps
    if conditions:
        col1, col2 = st.columns(2)

        with col1:
            render_section_header("CONDITIONS TO PROCEED")
            for i, condition in enumerate(conditions, 1):
                st.checkbox(condition, key=f"condition_{i}")

        with col2:
            render_section_header("NEXT STEPS")
            for i, step in enumerate(next_steps, 1):
                st.markdown(f"{i}. {step}")
    else:
        render_section_header("NEXT STEPS")
        for i, step in enumerate(next_steps, 1):
            st.markdown(f"{i}. {step}")


def render_audit_trail(audit_data: dict):
    """Render the audit trail expander."""
    with st.expander("View Audit Trail", expanded=False):
        st.markdown(f"**Last Updated:** {audit_data.get('last_updated', 'N/A')}")
        st.markdown("<br>**Agent Traces:**", unsafe_allow_html=True)

        for trace in audit_data.get("agent_traces", []):
            agent = trace.get("agent", "Unknown")
            timestamp = trace.get("timestamp", "N/A")
            action = trace.get("action", "")

            # Simplify timestamp for display
            if "T" in timestamp:
                timestamp = timestamp.split("T")[1][:8]

            st.markdown(f"""
            <div style="display: flex; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-muted);">
                <span style="color: var(--accent-blue); font-weight: 600; min-width: 100px;">{agent}</span>
                <span style="color: var(--text-muted); min-width: 80px;">{timestamp}</span>
                <span style="color: var(--text-secondary);">{action}</span>
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main entry point for the Deep Dive page."""
    # Check if a company is selected
    company_id = st.session_state.get("selected_company")

    if not company_id:
        st.warning("No company selected. Redirecting to dashboard...")
        st.switch_page("app.py")
        return

    # Fetch company synthesis data
    with st.spinner("Loading company intelligence..."):
        result = api.synthesis_company(company_id)

    if result.get("success"):
        data = result
    else:
        # Use mock data when backend is offline
        st.warning("Backend offline - showing demo data")
        data = get_mock_company_data(company_id)
        data["success"] = True

    # Extract data sections
    company = data.get("company", {})
    nexus_score = data.get("nexus_score", {})
    market = data.get("market_positioning", {})
    financial = data.get("financial_health", {})
    risk = data.get("risk_analysis", {})
    verdict = data.get("verdict", {})
    audit = data.get("audit_trail", {})

    # Render header
    render_header(
        company.get("name", "Unknown Company"),
        nexus_score.get("score", 0),
        nexus_score.get("tier", "MEDIUM"),
    )

    st.markdown("---")

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Market", "Financial", "Risk", "Verdict"])

    with tab1:
        render_market_tab(market)

    with tab2:
        render_financial_tab(financial)

    with tab3:
        render_risk_tab(risk)

    with tab4:
        render_verdict_tab(verdict, nexus_score.get("breakdown", {}))

    st.markdown("---")

    # Audit trail
    render_audit_trail(audit)


if __name__ == "__main__":
    main()
