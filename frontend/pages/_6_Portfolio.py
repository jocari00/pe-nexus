"""
Portfolio Monitoring Page - Value Creation Monitor Agent
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from utils.formatters import (
    format_currency,
    format_percentage,
    get_status_color,
    get_status_emoji,
)

st.set_page_config(
    page_title="Portfolio | PE-Nexus",
    page_icon="briefcase",
    layout="wide",
)

# Header
st.title("Portfolio Monitoring")
st.markdown("**Value Creation Monitor Agent**")

# Explanation box
st.info("""
**What this agent does:**

The Value Creation Monitor tracks portfolio company performance and generates LP reports:
- **KPI Dashboard** - Real-time performance metrics across portfolio
- **Variance Analysis** - Actual vs budget comparison
- **Alert System** - Proactive notifications for issues (Critical/High/Medium/Low)
- **Trend Detection** - Revenue, margin, and cash flow trends
- **LP Reporting** - Quarterly narrative reports for limited partners

Status indicators: ON_TRACK (green), WATCH (yellow), AT_RISK (red), OUTPERFORMING (blue)
""")

# Get API client early for LLM status
api = get_api_client()
llm_status = api.get_llm_status()

# Tech Stack - show current LLM
with st.expander("Tech Stack & AI Model"):
    st.markdown(f"""
    ### Technology Used

    | Component | Technology | Purpose |
    |-----------|------------|---------|
    | **AI Model** | **{llm_status['display_name']}** | Narrative generation, trend analysis |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | State machine-based agent orchestration |
    | KPI Calculations | Python + Pandas | Variance analysis, trend detection |
    | Alert System | Rule-based + AI | Threshold monitoring with AI insights |
    | Backend | FastAPI + Python | Async API endpoints |
    | Database | SQLite/PostgreSQL | Portfolio data storage |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**
    - Generates LP report executive summaries and narratives
    - Provides qualitative analysis of KPI trends
    - Interprets variance data and explains implications
    - Creates personalized company performance summaries
    - Identifies potential issues before they become critical
    - Suggests value creation initiatives based on performance data

    ---

    ### Works Without API Key?  YES

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | Portfolio Dashboard | Full metrics | Same |
    | KPI Calculations | Pandas variance analysis | Same |
    | Alert Generation | Rule-based thresholds | Same |
    | Trend Detection | Statistical analysis | Same |
    | Company Data | 5 mock portfolio companies | Same |
    | LP Report Metrics | Calculated | Same |
    | LP Report Narrative | Template-based | AI-generated prose |
    | Commentary | Structured bullets | Natural language insights |

    *All dashboard and KPI features work without AI. LP report narratives are enhanced with LLM.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Company Detail", "Alerts", "LP Report"])

