"""
Financial Model Page - Quant Strategist Agent
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from utils.formatters import format_currency, format_percentage, format_multiple

st.set_page_config(
    page_title="Financial Model | PE-Nexus",
    page_icon="chart",
    layout="wide",
)

# Header
st.title("Financial Modeling")
st.markdown("**Quant Strategist Agent**")

# Explanation box
st.info("""
**What this agent does:**

The Quant Strategist builds LBO (Leveraged Buyout) models to analyze investment returns:
- **Sources & Uses** - How the deal is financed (debt vs equity)
- **5-Year Projections** - Revenue, EBITDA, debt paydown
- **Returns Analysis** - IRR (Internal Rate of Return) and MOIC (Multiple on Invested Capital)
- **Sensitivity Tables** - How returns change with different assumptions
- **Investment Recommendation** - Based on return thresholds

Typical PE targets: **>20% IRR** and **>2.5x MOIC** over a 5-year hold.
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
    | **AI Model** | **{llm_status['display_name']}** | Investment commentary, thesis generation |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | State machine-based agent orchestration |
    | Financial Calculations | Python (Decimal) | Precise IRR/MOIC calculations |
    | Data Type | Decimal (not float) | Financial precision requirement |
    | Backend | FastAPI + Python | Async API endpoints |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**
    - Generates investment thesis based on model outputs
    - Provides qualitative assessment of returns (Attractive/Marginal/Unattractive)
    - Identifies key risks based on sensitivity analysis
    - Creates narrative explanations of value creation drivers
    - Recommends deal structure optimizations

    ---

    ### Works Without API Key?  YES

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | LBO Model | Full calculations | Same |
    | IRR/MOIC | Newton-Raphson method | Same |
    | Sensitivity Tables | Matrix generation | Same |
    | Sources & Uses | Calculated | Same |
    | Investment Thesis | Rule-based verdict | AI-generated narrative |
    | Risk Commentary | Template | AI-enhanced insights |

    *All financial calculations are pure Python - no AI needed. LLM only adds narrative commentary.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# LBO Model Builder
st.subheader("Build LBO Model")

# Input form
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Company Financials**")

    company_name = st.text_input(
        "Company Name",
        value="CloudSync Technologies",
    )

    ltm_revenue = st.number_input(
        "LTM Revenue ($M)",
        min_value=1.0,
        value=125.0,
        step=5.0,
        help="Last Twelve Months revenue in millions",
    )

    ltm_ebitda = st.number_input(
        "LTM EBITDA ($M)",
        min_value=1.0,
        value=25.0,
        step=1.0,
        help="Last Twelve Months EBITDA in millions",
    )

    ebitda_margin = ltm_ebitda / ltm_revenue * 100 if ltm_revenue > 0 else 0
    st.caption(f"EBITDA Margin: {ebitda_margin:.1f}%")

with col2:
    st.markdown("**Deal Assumptions**")

    entry_multiple = st.number_input(
        "Entry EV/EBITDA Multiple",
        min_value=4.0,
        max_value=15.0,
        value=8.0,
        step=0.5,
        help="Purchase price as multiple of EBITDA",
    )

    exit_multiple = st.number_input(
        "Exit EV/EBITDA Multiple",
        min_value=4.0,
        max_value=15.0,
        value=8.5,
        step=0.5,
        help="Exit price as multiple of projected EBITDA",
    )

    holding_period = st.slider(
        "Holding Period (Years)",
        min_value=3,
        max_value=7,
        value=5,
    )

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Financing Assumptions**")

    leverage = st.number_input(
        "Leverage (Debt/EBITDA)",
        min_value=2.0,
        max_value=7.0,
        value=4.5,
        step=0.5,
        help="Total debt as multiple of EBITDA",
    )

    interest_rate = st.slider(
        "Interest Rate (%)",
        min_value=4.0,
        max_value=12.0,
        value=8.0,
        step=0.5,
    ) / 100

with col4:
    st.markdown("**Growth Assumptions**")

    revenue_growth = st.slider(
        "Annual Revenue Growth (%)",
        min_value=0.0,
        max_value=30.0,
        value=10.0,
        step=1.0,
    ) / 100

    tax_rate = st.slider(
        "Tax Rate (%)",
        min_value=15.0,
        max_value=35.0,
        value=25.0,
        step=1.0,
    ) / 100

