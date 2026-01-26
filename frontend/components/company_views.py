
import streamlit as st
from components.theme import get_score_color, get_score_tier
from components.cards import render_metric_card
from utils.mock_data import get_mock_companies, get_mock_company_detail, get_mock_portfolio
from components.agent_views import (
    render_scout_section, render_navigator_section, render_financial_section,
    render_risk_section, render_verdict_section, render_news_section, render_agent_deep_dive
)

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
                {st.session_state.get('app_mode', 'Deal Flow').replace('_', ' ').title()}
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
    # PAIR: Explicit Disclaimer
    st.markdown("""
    <div style="background-color: #FFF7ED; border: 1px solid #FFEDD5; color: #9A3412; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
        <span>🤖</span>
        <span><strong>AI System:</strong> Company scores and tags are generated by AI agents. Verify independent data sources.</span>
    </div>
    """, unsafe_allow_html=True)
    
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


def render_detail_view():
    """Render the company detail view."""
    company_id = st.session_state.selected_company
    
    # Back button
    if st.button("← Back to Companies"):
        st.session_state.selected_company = None
        st.rerun()

    # PAIR: Explicit Disclaimer
    st.markdown("""
    <div style="background-color: #FFF7ED; border: 1px solid #FFEDD5; color: #9A3412; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
        <span>🤖</span>
        <span><strong>AI Analysis:</strong> Detailed reports are synthesized from multiple AI agents. Human review required for critical decisions.</span>
    </div>
    """, unsafe_allow_html=True)
    
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
        
        # Agent sections (Managed in agent_views, called here)
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


def render_portfolio_dashboard():
    """Render the Portfolio Management Dashboard."""
    
    # PAIR: Explicit Disclaimer
    st.markdown("""
    <div style="background-color: #EFFAFF; border: 1px solid #D1E9FF; color: #155CA2; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
        <span>📊</span>
        <span><strong>Automated Metrics:</strong> Portfolio Logic uses automated data ingestion. Confirm bank balances manually.</span>
    </div>
    """, unsafe_allow_html=True)

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