# =============================================================================
# Tab 1: Portfolio Dashboard
# =============================================================================
with tab1:
    st.subheader("Portfolio Dashboard")

    if st.button("Refresh Dashboard", key="refresh_dashboard"):
        st.cache_data.clear()

    # Get dashboard data
    dashboard_result = api.monitor_dashboard()

    if dashboard_result.get("success"):
        output = dashboard_result.get("output", {})
        summary = output.get("summary", {})
        companies = output.get("companies", [])

        # Summary metrics
        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

        with metric_col1:
            st.metric(
                label="Portfolio Companies",
                value=summary.get("total_companies", 0),
            )

        with metric_col2:
            st.metric(
                label="Total NAV",
                value=format_currency(summary.get("total_nav", 0)),
            )

        with metric_col3:
            st.metric(
                label="Avg Revenue Growth",
                value=format_percentage(summary.get("weighted_revenue_growth", 0)),
            )

        with metric_col4:
            total_alerts = output.get("total_alerts", 0)
            st.metric(
                label="Active Alerts",
                value=total_alerts,
                delta="Attention needed" if total_alerts > 0 else None,
                delta_color="inverse" if total_alerts > 0 else "normal",
            )

        with metric_col5:
            critical = output.get("critical_alerts", 0)
            st.metric(
                label="Critical Alerts",
                value=critical,
                delta="Immediate action" if critical > 0 else None,
                delta_color="inverse" if critical > 0 else "normal",
            )

        # Status Distribution
        st.markdown("---")
        st.subheader("Portfolio Status")

        # Count by status
        status_counts = {}
        for company in companies:
            status = company.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        status_col1, status_col2, status_col3, status_col4 = st.columns(4)

        with status_col1:
            on_track = status_counts.get("on_track", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #28A74520; border-radius: 10px;">
                <h2 style="color: #28A745; margin: 0;">{on_track}</h2>
                <p style="margin: 0;">On Track</p>
            </div>
            """, unsafe_allow_html=True)

        with status_col2:
            outperforming = status_counts.get("outperforming", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #17A2B820; border-radius: 10px;">
                <h2 style="color: #17A2B8; margin: 0;">{outperforming}</h2>
                <p style="margin: 0;">Outperforming</p>
            </div>
            """, unsafe_allow_html=True)

        with status_col3:
            watch = status_counts.get("watch", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #FFC10720; border-radius: 10px;">
                <h2 style="color: #FFC107; margin: 0;">{watch}</h2>
                <p style="margin: 0;">Watch</p>
            </div>
            """, unsafe_allow_html=True)

        with status_col4:
            at_risk = status_counts.get("at_risk", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #DC354520; border-radius: 10px;">
                <h2 style="color: #DC3545; margin: 0;">{at_risk}</h2>
                <p style="margin: 0;">At Risk</p>
            </div>
            """, unsafe_allow_html=True)

        # Company Cards
        st.markdown("---")
        st.subheader("Portfolio Companies")

        for company in companies:
            status = company.get("status", "unknown")
            color = get_status_color(status)
            emoji = get_status_emoji(status)

            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background-color: #f8f9fa; border-radius: 0 8px 8px 0;">
                    <strong style="font-size: 1.1rem;">{company.get('name', 'Unknown')}</strong>
                    <span style="color: {color}; margin-left: 10px;">[{status.upper().replace('_', ' ')}]</span>
                    <br>
                    <small>{company.get('industry', '')} | Entry: {company.get('entry_year', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)

                comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)

                with comp_col1:
                    st.caption("YTD Revenue vs Plan")
                    variance = company.get("ytd_revenue_variance", "N/A")
                    st.write(variance)

                with comp_col2:
                    st.caption("EBITDA Margin")
                    margin = company.get("ebitda_margin", "N/A")
                    st.write(margin)

                with comp_col3:
                    st.caption("Entry Value")
                    entry = company.get("entry_ev", 0)
                    st.write(format_currency(entry))

                with comp_col4:
                    st.caption("Alerts")
                    alerts = company.get("alert_count", 0)
                    if alerts > 0:
                        st.warning(f"{alerts} active")
                    else:
                        st.success("None")

    else:
        st.error(f"Failed to load dashboard: {dashboard_result.get('error', 'Unknown error')}")