# Calculate button
if st.button("Build LBO Model", type="primary"):
    with st.spinner("Building model..."):
        result = api.strategist_analyze(
            company_name=company_name,
            ltm_revenue=ltm_revenue,
            ltm_ebitda=ltm_ebitda,
            entry_multiple=entry_multiple,
            exit_multiple=exit_multiple,
            holding_period=holding_period,
            leverage=leverage,
            revenue_growth=revenue_growth,
        )

    if result.get("success"):
        output = result.get("output", {})
        model = output.get("model", {})
        commentary = output.get("commentary", {})

        st.success(f"Model complete in {result.get('duration_seconds', 0):.2f}s")

        # Sources & Uses
        st.markdown("---")
        st.subheader("Sources & Uses")

        sources_uses = model.get("sources_and_uses", {})
        # API returns nested structure: {"sources": {...}, "uses": {...}}
        sources = sources_uses.get("sources", {})
        uses = sources_uses.get("uses", {})

        su_col1, su_col2 = st.columns(2)

        with su_col1:
            st.markdown("**Sources**")
            st.write(f"Senior Debt: {format_currency(sources.get('senior_debt', 0))}")
            st.write(f"Equity: {format_currency(sources.get('equity', 0))}")
            st.write(f"**Total: {format_currency(sources.get('total', 0))}**")

        with su_col2:
            st.markdown("**Uses**")
            st.write(f"Purchase Price: {format_currency(uses.get('purchase_price', 0))}")
            st.write(f"Transaction Fees: {format_currency(uses.get('transaction_fees', 0))}")
            st.write(f"**Total: {format_currency(uses.get('total', 0))}**")

        # Returns
        st.markdown("---")
        st.subheader("Investment Returns")

        returns = model.get("returns", {})

        ret_col1, ret_col2, ret_col3, ret_col4 = st.columns(4)

        # API returns irr as decimal (e.g., 0.20 for 20%), convert to percentage
        irr = returns.get("irr", 0) * 100
        moic = returns.get("moic", 0)
        entry_equity = returns.get("entry_equity", 0)
        exit_equity = returns.get("exit_equity", 0)

        with ret_col1:
            # Color based on IRR threshold
            irr_color = "normal" if irr >= 20 else "inverse"
            st.metric(
                label="IRR",
                value=f"{irr:.1f}%",
                delta="Meets target" if irr >= 20 else "Below target",
                delta_color=irr_color,
            )

        with ret_col2:
            moic_color = "normal" if moic >= 2.5 else "inverse"
            st.metric(
                label="MOIC",
                value=f"{moic:.2f}x",
                delta="Meets target" if moic >= 2.5 else "Below target",
                delta_color=moic_color,
            )

        with ret_col3:
            st.metric(
                label="Entry Equity",
                value=format_currency(entry_equity),
            )

        with ret_col4:
            st.metric(
                label="Exit Equity",
                value=format_currency(exit_equity),
            )

        # Value Creation Bridge - API returns in returns.value_creation
        value_creation = returns.get("value_creation", {})
        if value_creation:
            st.markdown("---")
            st.subheader("Value Creation Bridge")

            vc_col1, vc_col2, vc_col3 = st.columns(3)

            with vc_col1:
                st.metric(
                    label="EBITDA Growth",
                    value=format_currency(value_creation.get("ebitda_growth", 0)),
                )
            with vc_col2:
                st.metric(
                    label="Multiple Expansion",
                    value=format_currency(value_creation.get("multiple_expansion", 0)),
                )
            with vc_col3:
                st.metric(
                    label="Deleveraging",
                    value=format_currency(value_creation.get("deleveraging", 0)),
                )

        # Investment Verdict
        st.markdown("---")
        st.subheader("Investment Recommendation")

        verdict = commentary.get("verdict", "UNKNOWN")
        thesis = commentary.get("investment_thesis", "")
        risks = commentary.get("key_risks", [])

        if verdict == "ATTRACTIVE":
            st.success(f"**Verdict: {verdict}**")
        elif verdict == "MARGINAL":
            st.warning(f"**Verdict: {verdict}**")
        else:
            st.error(f"**Verdict: {verdict}**")

        if thesis:
            st.markdown(f"**Investment Thesis:** {thesis}")

        if risks:
            st.markdown("**Key Risks:**")
            for risk in risks:
                st.write(f"- {risk}")

        # Sensitivity Tables
        sensitivity = output.get("sensitivity", {})
        if sensitivity:
            st.markdown("---")
            st.subheader("Sensitivity Analysis")

            sens_tables = sensitivity.get("tables", {})

            entry_exit_table = sens_tables.get("entry_exit_irr", {})
            if entry_exit_table:
                st.markdown("**IRR Sensitivity to Entry/Exit Multiples**")

                import pandas as pd

                # Build the sensitivity table
                rows = entry_exit_table.get("rows", [])
                cols = entry_exit_table.get("columns", [])
                data = entry_exit_table.get("data", [])

                if rows and cols and data:
                    df = pd.DataFrame(data, index=rows, columns=cols)
                    # Format as percentages
                    df = df.applymap(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x)
                    st.dataframe(df, use_container_width=True)

    else:
        st.error(f"Model failed: {result.get('error', 'Unknown error')}")

