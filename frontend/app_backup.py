"""
PE-Nexus - Unified Company Intelligence Platform
Single-page application with company browse and detail views.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import get_api_client
from components.theme import apply_theme, COLORS, get_score_color, get_score_tier
from components.cards import render_metric_card, render_section_header, render_info_box
from components.charts import render_score_gauge, render_progress_bar, render_score_breakdown

# Page configuration
st.set_page_config(
    page_title="PE-Nexus | Company Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply light theme
apply_theme()

# Initialize session state
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "deal_flow"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "deal_flow"  # or "portfolio"

# Get API client
api = get_api_client()


# =============================================================================
# MOCK DATA
# =============================================================================


def get_agent_data(company_id: str, base_revenue: float) -> dict:
    """Generate agent data variations based on company ID."""
    
    # Defaults (CyberGuard / High Performer)
    scout = {
        "deal_score": 8.5,
        "priority": "HIGH",
        "industry_fit": "A",
        "signals": ["PE firm Carlyle exploring strategic review", "3 leadership hires in past 90 days", "Industry consolidation wave ongoing"],
    }
    navigator = {
        "path_to_ceo": "2 hops",
        "relationship_strength": 78,
        "intro_available": True,
        "best_path": "You → Robert Kim → Jennifer Martinez (CEO)",
    }
    strategist = {
        "entry_multiple": 8.0,
        "exit_multiple": 9.5,
        "holding_period": 5,
        "leverage": 4.0,
        "projected_irr": "24.5%",
        "projected_moic": "2.8x",
        "recommendation": "BUY",
    }
    guardian = {
        "overall_risk": "MEDIUM",
        "critical_flags": 0,
        "high_flags": 2,
        "findings": [{"severity": "HIGH", "text": "Change of Control clause"}, {"severity": "MEDIUM", "text": "Lease restriction"}],
    }
    ic = {
        "recommendation": "APPROVE WITH CONDITIONS",
        "confidence": 78,
        "thesis": "Strong platform investment opportunity.",
        "conditions": ["Negotiate Change of Control", "Secure CTO retention"],
        "next_steps": ["Management presentation", "Legal review"],
    }

    # Variations
    if company_id == "greenleaf": # Medium Performer
        scout["deal_score"] = 6.2
        scout["priority"] = "MEDIUM"
        strategist["projected_irr"] = "18.5%"
        strategist["projected_moic"] = "2.1x"
        guardian["overall_risk"] = "MEDIUM"
        ic["confidence"] = 60
        ic["recommendation"] = "HOLD"
        
    elif company_id == "fintech_one": # Low Performer
        scout["deal_score"] = 4.5
        scout["priority"] = "LOW"
        strategist["projected_irr"] = "12.0%"
        strategist["projected_moic"] = "1.5x"
        guardian["overall_risk"] = "HIGH"
        guardian["findings"].append({"severity": "CRITICAL", "text": "Regulatory investigation pending"})
        ic["confidence"] = 35
        ic["recommendation"] = "PASS"
        
    elif company_id == "techflow": # Another High Performer
        scout["deal_score"] = 8.2
        strategist["projected_irr"] = "23.0%"
        strategist["projected_moic"] = "2.6x"
        guardian["overall_risk"] = "LOW"
        ic["confidence"] = 85

    return {
        "scout_data": scout,
        "navigator_data": navigator,
        "strategist_data": strategist,
        "guardian_data": guardian,
        "ic_data": ic
    }


def calculate_nexus_metrics(scout, strategist, guardian, ic):
    """Calculate Nexus Score dynamically based on Agent inputs."""
    # 1. Market Score (Scout)
    market_score = scout.get("deal_score", 5) * 10
    
    # 2. Financial Score (Strategist) - Heuristic based on IRR
    irr_str = strategist.get("projected_irr", "15%").replace("%", "")
    try:
        irr = float(irr_str)
    except:
        irr = 15.0
    health_score = min(irr * 4, 100) 
    
    # 3. Risk Score (Guardian) - Raw Risk Level (Lower is better for company, but for Score contribution we invert)
    # If Risk is LOW (20), Safety is 80.
    risk_level = guardian.get("overall_risk", "MEDIUM")
    risk_val = 80 if risk_level == "HIGH" else 50 if risk_level == "MEDIUM" else 20
    safety_score = 100 - risk_val
    
    # 4. Confidence/Returns (IC/Strategist)
    confidence = ic.get("confidence", 50)
    
    # Returns Score (MOIC)
    moic_str = strategist.get("projected_moic", "2.0x").replace("x", "")
    try:
        moic = float(moic_str)
    except:
        moic = 2.0
    returns_score = min(moic * 30, 100) # 3.3x = 100
    
    # Weighted Nexus Score
    # Market (30%) + Health (30%) + Safety (20%) + Confidence (20%)
    weighted_score = (market_score * 0.30) + (health_score * 0.30) + (safety_score * 0.20) + (confidence * 0.20)
    
    return {
        "nexus_score": int(weighted_score),
        "nexus_breakdown": {
            "market": int(market_score),
            "health": int(health_score),
            "risk": int(risk_val), # Display Risk (Low is Good)
            "confidence": int(confidence),
            "returns": int(returns_score),
        }
    }


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_mock_companies():
    """Get companies from API leaderboard endpoint."""
    try:
        # Call the real synthesis API
        response = api.synthesis_leaderboard(min_score=0, limit=50)

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to connect to backend. Showing demo data.")
            return _get_fallback_companies()

        # Transform API response to match UI expectations
        companies = []
        for item in response.get("companies", []):
            companies.append({
                "company_id": item.get("company_id", ""),
                "company_name": item.get("company_name", "Unknown"),
                "sector": item.get("sector", "Technology"),
                "industry": item.get("industry", "Technology"),
                "revenue": item.get("revenue", 0),
                "ebitda": item.get("ebitda", 0),
                "margin": item.get("margin", 0),
                "description": item.get("summary", ""),
                "tags": item.get("tags", []),
                "status": item.get("status", "on_track"),
                "nexus_score": item.get("nexus_score", 0),
                "score_tier": item.get("score_tier", "MEDIUM"),
                # Add some defaults for fields that might not be in API response
                "founded": "N/A",
                "employees": 0,
                "headquarters": "N/A",
            })

        return companies

    except Exception as e:
        # Fall back to mock data if there's any error
        st.warning(f"Unable to connect to backend: {str(e)}. Showing demo data.")
        return _get_fallback_companies()


def _get_fallback_companies():
    """Fallback mock data when API is unavailable."""
    base_companies = [
        {
            "company_id": "cyberguard",
            "company_name": "CyberGuard Systems",
            "sector": "Cybersecurity",
            "industry": "Technology",
            "revenue": 45.5,
            "ebitda": 12.4,
            "margin": 27.2,
            "description": "Leading provider of AI-driven threat detection.",
            "founded": "2018",
            "employees": 240,
            "headquarters": "San Francisco, CA",
            "tags": ["HIGH GROWTH", "PE INTEREST"],
            "status": "outperforming"
        },
        {
            "company_id": "techflow",
            "company_name": "TechFlow Solutions",
            "sector": "B2B SaaS",
            "industry": "Technology",
            "revenue": 52.0,
            "ebitda": 13.0,
            "margin": 25.0,
            "description": "Enterprise workflow automation software.",
            "founded": "2019",
            "employees": 180,
            "headquarters": "Austin, TX",
            "tags": ["OUTPERFORMING"],
            "status": "outperforming",
        },
        {
            "company_id": "healthbridge",
            "company_name": "HealthBridge Analytics",
            "sector": "Healthcare IT",
            "industry": "Healthcare",
            "revenue": 38.5,
            "ebitda": 8.5,
            "margin": 22.1,
            "description": "Data analytics for healthcare providers.",
            "founded": "2017",
            "employees": 120,
            "headquarters": "Boston, MA",
            "tags": ["HIGH GROWTH"],
            "status": "on_track",
        },
    ]

    # Calculate scores on the fly for fallback data
    for c in base_companies:
        data = get_agent_data(c["company_id"], c["revenue"])
        metrics = calculate_nexus_metrics(
            data["scout_data"],
            data["strategist_data"],
            data["guardian_data"],
            data["ic_data"]
        )
        c["nexus_score"] = metrics["nexus_score"]
        c["score_tier"] = get_score_tier(metrics["nexus_score"])

    return base_companies


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_mock_company_detail(company_id: str) -> dict:
    """Get detailed company data from API synthesis endpoint."""
    try:
        # Call the real synthesis company API
        response = api.synthesis_company(company_id)

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to load company details from backend. Showing demo data.")
            return _get_fallback_company_detail(company_id)

        # Extract data from API response
        company_info = response.get("company", {})
        nexus_score_data = response.get("nexus_score", {})
        market_positioning = response.get("market_positioning", {})
        financial_health = response.get("financial_health", {})
        risk_analysis = response.get("risk_analysis", {})
        verdict = response.get("verdict", {})

        # Transform to match UI expectations
        scout_data = market_positioning.get("scout_data", {})
        navigator_data = market_positioning.get("navigator_data", {})
        current_perf = financial_health.get("current_performance", {})
        returns_proj = financial_health.get("returns_projection", {})
        legal_analysis = risk_analysis.get("legal_analysis", {})
        ic_data = verdict.get("ic_data", {})

        return {
            "company_id": company_id,
            "company_name": company_info.get("name", "Unknown"),
            "sector": company_info.get("sector", "Technology"),
            "industry": company_info.get("industry", "Technology"),
            "status": company_info.get("status", "on_track"),
            "revenue": current_perf.get("revenue", 0),
            "ebitda": current_perf.get("ebitda", 0),
            "margin": current_perf.get("margin", 0),
            "description": f"{company_info.get('name', 'Company')} - AI-generated analysis",
            "founded": "N/A",
            "employees": 150,
            "headquarters": "United States",
            "tags": [],
            "contacts": [
                {"name": "CEO", "role": "Chief Executive Officer", "color": "#3B82F6"},
                {"name": "CFO", "role": "Chief Financial Officer", "color": "#10B981"},
                {"name": "CTO", "role": "Chief Technology Officer", "color": "#8B5CF6"},
            ],
            "scout_data": scout_data,
            "navigator_data": navigator_data,
            "strategist_data": {
                "entry_multiple": returns_proj.get("entry_multiple", 8.0),
                "exit_multiple": returns_proj.get("exit_multiple", 9.5),
                "holding_period": returns_proj.get("holding_period", 5),
                "leverage": returns_proj.get("leverage", 4.0),
                "projected_irr": returns_proj.get("projected_irr", "20%"),
                "projected_moic": returns_proj.get("projected_moic", "2.5x"),
                "recommendation": returns_proj.get("recommendation", "HOLD"),
            },
            "guardian_data": {
                "overall_risk": legal_analysis.get("overall_risk", "MEDIUM"),
                "critical_flags": legal_analysis.get("critical_flags", 0),
                "high_flags": legal_analysis.get("high_flags", 0),
                "findings": legal_analysis.get("findings", []),
            },
            "ic_data": ic_data,
            "financial_data": current_perf,
            "nexus_score": nexus_score_data.get("score", 0),
            "nexus_breakdown": nexus_score_data.get("breakdown", {}),
            "news": [
                {"author": "Scout Agent", "date": "Today", "title": f"Analysis completed for {company_info.get('name', 'company')}"},
                {"author": "Market Intel", "date": "Yesterday", "title": "Recent market activity detected"},
            ],
            "competitor_news": [
                {"author": "Industry Watch", "date": "2 days ago", "title": "Competitive landscape analysis available"},
            ],
            "competitors": [],
        }

    except Exception as e:
        st.warning(f"Unable to load company details: {str(e)}. Showing demo data.")
        return _get_fallback_company_detail(company_id)


def _get_fallback_company_detail(company_id: str) -> dict:
    """Fallback mock company detail when API is unavailable."""
    companies = {c["company_id"]: c for c in _get_fallback_companies()}
    base = companies.get(company_id, list(companies.values())[0] if companies else {})

    # Regenerate the SAME agent data to populate the detail view tabs
    agent_data = get_agent_data(base.get("company_id", "demo"), base.get("revenue", 50))
    metrics = calculate_nexus_metrics(
        agent_data["scout_data"],
        agent_data["strategist_data"],
        agent_data["guardian_data"],
        agent_data["ic_data"]
    )

    # Financial Data Helper
    financial_data = {
        "revenue": base.get("revenue", 50),
        "ebitda": base.get("ebitda", 10),
        "margin": base.get("margin", 20),
        "revenue_yoy": "+12%",
        "ebitda_yoy": "+18%",
        "margin_change": "+2.5pp",
        "cash": 12.4,
    }

    return {
        **base,
        "contacts": [
            {"name": "Jennifer Martinez", "role": "CEO", "color": "#3B82F6"},
            {"name": "Robert Kim", "role": "CFO", "color": "#10B981"},
            {"name": "Sarah Chen", "role": "CTO", "color": "#8B5CF6"},
        ],
        **agent_data,
        "financial_data": financial_data,
        "nexus_score": metrics["nexus_score"],
        "nexus_breakdown": metrics["nexus_breakdown"],
        "news": [
            {"author": "Demo", "date": "Today", "title": "Demo data - start backend to see real agent analysis"},
        ],
        "competitor_news": [],
        "competitors": [],
    }


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_mock_portfolio():
    """Get portfolio companies from Monitor API."""
    try:
        # Call the real monitor API
        response = api.monitor_companies()

        if not response.get("success", False):
            # Fall back to mock data if API fails
            st.warning("Unable to connect to Monitor agent. Showing demo portfolio data.")
            return _get_fallback_portfolio()

        # Transform API response to match UI expectations
        companies = []
        for company in response.get("companies", []):
            companies.append({
                "company_id": company.get("id", ""),
                "company_name": company.get("name", "Unknown"),
                "sector": company.get("sector", company.get("industry", "Technology")),
                "acquisition_date": company.get("acquisition_date", "N/A"),
                "invested_capital": company.get("invested_capital", 0),
                "current_valuation": company.get("current_valuation", 0),
                "irr": company.get("irr", 0),
                "moic": company.get("moic", 1.0),
                "status": company.get("status", "on_track"),
                "description": company.get("description", ""),
                "metrics": {
                    "revenue": company.get("revenue", 0),
                    "ebitda": company.get("ebitda", 0),
                    "margin": company.get("margin", 0),
                },
                "vcp_status": int(company.get("vcp_progress", 0) * 100) if isinstance(company.get("vcp_progress"), float) else company.get("vcp_progress", 50),
            })

        return companies

    except Exception as e:
        st.warning(f"Unable to load portfolio: {str(e)}. Showing demo data.")
        return _get_fallback_portfolio()


def _get_fallback_portfolio():
    """Fallback mock portfolio when API is unavailable."""
    return [
        {
            "company_id": "apex_manufacturing",
            "company_name": "Apex Manufacturing",
            "sector": "Industrial",
            "acquisition_date": "2022-06-15",
            "invested_capital": 45.0,
            "current_valuation": 62.5,
            "irr": 22.5,
            "moic": 1.39,
            "status": "on_track",
            "description": "Precision parts manufacturer for aerospace and defense sectors.",
            "metrics": {"revenue": 85.0, "ebitda": 14.5, "margin": 17.0},
            "vcp_status": 65,
        },
        {
            "company_id": "cloud_health",
            "company_name": "CloudHealth Solutions",
            "sector": "Healthcare IT",
            "acquisition_date": "2023-01-10",
            "invested_capital": 30.0,
            "current_valuation": 38.2,
            "irr": 28.1,
            "moic": 1.27,
            "status": "outperforming",
            "description": "SaaS platform for patient record management and billing.",
            "metrics": {"revenue": 22.0, "ebitda": 4.5, "margin": 20.5},
            "vcp_status": 40,
        },
        {
            "company_id": "nordic_foods",
            "company_name": "Nordic Foods Group",
            "sector": "Consumer",
            "acquisition_date": "2021-11-20",
            "invested_capital": 60.0,
            "current_valuation": 55.0,
            "irr": -4.2,
            "moic": 0.92,
            "status": "at_risk",
            "description": "Premium frozen food manufacturer distributing across Northern Europe.",
            "metrics": {"revenue": 150.0, "ebitda": 12.0, "margin": 8.0},
            "vcp_status": 80,
        }
    ]

# =============================================================================
# BROWSE VIEW COMPONENTS
# =============================================================================

def render_top_navbar():
    """Render the top navigation bar."""
    # Create Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
            <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #1F2937;">PE-NEXUS</h1>
            <span style="color: #9CA3AF; font-size: 1.2rem;">|</span>
            <span style="color: #6B7280; font-size: 1rem; font-weight: 500;">
                {st.session_state.app_mode.replace('_', ' ').title()}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        c_nav1, c_nav2 = st.columns([1, 1])
        with c_nav1:
            if st.button("Deal Flow (Search)", type="primary" if st.session_state.app_mode == "deal_flow" else "secondary", use_container_width=True):
                st.session_state.app_mode = "deal_flow"
                st.session_state.selected_company = None
                st.rerun()
        with c_nav2:
             if st.button("Portfolio (Acquired)", type="primary" if st.session_state.app_mode == "portfolio" else "secondary", use_container_width=True):
                st.session_state.app_mode = "portfolio"
                st.session_state.selected_company = None
                st.rerun()


def render_company_grid_card(company: dict) -> bool:
    """Render a company card for the grid. Returns True if clicked."""
    score_color = get_score_color(company["nexus_score"])
    score_tier = company.get("score_tier", get_score_tier(company["nexus_score"]))
    initials = "".join([w[0] for w in company["company_name"].split()[:2]])
    
    # Tags HTML
    tags_html = ""
    for tag in company.get("tags", [])[:2]:
        tag_lower = tag.lower().replace(" ", "-").replace("_", "-")
        tag_class = {
            "high-growth": "tag-high-growth",
            "pe-interest": "tag-pe-interest",
            "outperforming": "tag-outperforming",
            "at-risk": "tag-at-risk",
            "watch": "tag-watch",
            "expansion": "tag-expansion",
        }.get(tag_lower, "tag-default")
        tags_html += f'<span class="tag {tag_class}">{tag}</span>'
    
    st.markdown(f"""
    <div class="company-card">
        <div class="company-card-header">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div class="company-card-logo">{initials}</div>
                <div>
                    <div class="company-name">{company["company_name"]}</div>
                    <div class="company-sector">{company["sector"]}</div>
                </div>
            </div>
            <div class="nexus-score">
                <span class="nexus-score-label">Score</span>
                <span class="nexus-score-value nexus-score-{score_tier.lower()}">{company["nexus_score"]}</span>
            </div>
        </div>
        <div class="company-financials">
            <span class="company-financial-item">
                Revenue: <span class="company-financial-value">${company["revenue"]:.1f}M</span>
            </span>
            <span class="company-financial-item">
                EBITDA: <span class="company-financial-value">${company["ebitda"]:.1f}M</span>
            </span>
            <span class="company-financial-item">
                Margin: <span class="company-financial-value">{company["margin"]:.1f}%</span>
            </span>
        </div>
        <div class="company-footer">
            <div>{tags_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Use both company_id and index to ensure unique keys
    button_key = f"view_{company.get('company_id', 'unknown')}_{hash(company.get('company_name', ''))}"
    return st.button("View Details", key=button_key, type="primary", use_container_width=True)


def render_browse_view():
    """Render the company browse/search view."""
    # render_header() is handled by main nav now
    pass
    
    # Search box
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("Search")
        search = st.text_input("Search", value=st.session_state.search_query, label_visibility="collapsed", placeholder="Search by company name or sector...")
        st.session_state.search_query = search
    
    with col2:
        st.caption("Industry")
        industry_filter = st.selectbox("Industry", ["All Industries", "Technology", "Healthcare", "Industrial", "Financial Services"], label_visibility="collapsed")
        industry_filter = "All" if industry_filter == "All Industries" else industry_filter
    
    with col3:
        st.caption("Nexus Score")
        score_filter = st.selectbox("Score", ["All Scores", "High (75+)", "Medium (50-74)", "Low (<50)"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Get companies
    companies = get_mock_companies()
    
    # Apply filters
    if search:
        companies = [c for c in companies if search.lower() in c["company_name"].lower() or search.lower() in c["sector"].lower()]
    
    if industry_filter != "All":
        companies = [c for c in companies if c["industry"] == industry_filter]
    
    if score_filter == "High (75+)":
        companies = [c for c in companies if c["nexus_score"] >= 75]
    elif score_filter == "Medium (50-74)":
        companies = [c for c in companies if 50 <= c["nexus_score"] < 75]
    elif score_filter == "Low (<50)":
        companies = [c for c in companies if c["nexus_score"] < 50]
    
    if not companies:
        st.info("No companies match your search criteria.")
        return
    
    # Display companies in grid
    cols = st.columns(3)
    for i, company in enumerate(companies):
        with cols[i % 3]:
            if render_company_grid_card(company):
                st.session_state.selected_company = company["company_id"]
                st.rerun()


# =============================================================================
# DETAIL VIEW COMPONENTS
# =============================================================================

def render_profile_header(company: dict):
    """Render the company profile header using native components."""
    
    # Top level header with back button integration option
    # (Back button is handled in render_detail_view, so we focus on content here)
    
    col_logo, col_info, col_metrics = st.columns([1, 3, 4])
    
    with col_logo:
        initials = "".join([w[0] for w in company["company_name"].split()[:2]])
        st.markdown(f"""
        <div style="width: 80px; height: 80px; background-color: #3B82F6; color: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 700;">
            {initials}
        </div>
        """, unsafe_allow_html=True)
    
    with col_info:
        st.title(company["company_name"])
        
        # Status Badge
        status_colors = {
            "outperforming": ("#10B981", "rgba(16, 185, 129, 0.1)"),
            "on_track": ("#3B82F6", "rgba(59, 130, 246, 0.1)"),
            "watch": ("#F59E0B", "rgba(245, 158, 11, 0.1)"),
            "at_risk": ("#EF4444", "rgba(239, 68, 68, 0.1)"),
        }
        badge_color, badge_bg = status_colors.get(company.get("status", "on_track"), ("#3B82F6", "rgba(59, 130, 246, 0.1)"))
        
        st.markdown(f"""
        <div style="display: flex; gap: 1rem; align-items: center; margin-top: -0.5rem;">
            <span style="background-color: {badge_bg}; color: {badge_color}; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid {badge_color}30;">
                {company.get("status", "Active").replace("_", " ").upper()}
            </span>
            <span style="color: #6B7280; font-size: 0.9rem;">{company["sector"]} • {company.get("headquarters", "United States")}</span>
        </div>
        """, unsafe_allow_html=True)

    with col_metrics:
        m1, m2, m3 = st.columns(3)
        score_color = get_score_color(company["nexus_score"])
        with m1:
            st.metric("Revenue", f"${company['revenue']:.0f}M")
        with m2:
            st.metric("Employees", company.get("employees", 150))
        with m3:
            st.markdown(f"""
            <div style="text-align: left;">
                <p style="font-size: 0.8rem; margin-bottom: 0px; color: rgb(49, 51, 63);">Nexus Score</p>
                <p style="font-size: 1.8rem; font-weight: 600; margin: 0px; color: {score_color};">{company['nexus_score']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()


def render_about_section(company: dict):
    """Render the About Company section."""
    with st.container(border=True):
        st.subheader("About Company")
        st.markdown(company.get("description", "No description available."))
        
        st.write("") # Spacer
        st.caption("TAGS")
        
        # Tags using standard pills or badges
        tags_html = ""
        for tag in company.get("tags", []):
            tag_class = "tag-default" # Simplified styling
            # Using inline style for tags within markdown to keep it simple but nice
            tags_html += f'<span style="background-color: #EFF6FF; color: #1D4ED8; padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; margin-right: 8px; border: 1px solid #DBEAFE;">{tag}</span>'
        
        st.markdown(tags_html, unsafe_allow_html=True)
        
        st.write("")
        st.caption("SOCIAL")
        col_s1, col_s2, col_s3, _ = st.columns([1, 1, 1, 10])
        with col_s1:
            st.button("In", key="linkedin", help="LinkedIn")
        with col_s2:
            st.button("X", key="twitter", help="X / Twitter")
        with col_s3:
            st.button("Web", key="website", help="Website")


def render_contacts_section(contacts: list):
    """Render the Primary Contacts section."""
    with st.container(border=True):
        st.subheader("Primary Contacts")
        
        for contact in contacts:
            c1, c2 = st.columns([1, 4])
            with c1:
                initials = "".join([w[0] for w in contact["name"].split()[:2]])
                st.markdown(f"""
                <div style="width: 40px; height: 40px; background-color: {contact.get('color', '#3B82F6')}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 600;">
                    {initials}
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{contact['name']}**")
                st.caption(contact["role"])


def render_scout_section(scout_data: dict):
    """Render Scout Agent data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([4, 1])
        with c_head:
            st.subheader("🔍 Market Intelligence")
        with c_btn:
            if st.button("Agent Analysis →", key="btn_scout"):
                st.session_state.selected_agent = "Scout Agent"
                st.rerun()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            render_metric_card("Deal Score", f"{scout_data.get('deal_score', 0)}/10")
        with col2:
            render_metric_card("Priority", scout_data.get("priority", "N/A"))
        with col3:
            render_metric_card("Industry Fit", scout_data.get("industry_fit", "N/A"))
        
        st.write("")
        st.markdown("**Key Signals**")
        for signal in scout_data.get("signals", []):
            st.markdown(f"- {signal}")


def render_navigator_section(navigator_data: dict):
    """Render Navigator Agent data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([4, 1])
        with c_head:
            st.subheader("🤝 Relationship Intelligence")
        with c_btn:
            if st.button("Agent Analysis →", key="btn_navigator"):
                st.session_state.selected_agent = "Navigator Agent"
                st.rerun()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            render_metric_card("Path to CEO", navigator_data.get("path_to_ceo", "N/A"))
        with col2:
            render_metric_card("Strength", f"{navigator_data.get('relationship_strength', 0)}%")
        with col3:
            intro = "✓ Yes" if navigator_data.get("intro_available") else "✗ No"
            render_metric_card("Intro Available", intro)
        
        st.info(f"**Best Path:** {navigator_data.get('best_path', 'No path found')}")


def render_financial_section(financial_data: dict, strategist_data: dict, key_suffix: str = ""):
    """Render financial and strategist data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([4, 1])
        with c_head:
            st.subheader("💰 Financial Analysis")
        with c_btn:
            if st.button("Agent Analysis →", key=f"btn_strategist{key_suffix}"):
                st.session_state.selected_agent = "Strategist Agent"
                st.rerun()
        
        # Current performance
        st.caption("CURRENT PERFORMANCE")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Revenue", f"${financial_data.get('revenue', 0):.1f}M", 
                              delta=financial_data.get('revenue_yoy'), delta_direction="positive")
        with col2:
            render_metric_card("EBITDA", f"${financial_data.get('ebitda', 0):.1f}M",
                              delta=financial_data.get('ebitda_yoy'), delta_direction="positive")
        with col3:
            render_metric_card("Margin", f"{financial_data.get('margin', 0):.1f}%",
                              delta=financial_data.get('margin_change'), delta_direction="positive")
        with col4:
            render_metric_card("Cash", f"${financial_data.get('cash', 0):.1f}M")
        
        st.divider()
        st.caption("LBO MODEL PROJECTIONS")
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe({
                "Parameter": ["Entry Multiple", "Exit Multiple", "Holding Period", "Leverage"],
                "Value": [
                    f"{strategist_data.get('entry_multiple', 8.0)}x",
                    f"{strategist_data.get('exit_multiple', 9.5)}x",
                    f"{strategist_data.get('holding_period', 5)} years",
                    f"{strategist_data.get('leverage', 4.0)}x"
                ]
            }, hide_index=True, use_container_width=True)
        
        with col2:
            rec = strategist_data.get("recommendation", "HOLD")
            rec_color = "#10B981" if "BUY" in rec else "#F59E0B"
            bg_color = "rgba(16, 185, 129, 0.1)" if "BUY" in rec else "rgba(245, 158, 11, 0.1)"
            
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("IRR", strategist_data.get('projected_irr', 'N/A'))
                with c2:
                    st.metric("MOIC", strategist_data.get('projected_moic', 'N/A'))
                
                st.divider()
                st.markdown(f"""
                <div style="text-align: center;">
                    <span style="font-size: 1.2rem; font-weight: 700; color: {rec_color}; background: {bg_color}; padding: 0.5rem 1.5rem; border-radius: 999px;">
                        {rec}
                    </span>
                </div>
                """, unsafe_allow_html=True)


def render_risk_section(guardian_data: dict):
    """Render Guardian Agent risk analysis."""
    with st.container(border=True):
        c_head, c_btn = st.columns([4, 1])
        with c_head:
            st.subheader("⚠️ Risk Analysis")
        with c_btn:
            if st.button("Agent Analysis →", key="btn_guardian"):
                st.session_state.selected_agent = "Guardian Agent"
                st.rerun()
        
        overall_risk = guardian_data.get("overall_risk", "MEDIUM")
        risk_color = "#EF4444" if overall_risk == "CRITICAL" else "#F97316" if overall_risk == "HIGH" else "#F59E0B" if overall_risk == "MEDIUM" else "#10B981"
        
        col1, col2, col3 = st.columns(3)
        with col1:
             st.markdown(f"""
            <div style="padding: 1rem; border-radius: 8px; background-color: {risk_color}15; border: 1px solid {risk_color}30;">
                <p style="font-size: 0.8rem; margin: 0; color: #4B5563;">Overall Risk</p>
                <p style="font-size: 1.2rem; font-weight: 700; margin: 0; color: {risk_color};">{overall_risk}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            render_metric_card("Critical Flags", str(guardian_data.get("critical_flags", 0)))
        with col3:
            render_metric_card("High Flags", str(guardian_data.get("high_flags", 0)))
        
        st.write("")
        st.caption("KEY FINDINGS")
        for finding in guardian_data.get("findings", []):
            severity = finding.get("severity", "MEDIUM")
            color = "#EF4444" if severity == "CRITICAL" else "#F97316" if severity == "HIGH" else "#F59E0B"
            st.markdown(f"""
            <div style="padding: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid {color}; background-color: #F9FAFB;">
                <span style="font-weight: 600; color: {color}; font-size: 0.8rem;">{severity}</span>
                <span style="font-size: 0.9rem; color: #374151; margin-left: 0.5rem;">{finding.get('text', '')}</span>
            </div>
            """, unsafe_allow_html=True)


def render_verdict_section(ic_data: dict, nexus_breakdown: dict, key_suffix: str = ""):
    """Render the IC Agent verdict using native components."""
    recommendation = ic_data.get("recommendation", "FURTHER ANALYSIS")
    confidence = ic_data.get("confidence", 50)
    rec_class = "verdict-approve" if "APPROVE" in recommendation and "CONDITION" not in recommendation else \
                "verdict-conditional" if "CONDITION" in recommendation else "verdict-reject"
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.subheader("Score Breakdown")
            
            labels = {
                "market": "Market Position",
                "health": "Financial Health",
                "risk": "Risk Level",
                "confidence": "IC Confidence",
                "returns": "Returns Potential",
            }
            
            for key, score in nexus_breakdown.items():
                label = labels.get(key, key.title())
                bar_value = (100 - score) if key == "risk" else score
                st.progress(bar_value / 100, text=f"{label}: {score}") # Improved text display
    
    with col2:
        with st.container(border=True):
            c_head, c_btn = st.columns([3, 1])
            with c_head:
                st.subheader("🎯 Investment Recommendation")
            with c_btn:
                if st.button("Agent Analysis →", key=f"btn_ic{key_suffix}"):
                    st.session_state.selected_agent = "IC Agent"
                    st.rerun()
            
            # Recommendation Banner
            bg = "#ECFDF5" if "APPROVE" in recommendation else "#FFFBEB"
            color = "#047857" if "APPROVE" in recommendation else "#B45309"
            
            st.markdown(f"""
            <div style="background-color: {bg}; border: 1px solid {color}40; border-radius: 8px; padding: 1.5rem; text-align: center; margin: 1rem 0;">
                <h2 style="color: {color}; margin: 0; font-size: 1.5rem;">{recommendation}</h2>
                <p style="color: {color}; margin: 0.5rem 0 0 0; font-weight: 500;">Confidence Score: {confidence}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("INVESTMENT THESIS")
            st.info(ic_data.get('thesis', ''))

    # Conditions and next steps
    if ic_data.get("conditions"):
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Conditions")
                for condition in ic_data.get("conditions", []):
                    st.checkbox(condition, key=f"cond_{condition[:10]}")
        
        with col2:
             with st.container(border=True):
                st.subheader("Next Steps")
                for i, step in enumerate(ic_data.get("next_steps", []), 1):
                    st.markdown(f"**{i}.** {step}")


def render_news_section(company_news: list, competitor_news: list):
    """Render the news sections."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="profile-card">
            <div class="profile-card-header">
                <h3 class="profile-card-title">Company News</h3>
                <span class="profile-card-action">View More</span>
            </div>
        """, unsafe_allow_html=True)
        
        for news in company_news[:3]:
            initials = "".join([w[0] for w in news["author"].split()[:2]])
            st.markdown(f"""
            <div class="news-item">
                <div class="news-avatar">{initials}</div>
                <div class="news-content">
                    <span class="news-author">{news["author"]}</span>
                    <span class="news-date">• {news["date"]}</span>
                    <div class="news-title">{news["title"][:80]}...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="profile-card">
            <div class="profile-card-header">
                <h3 class="profile-card-title">Competitor News</h3>
                <span class="profile-card-action">View More</span>
            </div>
        """, unsafe_allow_html=True)
        
        for news in competitor_news[:3]:
            initials = "".join([w[0] for w in news["author"].split()[:2]])
            st.markdown(f"""
            <div class="news-item">
                <div class="news-avatar" style="background-color: #8B5CF6;">{initials}</div>
                <div class="news-content">
                    <span class="news-author">{news["author"]}</span>
                    <span class="news-date">• {news["date"]}</span>
                    <div class="news-title">{news["title"][:80]}...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_detail_view():
    """Render the company detail view."""
    company_id = st.session_state.selected_company
    
    # Back button
    if st.button("← Back to Companies"):
        st.session_state.selected_company = None
        st.rerun()
    
    # Get company data
    company = get_mock_company_detail(company_id)
    
    # Render header
    render_profile_header(company)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Analytics", "News", "Comparison"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            render_about_section(company)
        with col2:
            render_contacts_section(company["contacts"])
        
        # Agent sections
        col1, col2 = st.columns(2)
        with col1:
            render_scout_section(company["scout_data"])
        with col2:
            render_navigator_section(company["navigator_data"])
        
        render_financial_section(company["financial_data"], company["strategist_data"], key_suffix="_overview")
        render_risk_section(company["guardian_data"])
        render_verdict_section(company["ic_data"], company["nexus_breakdown"], key_suffix="_overview")
    
    with tab2:
        render_financial_section(company["financial_data"], company["strategist_data"], key_suffix="_analytics")
        
        # Additional charts would go here
        st.markdown("""
        <div class="profile-card">
            <div class="profile-card-header">
                <h3 class="profile-card-title">Growth Trends</h3>
            </div>
            <div style="height: 200px; background: linear-gradient(135deg, #F5F7FB 0%, #EEF2F7 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9CA3AF;">
                📈 Revenue & EBITDA growth charts would render here
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        render_news_section(company["news"], company["competitor_news"])
    
    with tab4:
        st.markdown("""
        <div class="profile-card">
            <div class="profile-card-header">
                <h3 class="profile-card-title">Competitive Analysis</h3>
            </div>
        """, unsafe_allow_html=True)
        
        for comp in company["competitors"]:
            change_color = "#10B981" if comp["change"] > 0 else "#EF4444"
            change_sign = "+" if comp["change"] > 0 else ""
            st.markdown(f"""
            <div class="competitor-row">
                <div class="competitor-logo">📊</div>
                <div class="competitor-info">
                    <div class="competitor-name">{comp["name"]}</div>
                    <div class="competitor-desc">{comp["description"]}</div>
                </div>
                <div class="competitor-trend">
                    <span style="color: {change_color}; font-weight: 600;">{change_sign}{comp["change"]}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)



def render_agent_deep_dive():
    """Render the deep dive view for a selected agent."""
    agent_name = st.session_state.selected_agent
    company_id = st.session_state.selected_company
    company = get_mock_company_detail(company_id)
    
    # Back navigation
    if st.button("← Back to Company Profile"):
        st.session_state.selected_agent = None
        st.rerun()
        
    st.title(f"{agent_name} Analysis")
    st.caption(f"Deep dive analysis for {company['company_name']}")
    
    st.divider()
    
    # Render specific agent content
    if agent_name == "Scout Agent":
        with st.container(border=True):
            st.subheader("Market Intelligence Overview")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Deal Score", f"{company['scout_data'].get('deal_score', 0)}/10")
                st.metric("Priority", company['scout_data'].get("priority", "N/A"))
            with col2:
                st.metric("Industry Fit", company['scout_data'].get("industry_fit", "N/A"))
                
            st.divider()
            st.subheader("Analysis Signals")
            for signal in company['scout_data'].get("signals", []):
                st.info(signal, icon="📡")
            
            st.write("")
            st.subheader("Raw Market Data")
            st.dataframe({
                "Metric": ["Market Growth", "Competitor Activity", "Regulatory Risk"],
                "Value": ["High", "Medium", "Low"],
                "Source": ["Crunchbase", "PitchBook", "Public Filings"]
            }, use_container_width=True)
        
    elif agent_name == "Navigator Agent":
        render_navigator_section(company["navigator_data"])
        st.subheader("Relationship Graph")
        
        st.graphviz_chart('''
            digraph {
                rankdir=LR;
                node [shape=box style="filled,rounded" fillcolor="#EFF6FF" fontname="Helvetica" color="#DBEAFE"];
                edge [fontname="Helvetica" color="#9CA3AF" fontsize=10];
                
                "You" [fillcolor="#3B82F6" fontcolor="white"];
                "Robert Kim\n(CFO)" [fillcolor="#EFF6FF"];
                "Jennifer Martinez\n(CEO)" [fillcolor="#10B981" fontcolor="white"];
                
                "You" -> "Robert Kim\n(CFO)" [label=" Shared Board Member "];
                "Robert Kim\n(CFO)" -> "Jennifer Martinez\n(CEO)" [label=" former Colleague "];
            }
        ''', use_container_width=True)
        
    elif agent_name == "Strategist Agent":
        st.subheader("Financial Statements")
        tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow", "LBO Model"])
        with tabs[0]:
            st.dataframe({"Year": [2022, 2023, 2024], "Revenue": [40, 65, 85.2], "EBITDA": [5, 12, 21.3]}, use_container_width=True)
        with tabs[3]:
             render_financial_section(company["financial_data"], company["strategist_data"], key_suffix="_deepdive")
        
    elif agent_name == "Guardian Agent":
        render_risk_section(company["guardian_data"])
        st.subheader("Legal Document Repository")
        st.dataframe({
             "Document": ["Vendor Agreement", "Office Lease", "Employment Contracts"],
             "Status": ["Flagged", "Review Complete", "Pending"],
             "Risk Level": ["High", "Medium", "Low"]
        }, use_container_width=True)
        
    elif agent_name == "IC Agent":
        c1, c2 = st.columns([1, 1])
        with c1:
            render_score_breakdown(company["nexus_breakdown"])
        with c2:
            render_verdict_section(company["ic_data"], company["nexus_breakdown"], key_suffix="_deepdive")
        
        st.divider()
        st.subheader("Investment Discussion")
        st.text_area("Add notes to Investment Memo...", height=200)


def render_portfolio_dashboard():
    """Render the Portfolio Management Dashboard."""
    portfolio = get_mock_portfolio()
    
    # Portfolio Summary Logic
    total_invested = sum(c['invested_capital'] for c in portfolio)
    total_value = sum(c['current_valuation'] for c in portfolio)
    avg_irr = sum(c['irr'] for c in portfolio) / len(portfolio) if portfolio else 0
    active_companies = len(portfolio)
    
    st.title("Portfolio Overview")
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Invested", f"${total_invested:.1f}M")
    with col2:
        render_metric_card("Current FMV", f"${total_value:.1f}M", delta=f"+{(total_value-total_invested):.1f}M", delta_direction="positive")
    with col3:
        render_metric_card("Portfolio IRR", f"{avg_irr:.1f}%")
    with col4:
        render_metric_card("Active Companies", str(active_companies))
        
    st.divider()
    
    # Portfolio Grid
    st.subheader("Acquired Companies")
    
    cols = st.columns(3)
    for i, company in enumerate(portfolio):
        # Calculate status color
        status_color = "#10B981" if company['status'] == 'outperforming' else "#F59E0B" if company['status'] == 'on_track' else "#EF4444"
        
        with cols[i % 3]:
            with st.container(border=True):
                # Header
                c1, c2 = st.columns([3, 1])
                with c1:
                    initials = "".join([w[0] for w in company["company_name"].split()[:2]])
                    st.markdown(f"**{company['company_name']}**")
                    st.caption(f"{company['sector']}")
                with c2:
                    st.markdown(f"""
                    <div style="text-align: right;">
                        <span style="color: {status_color}; font-size: 0.8rem; font-weight: 600;">{company['status'].upper().replace('_', ' ')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Metrics
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("IRR", f"{company['irr']}%")
                with m2:
                    st.metric("MOIC", f"{company['moic']}x")
                
                st.write("")
                st.progress(company['vcp_status'] / 100, text=f"Value Creation Plan: {company['vcp_status']}%")
                
                st.write("")
                if st.button("Manage Asset →", key=f"btn_manage_{company['company_id']}", use_container_width=True):
                    st.session_state.selected_company = company['company_id']
                    st.rerun()


def render_portfolio_company_detail():
    """Render the detailed view for a portfolio company."""
    company_id = st.session_state.selected_company
    portfolio = {c["company_id"]: c for c in get_mock_portfolio()}
    company = portfolio.get(company_id)
    
    if not company:
        st.error("Company not found.")
        if st.button("Back to Dashboard"):
            st.session_state.selected_company = None
            st.rerun()
        return

    # Back button
    if st.button("← Back to Portfolio Dashboard", key="btn_back_port"):
        st.session_state.selected_company = None
        st.rerun()
        
    # Header
    st.title(company["company_name"])
    st.caption(f"{company['sector']} | Acquired: {company['acquisition_date']}")
    
    # Key Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Invested Capital", f"${company['invested_capital']}M")
    with c2:
        render_metric_card("Current Valuation", f"${company['current_valuation']}M", 
                          delta=f"{(company['current_valuation']/company['invested_capital']):.2f}x", delta_direction="positive")
    with c3:
        render_metric_card("IRR", f"{company['irr']}%")
    with c4:
        render_metric_card("VCP Status", f"{company['vcp_status']}%")
        
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Value Creation (Operating Partner)", "💰 Financials (Strategist)", "⚖️ Compliance (Guardian)"])
    
    with tab1:
        with st.container(border=True):
            st.subheader("Operating Partner Agent")
            st.info("Tracking 100-Day Plan and Strategic Initiatives")
            
            # Mock Initiatives
            initiatives = [
                {"name": "Executive Team Recruitment", "progress": 80, "status": "On Track"},
                {"name": "Cloud Migration", "progress": 45, "status": "Delayed"},
                {"name": "Sales Force Optimization", "progress": 20, "status": "On Track"},
                {"name": "Pricing Strategy Rollout", "progress": 60, "status": "At Risk"},
            ]
            
            for init in initiatives:
                color = "#EF4444" if init['status'] == "At Risk" else "#F59E0B" if init['status'] == "Delayed" else "#10B981"
                c_label, c_bar = st.columns([1, 2])
                with c_label:
                    st.markdown(f"**{init['name']}**")
                    st.caption(init['status'])
                with c_bar:
                    st.progress(init['progress']/100, text=f"{init['progress']}%")
    
    with tab2:
        with st.container(border=True):
            st.subheader("Strategist Agent")
            st.caption("Budget vs Actuals (YTD)")
            
            # Mock Financials
            st.dataframe({
                "Metric": ["Revenue", "EBITDA", "Gross Margin", "OpEx"],
                "Actual (YTD)": [45.2, 12.1, "42%", 15.5],
                "Budget (YTD)": [44.0, 11.5, "40%", 16.0],
                "Variance": ["+2.7%", "+5.2%", "+2pp", "-3.1%"]
            }, use_container_width=True)
            
    with tab3:
        with st.container(border=True):
            st.subheader("Guardian Agent")
            st.success("✅ No critical compliance issues detected.")
            st.markdown("- **Board Meeting Minutes:** Filed (Oct 2025)")
            st.markdown("- **Audit:** Scheduled for Jan 2026")
            st.markdown("- **Insurance:** Active regarding D&O Policy")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application entry point."""
    render_top_navbar()
    
    if st.session_state.app_mode == "deal_flow":
        if st.session_state.selected_company is None:
            render_browse_view()
        elif st.session_state.selected_agent is not None:
            render_agent_deep_dive()
        else:
            render_detail_view()
            
    elif st.session_state.app_mode == "portfolio":
        if st.session_state.selected_company is None:
            render_portfolio_dashboard()
        else:
            render_portfolio_company_detail()


if __name__ == "__main__":
    main()