# =============================================================================
# Tab 2: Company Detail
# =============================================================================
with tab2:
    st.subheader("Company Analysis")

    # Get list of companies
    companies_result = api.monitor_companies()
    companies_list = companies_result.get("companies", [])

    if companies_list:
        company_options = {c.get("name", f"Company {i}"): c.get("id") for i, c in enumerate(companies_list)}

        selected_company_name = st.selectbox(
            "Select Company",
            options=list(company_options.keys()),
        )

        if selected_company_name:
            company_id = company_options[selected_company_name]

            period = st.radio(
                "Analysis Period",
                options=["quarterly", "annual", "ytd"],
                horizontal=True,
                format_func=lambda x: x.upper() if x == "ytd" else x.title(),
            )

            if st.button("Analyze Company", type="primary"):
                with st.spinner(f"Analyzing {selected_company_name}..."):
                    result = api.monitor_analyze(
                        company_id=company_id,
                        period=period,
                    )

                if result.get("success"):
                    output = result.get("output", {})
                    analysis = output.get("analysis", {})
                    company_info = analysis.get("company", {})

                    st.success("Analysis complete!")

                    # Company header
                    st.markdown("---")
                    status = company_info.get("status", "unknown")
                    color = get_status_color(status)

                    st.markdown(f"""
                    <h3>{company_info.get('name', selected_company_name)}
                    <span style="color: {color};">({status.upper().replace('_', ' ')})</span></h3>
                    """, unsafe_allow_html=True)

                    # Financial KPIs
                    st.subheader("Financial Performance")

                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

                    financial_kpis = analysis.get("financial_kpis", {})

                    with kpi_col1:
                        rev_var = financial_kpis.get("revenue_variance_pct", 0)
                        st.metric(
                            label="Revenue vs Plan",
                            value=f"{rev_var:+.1f}%",
                            delta="On track" if rev_var >= 0 else "Below plan",
                            delta_color="normal" if rev_var >= 0 else "inverse",
                        )

                    with kpi_col2:
                        ebitda_var = financial_kpis.get("ebitda_variance_pct", 0)
                        st.metric(
                            label="EBITDA vs Plan",
                            value=f"{ebitda_var:+.1f}%",
                            delta="On track" if ebitda_var >= 0 else "Below plan",
                            delta_color="normal" if ebitda_var >= 0 else "inverse",
                        )

                    with kpi_col3:
                        margin = financial_kpis.get("current_ebitda_margin", 0)
                        st.metric(
                            label="EBITDA Margin",
                            value=f"{margin:.1f}%",
                        )

                    with kpi_col4:
                        cash = financial_kpis.get("cash_balance", 0)
                        st.metric(
                            label="Cash Balance",
                            value=format_currency(cash),
                        )

                    # Operational KPIs
                    operational_kpis = analysis.get("operational_kpis", {})
                    if operational_kpis:
                        st.subheader("Operational KPIs")

                        op_col1, op_col2, op_col3 = st.columns(3)

                        with op_col1:
                            for key, value in list(operational_kpis.items())[:3]:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                        with op_col2:
                            for key, value in list(operational_kpis.items())[3:6]:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                        with op_col3:
                            for key, value in list(operational_kpis.items())[6:]:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                    # Trends
                    trends = analysis.get("trends", {})
                    if trends:
                        st.subheader("Trends")

                        for trend_name, trend_data in trends.items():
                            direction = trend_data.get("direction", "flat")
                            if direction == "improving":
                                st.success(f"**{trend_name.replace('_', ' ').title()}**: Improving")
                            elif direction == "declining":
                                st.warning(f"**{trend_name.replace('_', ' ').title()}**: Declining")
                            else:
                                st.info(f"**{trend_name.replace('_', ' ').title()}**: Stable")

                    # Alerts for this company
                    company_alerts = analysis.get("alerts", [])
                    if company_alerts:
                        st.subheader("Active Alerts")
                        for alert in company_alerts:
                            severity = alert.get("severity", "low")
                            if severity == "critical":
                                st.error(f"**{alert.get('title', 'Alert')}**: {alert.get('message', '')}")
                            elif severity == "high":
                                st.warning(f"**{alert.get('title', 'Alert')}**: {alert.get('message', '')}")
                            else:
                                st.info(f"**{alert.get('title', 'Alert')}**: {alert.get('message', '')}")

                    # Commentary
                    commentary = analysis.get("commentary", "")
                    if commentary:
                        st.subheader("AI Commentary")
                        st.write(commentary)

                else:
                    st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
    else:
        st.warning("No portfolio companies available.")