# Quick Returns Calculator
st.markdown("---")
st.subheader("Quick Returns Calculator")

st.markdown("Simple IRR/MOIC calculation from entry and exit values:")

quick_col1, quick_col2, quick_col3 = st.columns(3)

with quick_col1:
    quick_entry = st.number_input(
        "Entry Equity ($M)",
        min_value=1.0,
        value=50.0,
        step=5.0,
        key="quick_entry",
    )

with quick_col2:
    quick_exit = st.number_input(
        "Exit Equity ($M)",
        min_value=1.0,
        value=125.0,
        step=5.0,
        key="quick_exit",
    )

with quick_col3:
    quick_years = st.number_input(
        "Holding Period (Years)",
        min_value=1,
        max_value=10,
        value=5,
        key="quick_years",
    )

if st.button("Calculate Returns"):
    # Local calculation (no API needed)
    moic = quick_exit / quick_entry
    irr = (moic ** (1 / quick_years) - 1) * 100

    quick_res_col1, quick_res_col2 = st.columns(2)

    with quick_res_col1:
        st.metric(
            label="IRR",
            value=f"{irr:.1f}%",
            delta="Meets target" if irr >= 20 else "Below target",
            delta_color="normal" if irr >= 20 else "inverse",
        )

    with quick_res_col2:
        st.metric(
            label="MOIC",
            value=f"{moic:.2f}x",
            delta="Meets target" if moic >= 2.5 else "Below target",
            delta_color="normal" if moic >= 2.5 else "inverse",
        )

# Standalone Sensitivity Analysis
st.markdown("---")
st.subheader("Sensitivity Table Generator")

sens_col1, sens_col2 = st.columns(2)

with sens_col1:
    sens_revenue = st.number_input(
        "Base Revenue ($M)",
        min_value=1.0,
        value=100.0,
        key="sens_revenue",
    )
    sens_ebitda = st.number_input(
        "Base EBITDA ($M)",
        min_value=1.0,
        value=20.0,
        key="sens_ebitda",
    )

with sens_col2:
    sens_type = st.selectbox(
        "Sensitivity Type",
        options=["entry_exit", "growth_leverage", "all"],
        format_func=lambda x: {
            "entry_exit": "Entry vs Exit Multiple",
            "growth_leverage": "Growth vs Leverage",
            "all": "All Tables",
        }.get(x, x),
    )
    sens_metric = st.selectbox(
        "Metric",
        options=["irr", "moic"],
        format_func=lambda x: x.upper(),
    )

if st.button("Generate Sensitivity Tables"):
    with st.spinner("Generating..."):
        result = api.strategist_sensitivity(
            ltm_revenue=sens_revenue,
            ltm_ebitda=sens_ebitda,
            sensitivity_type=sens_type,
            metric=sens_metric,
        )

    if result.get("success"):
        output = result.get("output", {})
        tables = output.get("tables", {})

        st.success("Sensitivity tables generated!")

        import pandas as pd

        for table_name, table_data in tables.items():
            st.markdown(f"**{table_name.replace('_', ' ').title()}**")

            rows = table_data.get("rows", [])
            cols = table_data.get("columns", [])
            data = table_data.get("data", [])

            if rows and cols and data:
                df = pd.DataFrame(data, index=rows, columns=cols)
                if sens_metric == "irr":
                    df = df.applymap(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x)
                else:
                    df = df.applymap(lambda x: f"{x:.2f}x" if isinstance(x, (int, float)) else x)
                st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Generation failed: {result.get('error', 'Unknown error')}")
