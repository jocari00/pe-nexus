"""
Deal Sourcing Page - Intelligence Scout Agent
"""

import streamlit as st
import sys
from pathlib import Path

# Add frontend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from utils.formatters import format_score, format_percentage, truncate_text

st.set_page_config(
    page_title="Deal Sourcing | PE-Nexus",
    page_icon="mag",
    layout="wide",
)

# Header
st.title("Deal Sourcing")
st.markdown("**Intelligence Scout Agent**")

# Explanation box
st.info("""
**What this agent does:**

The Intelligence Scout scans market signals to identify potential acquisition targets. It analyzes:
- News articles and press releases for M&A signals
- Job posting patterns indicating growth or distress
- Macroeconomic indicators affecting the industry
- Company-specific financial signals

The agent produces a **Deal Score (0-10)** with a breakdown of factors and an **Investment Thesis**.
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
    | **AI Model** | **{llm_status['display_name']}** | Investment thesis generation, signal analysis |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | State machine-based agent orchestration |
    | Data Sources | Mock adapters (News, Jobs, Macro) | Market signal aggregation |
    | Scoring | Custom algorithm | 5-component weighted scoring |
    | Backend | FastAPI + Python | Async API endpoints |
    | Database | SQLite + SQLAlchemy | Deal storage and tracking |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**
    - Analyzes aggregated market signals to identify patterns
    - Generates natural language investment thesis
    - Provides reasoning for deal scoring adjustments
    - Identifies key risks and opportunities from unstructured data

    ---

    ### Works Without API Key?  YES

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | Deal Scoring | Rule-based algorithm | Same |
    | News/Job Signals | Mock data | Mock data (or real APIs) |
    | Investment Thesis | Generic template | AI-generated narrative |
    | Key Signals List | Extracted from data | AI-enhanced insights |

    *The scoring algorithm and mock data provide full functionality for demos.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server: `uvicorn src.main:app --reload`")
    st.stop()

# Analysis Form
st.subheader("Analyze a Company")

col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input(
        "Company Name",
        value="CloudSync Technologies",
        help="Enter the name of the company to analyze",
    )

with col2:
    industry = st.selectbox(
        "Industry",
        options=[
            "Technology",
            "Healthcare",
            "Financial Services",
            "Consumer",
            "Industrial",
            "Energy",
        ],
        index=0,
    )

sub_sector = st.text_input(
    "Sub-sector (optional)",
    value="Enterprise Software",
    help="Specific sub-sector within the industry",
)

# Run Analysis
if st.button("Analyze Company", type="primary"):
    with st.spinner(f"Analyzing {company_name}..."):
        result = api.scout_analyze(
            company_name=company_name,
            industry=industry,
            sub_sector=sub_sector,
        )

    if result.get("success"):
        output = result.get("output", {})
        scored_deal = output.get("scored_deal", {})

        st.success(f"Analysis complete in {result.get('duration_seconds', 0):.2f}s")

        # Deal Score Display
        st.markdown("---")
        st.subheader("Deal Score")

        score_col1, score_col2, score_col3 = st.columns(3)

        total_score = scored_deal.get("total_score", 0)
        score_tier = scored_deal.get("score_tier", "Unknown")

        with score_col1:
            # Score gauge using metric
            st.metric(
                label="Overall Score",
                value=f"{total_score:.1f}/10",
                delta=score_tier,
            )

        with score_col2:
            st.metric(
                label="Industry",
                value=scored_deal.get("industry", "Unknown"),
            )

        with score_col3:
            st.metric(
                label="Sub-sector",
                value=scored_deal.get("sub_sector", "N/A"),
            )

        # Score Breakdown
        st.markdown("---")
        st.subheader("Score Breakdown")

        # Get components from the API response
        components_list = scored_deal.get("components", [])

        breakdown_col1, breakdown_col2 = st.columns(2)

        with breakdown_col1:
            st.markdown("**Component Scores:**")

            if components_list:
                for comp in components_list:
                    name = comp.get("name", "Unknown")
                    raw_score = comp.get("raw_score", 0)
                    weight = comp.get("weight", 0)
                    rationale = comp.get("rationale", "")

                    # Display score with progress bar
                    st.write(f"{name}: **{raw_score:.1f}/10** (weight: {weight*100:.0f}%)")
                    st.progress(min(raw_score / 10, 1.0))
                    if rationale:
                        st.caption(f"_{rationale}_")
            else:
                st.write("No component breakdown available")

        with breakdown_col2:
            # Key Signals
            st.markdown("**Key Signals:**")
            signals = scored_deal.get("key_signals", [])
            if signals:
                for signal in signals[:5]:  # Limit to 5
                    st.success(f"+ {signal}")
            else:
                # Extract signals from components
                for comp in components_list:
                    signals_used = comp.get("signals_used", [])
                    for sig in signals_used[:2]:  # 2 per component
                        st.write(f"- {sig}")
                if not any(comp.get("signals_used") for comp in components_list):
                    st.write("No specific signals identified")

            # Risks/Concerns
            st.markdown("**Potential Risks:**")
            risks = scored_deal.get("risks", [])
            if risks:
                for risk in risks[:5]:  # Limit to 5
                    st.warning(f"- {risk}")
            else:
                st.write("No major risks identified")

        # Investment Thesis
        st.markdown("---")
        st.subheader("Investment Thesis")

        thesis = scored_deal.get("investment_thesis", "")
        if thesis:
            st.write(thesis)
        else:
            st.info("Investment thesis will be generated with an LLM API key configured.")

        # Recommended Next Steps
        st.markdown("---")
        st.subheader("Recommended Next Steps")

        if total_score >= 7:
            st.success("Strong candidate - proceed to detailed analysis")
            st.markdown("""
            1. Run **Financial Triage** to extract detailed financials
            2. Use **Relationship Navigator** to find warm introduction paths
            3. Prepare materials for **IC Review**
            """)
        elif total_score >= 5:
            st.warning("Moderate potential - gather more information")
            st.markdown("""
            1. Conduct additional research on specific concerns
            2. Monitor for improving signals
            3. Consider adding to watchlist
            """)
        else:
            st.error("Below threshold - pass or monitor")
            st.markdown("""
            1. Document reasons for passing
            2. Add to monitoring list if sector is strategic
            3. Consider re-evaluating if conditions change
            """)

    else:
        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

# Industry Scan Section
st.markdown("---")
st.subheader("Industry Scan")

st.markdown("Scan an entire industry for opportunities:")

scan_col1, scan_col2 = st.columns(2)

with scan_col1:
    scan_industry = st.selectbox(
        "Scan Industry",
        options=[
            "All Industries",
            "Technology",
            "Healthcare",
            "Financial Services",
            "Consumer",
            "Industrial",
        ],
        key="scan_industry",
    )

with scan_col2:
    min_score = st.slider(
        "Minimum Score",
        min_value=1.0,
        max_value=9.0,
        value=5.0,
        step=0.5,
    )

if st.button("Scan Industry"):
    industry_to_scan = None if scan_industry == "All Industries" else scan_industry

    with st.spinner(f"Scanning {scan_industry}..."):
        result = api.scout_scan(
            industry=industry_to_scan,
            limit=10,
            min_score=min_score,
        )

    if result.get("success"):
        output = result.get("output", {})
        # API returns "scored_deals" not "opportunities"
        opportunities = output.get("scored_deals", [])

        st.success(f"Found {len(opportunities)} opportunities above {min_score} score")

        if opportunities:
            # Display as a table
            import pandas as pd

            df_data = []
            for opp in opportunities:
                df_data.append({
                    "Company": opp.get("company_name", "Unknown"),
                    "Industry": opp.get("industry", ""),
                    "Sub-sector": opp.get("sub_sector", ""),
                    "Score": f"{opp.get('total_score', 0):.1f}",
                    "Tier": opp.get("score_tier", ""),
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Scan failed: {result.get('error', 'Unknown error')}")

# Market Signals
st.markdown("---")
st.subheader("Recent Market Signals")

if st.button("Fetch Market Signals"):
    with st.spinner("Fetching signals..."):
        result = api.scout_signals()

    if result.get("success"):
        signals = result.get("signals", {})

        signal_col1, signal_col2, signal_col3 = st.columns(3)

        with signal_col1:
            st.markdown("**News Signals**")
            news = signals.get("news", [])
            if news:
                for item in news[:5]:
                    headline = item.get("headline", item) if isinstance(item, dict) else item
                    st.write(f"- {truncate_text(str(headline), 60)}")
            else:
                st.write("No recent news signals")

        with signal_col2:
            st.markdown("**Job Signals**")
            jobs = signals.get("jobs", [])
            if jobs:
                for item in jobs[:5]:
                    title = item.get("title", item) if isinstance(item, dict) else item
                    st.write(f"- {truncate_text(str(title), 60)}")
            else:
                st.write("No recent job signals")

        with signal_col3:
            st.markdown("**Macro Signals**")
            macro = signals.get("macro", {})
            if macro:
                for key, value in list(macro.items())[:5]:
                    st.write(f"- {key}: {value}")
            else:
                st.write("No macro signals available")
    else:
        st.error(f"Failed to fetch signals: {result.get('error', 'Unknown error')}")