# =============================================================================
# Tab 3: Alerts
# =============================================================================
with tab3:
    st.subheader("Portfolio Alerts")

    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        severity_filter = st.selectbox(
            "Filter by Severity",
            options=["All", "critical", "high", "medium", "low"],
            format_func=lambda x: x.title() if x != "All" else x,
        )

    with alert_col2:
        company_filter = st.selectbox(
            "Filter by Company",
            options=["All Companies"] + [c.get("name", "") for c in companies_list],
        )

    # Get alerts
    severity = None if severity_filter == "All" else severity_filter
    company_id = None
    if company_filter != "All Companies":
        company_id = next(
            (c.get("id") for c in companies_list if c.get("name") == company_filter),
            None
        )

    alerts_result = api.monitor_alerts(severity=severity, company_id=company_id)

    if alerts_result.get("success"):
        alerts = alerts_result.get("alerts", [])
        total = alerts_result.get("total_count", 0)
        critical_count = alerts_result.get("critical_count", 0)

        st.write(f"**Total Alerts:** {total} | **Critical:** {critical_count}")

        if alerts:
            for alert in alerts:
                severity = alert.get("severity", "low")
                color = get_status_color(severity)

                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background-color: {color}10;">
                    <strong>{alert.get('title', 'Alert')}</strong>
                    <span style="color: {color};">({severity.upper()})</span><br>
                    <small>Company: {alert.get('company', 'Unknown')}</small><br>
                    {alert.get('message', '')}
                </div>
                """, unsafe_allow_html=True)

                action = alert.get("recommended_action", "")
                if action:
                    st.info(f"**Recommended Action:** {action}")
        else:
            st.success("No alerts matching the filter criteria.")
    else:
        st.error(f"Failed to load alerts: {alerts_result.get('error', 'Unknown error')}")

# =============================================================================
# Tab 4: LP Report
# =============================================================================
with tab4:
    st.subheader("LP Report Generator")

    st.markdown("""
    Generate quarterly LP (Limited Partner) reports with portfolio performance summaries,
    individual company updates, and value creation narratives.
    """)

    report_col1, report_col2, report_col3 = st.columns(3)

    with report_col1:
        quarter = st.selectbox(
            "Quarter",
            options=[1, 2, 3, 4],
            index=3,
        )

    with report_col2:
        year = st.number_input(
            "Year",
            min_value=2020,
            max_value=2030,
            value=2025,
        )

    with report_col3:
        fund_name = st.text_input(
            "Fund Name",
            value="PE-Nexus Fund I",
        )

    if st.button("Generate LP Report", type="primary"):
        with st.spinner("Generating LP report... This may take a moment."):
            result = api.monitor_report(
                quarter=quarter,
                year=year,
                fund_name=fund_name,
            )

        if result.get("success"):
            output = result.get("output", {})
            report = output.get("report", {})

            st.success(f"Report generated in {result.get('duration_seconds', 0):.2f}s")

            if result.get("requires_review"):
                st.warning("This report requires human review before distribution to LPs.")

            st.markdown("---")
            st.markdown(f"## {fund_name} - Q{quarter} {year} Report")

            # Executive Summary
            exec_summary = report.get("executive_summary", "")
            if exec_summary:
                st.subheader("Executive Summary")
                st.write(exec_summary)

            # Portfolio Metrics
            metrics = report.get("portfolio_metrics", {})
            if metrics:
                st.subheader("Portfolio Metrics")

                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric(
                        label="Total NAV",
                        value=format_currency(metrics.get("total_nav", 0)),
                    )

                with metric_col2:
                    st.metric(
                        label="Gross IRR",
                        value=format_percentage(metrics.get("gross_irr", 0)),
                    )

                with metric_col3:
                    st.metric(
                        label="Gross MOIC",
                        value=f"{metrics.get('gross_moic', 0):.2f}x",
                    )

                with metric_col4:
                    st.metric(
                        label="DPI",
                        value=f"{metrics.get('dpi', 0):.2f}x",
                    )

            # Company Updates
            company_updates = report.get("company_updates", [])
            if company_updates:
                st.subheader("Company Updates")

                for update in company_updates:
                    with st.expander(f"{update.get('company_name', 'Unknown')} - {update.get('status', 'N/A').upper()}"):
                        st.write(f"**Performance:** {update.get('performance_summary', 'N/A')}")
                        st.write(f"**Key Developments:** {update.get('key_developments', 'N/A')}")
                        st.write(f"**Outlook:** {update.get('outlook', 'N/A')}")

            # Value Creation Narrative
            narrative = report.get("value_creation_narrative", "")
            if narrative:
                st.subheader("Value Creation")
                st.write(narrative)

            # Outlook
            outlook = report.get("outlook", "")
            if outlook:
                st.subheader("Outlook")
                st.write(outlook)

            # Download option
            st.markdown("---")

            # Create downloadable text version
            report_text = f"""
{fund_name} - Q{quarter} {year} Report
{'=' * 50}

EXECUTIVE SUMMARY
{exec_summary}

PORTFOLIO METRICS
- Total NAV: {format_currency(metrics.get('total_nav', 0))}
- Gross IRR: {format_percentage(metrics.get('gross_irr', 0))}
- Gross MOIC: {metrics.get('gross_moic', 0):.2f}x

VALUE CREATION
{narrative}

OUTLOOK
{outlook}
"""

            st.download_button(
                label="Download Report (TXT)",
                data=report_text,
                file_name=f"LP_Report_Q{quarter}_{year}.txt",
                mime="text/plain",
            )

        else:
            st.error(f"Report generation failed: {result.get('error', 'Unknown error')}")
