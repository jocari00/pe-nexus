"""
IC Debate Page - Adversarial IC Agent
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from utils.formatters import format_currency, format_percentage

st.set_page_config(
    page_title="IC Debate | PE-Nexus",
    page_icon="scales",
    layout="wide",
)

# Header
st.title("Investment Committee Debate")
st.markdown("**Adversarial IC Agent**")

# Explanation box
st.info("""
**What this agent does:**

The Adversarial IC simulates an Investment Committee debate with two perspectives:
- **Bull Agent** - Builds the investment case, highlights strengths and value creation opportunities
- **Bear Agent** - Challenges the thesis, identifies risks and deal-killers
- **Synthesis** - Combines both views into a final recommendation

This process ensures rigorous analysis before investment decisions. The debate produces:
- Investment memorandum (bull case)
- Risk assessment and counter-arguments (bear case)
- Final recommendation with conditions
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
    | **AI Model** | **{llm_status['display_name']}** | Both Bull and Bear case generation |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | Multi-agent orchestration |
    | Pattern | Adversarial AI | Two agents with opposing objectives |
    | Backend | FastAPI + Python | Async API endpoints |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**

    *Bull Agent (Investment Advocate):*
    - Generates compelling investment thesis
    - Identifies value creation opportunities
    - Highlights competitive advantages
    - Projects optimistic but defensible returns

    *Bear Agent (Risk Challenger):*
    - Identifies potential deal-killers
    - Challenges assumptions in bull case
    - Highlights market and execution risks
    - Provides counter-arguments to investment thesis

    *Synthesis:*
    - Weighs bull and bear arguments
    - Determines final recommendation
    - Lists conditions for approval
    - Suggests additional due diligence items

    **Adversarial AI Pattern:**
    Using two AI agents with opposing objectives produces more balanced analysis than a single agent,
    similar to how real Investment Committees operate with devil's advocates.

    ---

    ### Works Without API Key?  PARTIALLY

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | Bull Case Structure | Template with deal data | AI-generated narrative |
    | Bear Case Structure | Template risk list | AI-generated counter-arguments |
    | Final Recommendation | Rule-based (IRR/MOIC thresholds) | AI-synthesized decision |
    | Conditions | Standard checklist | AI-customized conditions |

    *Basic structure works with templates, but the IC Debate is most valuable with AI generating
    realistic bull/bear arguments. This agent benefits most from having an API key.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# Deal Context Form
st.subheader("Deal Context")

st.markdown("Enter deal information for IC debate:")

col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input(
        "Company Name",
        value="CloudSync Technologies",
    )

    industry = st.selectbox(
        "Industry",
        options=["Technology", "Healthcare", "Financial Services", "Consumer", "Industrial"],
    )

    revenue = st.number_input(
        "Revenue ($M)",
        min_value=1.0,
        value=125.0,
        step=5.0,
    )

    ebitda = st.number_input(
        "EBITDA ($M)",
        min_value=1.0,
        value=25.0,
        step=1.0,
    )

with col2:
    entry_multiple = st.number_input(
        "Entry Multiple",
        min_value=4.0,
        max_value=15.0,
        value=8.0,
        step=0.5,
    )

    exit_multiple = st.number_input(
        "Exit Multiple",
        min_value=4.0,
        max_value=15.0,
        value=8.5,
        step=0.5,
    )

    irr = st.text_input(
        "Projected IRR",
        value="22%",
    )

    moic = st.text_input(
        "Projected MOIC",
        value="2.8x",
    )

growth_rate = st.text_input(
    "Revenue Growth Rate",
    value="15%",
)

strengths = st.text_area(
    "Key Strengths (one per line)",
    value="Market leader in cloud synchronization\nStrong recurring revenue base\nExperienced management team\nClear expansion opportunities",
    help="List the key strengths of this investment opportunity",
)

strengths_list = [s.strip() for s in strengths.split("\n") if s.strip()]

# Run Debate
st.markdown("---")

debate_col1, debate_col2, debate_col3 = st.columns(3)

with debate_col1:
    run_full = st.button("Run Full IC Debate", type="primary")

with debate_col2:
    run_bull = st.button("Generate Bull Case Only")

with debate_col3:
    run_bear = st.button("Generate Bear Case Only")

if run_full:
    with st.spinner("Running IC debate... This may take a moment."):
        result = api.ic_debate(
            company_name=company_name,
            industry=industry,
            revenue=revenue,
            ebitda=ebitda,
            entry_multiple=entry_multiple,
            exit_multiple=exit_multiple,
            irr=irr,
            moic=moic,
            strengths=strengths_list,
            growth_rate=growth_rate.replace("%", ""),
        )

    if result.get("success"):
        output = result.get("output", {})
        debate = output.get("debate_outcome", {})

        st.success(f"IC debate complete in {result.get('duration_seconds', 0):.2f}s")

        # Final Recommendation
        st.markdown("---")
        st.subheader("IC Recommendation")

        recommendation = debate.get("final_recommendation", "PENDING")
        confidence = debate.get("confidence_level", "MEDIUM")

        # Display recommendation with appropriate styling
        if "APPROVE" in recommendation.upper() and "CONDITION" not in recommendation.upper():
            st.success(f"**{recommendation}**")
        elif "CONDITION" in recommendation.upper() or "DD" in recommendation.upper():
            st.warning(f"**{recommendation}**")
        else:
            st.error(f"**{recommendation}**")

        st.caption(f"Confidence Level: {confidence}")

        # Key Conditions
        conditions = debate.get("key_conditions", [])
        if conditions:
            st.markdown("**Conditions for Approval:**")
            for condition in conditions:
                st.write(f"- {condition}")

        # Side-by-side Bull and Bear
        st.markdown("---")

        bull_col, bear_col = st.columns(2)

        with bull_col:
            st.markdown("### Bull Case")
            st.markdown("*Investment Thesis*")

            bull_memo = debate.get("bull_memo", {})

            # Investment thesis points
            thesis_points = bull_memo.get("investment_thesis", [])
            if thesis_points:
                for point in thesis_points:
                    st.markdown(f"+ {point}")

            # Value creation
            value_creation = bull_memo.get("value_creation_plan", [])
            if value_creation:
                st.markdown("**Value Creation Opportunities:**")
                for item in value_creation:
                    st.write(f"- {item}")

            # Target returns
            target = bull_memo.get("target_returns", {})
            if target:
                st.markdown("**Target Returns:**")
                st.write(f"IRR: {target.get('irr', 'N/A')}")
                st.write(f"MOIC: {target.get('moic', 'N/A')}")

        with bear_col:
            st.markdown("### Bear Case")
            st.markdown("*Risk Assessment*")

            bear_case = debate.get("bear_assessment", {})

            # Deal killers
            deal_killers = bear_case.get("deal_killers", [])
            if deal_killers:
                st.markdown("**Deal Killers:**")
                for dk in deal_killers:
                    if isinstance(dk, dict):
                        st.error(f"- {dk.get('issue', dk)}")
                    else:
                        st.error(f"- {dk}")

            # Major risks
            major_risks = bear_case.get("major_risks", [])
            if major_risks:
                st.markdown("**Major Risks:**")
                for risk in major_risks:
                    if isinstance(risk, dict):
                        st.warning(f"- {risk.get('risk', risk)}")
                    else:
                        st.warning(f"- {risk}")

            # Mitigating factors
            mitigating = bear_case.get("mitigating_factors", [])
            if mitigating:
                st.markdown("**Mitigating Factors:**")
                for factor in mitigating:
                    st.write(f"- {factor}")

        # Next Steps
        next_steps = debate.get("next_steps", [])
        if next_steps:
            st.markdown("---")
            st.subheader("Recommended Next Steps")
            for step in next_steps:
                st.write(f"- {step}")

    else:
        st.error(f"IC debate failed: {result.get('error', 'Unknown error')}")

if run_bull:
    with st.spinner("Generating bull case..."):
        result = api.ic_memo(
            company_name=company_name,
            industry=industry,
            revenue=revenue,
            ebitda=ebitda,
            entry_multiple=entry_multiple,
            exit_multiple=exit_multiple,
            irr=irr,
            moic=moic,
        )

    if result.get("success"):
        output = result.get("output", {})
        memo = output.get("memo", {})

        st.success("Bull case generated!")

        st.markdown("---")
        st.subheader("Investment Memorandum")

        # Executive Summary
        exec_summary = memo.get("executive_summary", "")
        if exec_summary:
            st.markdown("**Executive Summary:**")
            st.write(exec_summary)

        # Investment Thesis
        thesis = memo.get("investment_thesis", [])
        if thesis:
            st.markdown("**Investment Thesis:**")
            for point in thesis:
                st.markdown(f"+ {point}")

        # Value Creation
        value_creation = memo.get("value_creation_plan", [])
        if value_creation:
            st.markdown("**Value Creation Plan:**")
            for item in value_creation:
                st.write(f"- {item}")

        # Target Returns
        returns = memo.get("target_returns", {})
        if returns:
            st.markdown("**Target Returns:**")
            ret_col1, ret_col2 = st.columns(2)
            with ret_col1:
                st.metric("IRR", returns.get("irr", "N/A"))
            with ret_col2:
                st.metric("MOIC", returns.get("moic", "N/A"))
    else:
        st.error(f"Bull case failed: {result.get('error', 'Unknown error')}")

if run_bear:
    with st.spinner("Generating bear case..."):
        result = api.ic_bear(
            company_name=company_name,
            industry=industry,
            revenue=revenue,
            ebitda=ebitda,
            entry_multiple=entry_multiple,
            exit_multiple=exit_multiple,
            irr=irr,
            moic=moic,
        )

    if result.get("success"):
        output = result.get("output", {})
        bear = output.get("bear_case", {})

        st.success("Bear case generated!")

        st.markdown("---")
        st.subheader("Risk Assessment")

        # Overall Risk
        overall = bear.get("overall_risk_level", "MEDIUM")
        risk_colors = {"HIGH": "error", "MEDIUM": "warning", "LOW": "success"}

        if overall == "HIGH":
            st.error(f"**Overall Risk Level: {overall}**")
        elif overall == "MEDIUM":
            st.warning(f"**Overall Risk Level: {overall}**")
        else:
            st.success(f"**Overall Risk Level: {overall}**")

        # Deal Killers
        deal_killers = bear.get("deal_killers", [])
        if deal_killers:
            st.markdown("**Deal Killers:**")
            for dk in deal_killers:
                if isinstance(dk, dict):
                    st.error(f"- **{dk.get('issue', 'Unknown')}**: {dk.get('explanation', '')}")
                else:
                    st.error(f"- {dk}")
        else:
            st.success("No deal killers identified")

        # Major Risks
        major_risks = bear.get("major_risks", [])
        if major_risks:
            st.markdown("**Major Risks:**")
            for risk in major_risks:
                if isinstance(risk, dict):
                    st.warning(f"- **{risk.get('risk', 'Unknown')}**: {risk.get('impact', '')}")
                else:
                    st.warning(f"- {risk}")

        # Minor Concerns
        minor = bear.get("minor_concerns", [])
        if minor:
            st.markdown("**Minor Concerns:**")
            for concern in minor:
                st.write(f"- {concern}")

        # Mitigating Factors
        mitigating = bear.get("mitigating_factors", [])
        if mitigating:
            st.markdown("**Mitigating Factors:**")
            for factor in mitigating:
                st.info(f"+ {factor}")

        # Bear Recommendation
        rec = bear.get("recommendation", "")
        if rec:
            st.markdown("---")
            st.markdown(f"**Bear Recommendation:** {rec}")

    else:
        st.error(f"Bear case failed: {result.get('error', 'Unknown error')}")

# IC Process Guide
st.markdown("---")
st.subheader("IC Process Guide")

with st.expander("Understanding the IC Debate"):
    st.markdown("""
    **What is an Investment Committee (IC)?**

    The Investment Committee is a group of senior investment professionals who make
    final decisions on whether to proceed with an investment. The IC debate ensures
    rigorous analysis by presenting both positive and negative perspectives.

    **Bull Case (Investment Memo):**
    - Presents the investment thesis
    - Highlights market opportunity and competitive advantages
    - Outlines value creation plan
    - Projects target returns (IRR/MOIC)

    **Bear Case (Risk Assessment):**
    - Identifies potential deal killers
    - Highlights major risks and concerns
    - Questions assumptions in the bull case
    - Provides counter-arguments

    **Final Recommendation:**
    - APPROVE: Proceed with investment
    - APPROVE WITH CONDITIONS: Proceed if specific items are resolved
    - MORE DD REQUIRED: Need additional due diligence
    - PASS: Do not proceed with investment

    **Typical Thresholds:**
    - IRR > 20% for approval
    - MOIC > 2.5x for approval
    - No unmitigated deal killers
    """)
