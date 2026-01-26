"""
Legal Review Page - Legal Guardian Agent
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client
from utils.formatters import get_status_color, format_risk_level

st.set_page_config(
    page_title="Legal Review | PE-Nexus",
    page_icon="shield",
    layout="wide",
)

# Header
st.title("Legal Review")
st.markdown("**Legal Guardian Agent**")

# Explanation box
st.info("""
**What this agent does:**

The Legal Guardian analyzes contracts and VDR (Virtual Data Room) documents for M&A-critical risks:
- **Change of Control clauses** - May require consent or trigger termination
- **Assignment restrictions** - Limits on transferring contracts
- **Non-compete agreements** - Restrictions on business activities
- **Termination rights** - Early exit provisions
- **Personal guarantees** - Individual liability exposure
- **Acceleration clauses** - Debt repayment triggers

Each finding is scored by **Risk Level** (Critical/High/Medium/Low) with **Deal Impact** assessment.
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
    | **AI Model** | **{llm_status['display_name']}** | Clause detection, risk assessment, legal summarization |
    | AI Type | Large Language Model (LLM) | Generative AI with reasoning capabilities |
    | Agent Framework | LangGraph | State machine-based agent orchestration |
    | Document Processing | pdfplumber | PDF text extraction with coordinates |
    | Vector Store | ChromaDB | Semantic search for clause matching |
    | Backend | FastAPI + Python | Async API endpoints |

    **Supported LLM Providers:**
    - **Groq** (Llama 3.3 70B) - FREE, 30 req/min
    - **Ollama** (Llama 3.2) - FREE, runs locally
    - **Anthropic** (Claude) - Paid, highest quality

    **How the LLM is used in this agent:**
    - Identifies and classifies legal clause types from contract text
    - Assesses risk level and potential deal impact
    - Generates recommendations for each identified risk
    - Creates executive summaries of contract analysis
    - Explains complex legal terms in plain language

    ---

    ### Works Without API Key?  YES

    | Feature | Without API Key | With API Key |
    |---------|-----------------|--------------|
    | Clause Detection | Pattern matching + keywords | AI-enhanced detection |
    | Risk Scoring | Rule-based severity mapping | Same |
    | Contract Data | 6 mock VDR contracts | Same |
    | Recommendations | Template-based | AI-generated advice |
    | Summary | Structured output | Natural language summary |

    *Clause detection uses pattern matching that works without AI - LLM enhances accuracy and explanations.*
    """)

st.markdown("---")

# Check backend status (api already initialized above)
health = api.health_check()
if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# Get available contracts
contracts_result = api.guardian_contracts()
contracts = contracts_result.get("contracts", [])

# Full Analysis Section
st.subheader("Analyze All Contracts")

contract_type_filter = st.selectbox(
    "Filter by Contract Type",
    options=[
        "All Types",
        "customer_agreement",
        "employment",
        "vendor",
        "lease",
        "ip_license",
        "loan",
    ],
)

if st.button("Run Full Analysis", type="primary"):
    filter_type = None if contract_type_filter == "All Types" else contract_type_filter

    with st.spinner("Analyzing contracts..."):
        result = api.guardian_analyze_all(contract_type=filter_type)

    if result.get("success"):
        output = result.get("output", {})
        analyses = output.get("analyses", [])

        st.success(f"Analyzed {output.get('contracts_analyzed', 0)} contracts in {result.get('duration_seconds', 0):.2f}s")

        # Summary metrics
        st.markdown("---")
        st.subheader("Risk Summary")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            critical = output.get("total_critical_flags", 0)
            st.metric(
                label="Critical Flags",
                value=critical,
                delta="Immediate attention" if critical > 0 else None,
                delta_color="inverse",
            )

        with metric_col2:
            high = output.get("total_high_flags", 0)
            st.metric(
                label="High Priority",
                value=high,
            )

        with metric_col3:
            medium = output.get("total_medium_flags", 0)
            st.metric(
                label="Medium Priority",
                value=medium,
            )

        with metric_col4:
            low = output.get("total_low_flags", 0)
            st.metric(
                label="Low Priority",
                value=low,
            )

        # Contract-level results
        st.markdown("---")
        st.subheader("Contract Analysis")

        for analysis in analyses:
            risk_level = analysis.get("overall_risk", "low")
            color, label = format_risk_level(risk_level)

            with st.expander(
                f"{analysis.get('contract_name', 'Unknown')} - {label} RISK",
                expanded=risk_level in ["critical", "high"],
            ):
                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.write(f"**Counterparty:** {analysis.get('counterparty', 'Unknown')}")
                with info_col2:
                    st.write(f"**Contract Type:** {analysis.get('contract_type', 'Unknown')}")
                with info_col3:
                    st.write(f"**Flags Found:** {analysis.get('flag_count', 0)}")

                # Show flags
                flags = analysis.get("flags", [])
                if flags:
                    st.markdown("**Identified Risks:**")

                    for flag in flags:
                        flag_color, flag_label = format_risk_level(flag.get("risk_level", "low"))

                        st.markdown(f"""
                        <div style="border-left: 4px solid {flag_color}; padding-left: 10px; margin: 10px 0;">
                            <strong>{flag.get('clause_type', 'Unknown').replace('_', ' ').title()}</strong>
                            <span style="color: {flag_color};">({flag_label})</span><br>
                            <em>{flag.get('description', 'No description')}</em><br>
                            <small>Deal Impact: {flag.get('deal_impact', 'Unknown')}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        # Recommendations
                        rec = flag.get("recommendation", "")
                        if rec:
                            st.info(f"**Recommendation:** {rec}")
                else:
                    st.success("No significant risks identified in this contract.")

                # Summary
                summary = analysis.get("summary", "")
                if summary:
                    st.markdown("---")
                    st.markdown(f"**Summary:** {summary}")

    else:
        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

# Single Contract Analysis
st.markdown("---")
st.subheader("Analyze Single Contract")

if contracts:
    contract_options = {c.get("contract_name", f"Contract {i}"): c.get("contract_id") for i, c in enumerate(contracts)}

    selected_contract_name = st.selectbox(
        "Select Contract",
        options=list(contract_options.keys()),
    )

    if st.button("Analyze Selected Contract"):
        contract_id = contract_options[selected_contract_name]

        with st.spinner(f"Analyzing {selected_contract_name}..."):
            result = api.guardian_analyze(contract_id=contract_id)

        if result.get("success"):
            output = result.get("output", {})
            analysis = output.get("analysis", {})

            st.success("Analysis complete!")

            risk_level = analysis.get("overall_risk", "low")
            color, label = format_risk_level(risk_level)

            st.markdown(f"""
            <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {color}20;">
                <h2 style="color: {color};">{label} RISK</h2>
                <p>{analysis.get('contract_name', 'Unknown Contract')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Detailed flags
            flags = analysis.get("flags", [])
            if flags:
                st.markdown("---")
                st.markdown("**Detected Issues:**")
                for flag in flags:
                    flag_color, flag_label = format_risk_level(flag.get("risk_level", "low"))
                    st.write(f"- [{flag_label}] **{flag.get('clause_type', '').replace('_', ' ').title()}**: {flag.get('description', '')}")
        else:
            st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
else:
    st.warning("No contracts available in the system.")

# Clause Search
st.markdown("---")
st.subheader("Search for Specific Clause Type")

clause_types = [
    "change_of_control",
    "assignment_restriction",
    "termination_rights",
    "non_compete",
    "non_solicitation",
    "personal_guarantee",
    "acceleration_clause",
    "consent_required",
]

selected_clause = st.selectbox(
    "Clause Type to Search",
    options=clause_types,
    format_func=lambda x: x.replace("_", " ").title(),
)

if st.button("Search for Clause"):
    with st.spinner(f"Searching for {selected_clause.replace('_', ' ')} clauses..."):
        result = api.guardian_check_clause(clause_type=selected_clause)

    if result.get("success"):
        output = result.get("output", {})
        findings = output.get("findings", [])

        st.success(f"Found {len(findings)} contracts with {selected_clause.replace('_', ' ')} clauses")

        if findings:
            import pandas as pd

            df_data = []
            for f in findings:
                df_data.append({
                    "Contract": f.get("contract_name", "Unknown"),
                    "Counterparty": f.get("counterparty", "Unknown"),
                    "Risk Level": f.get("risk_level", "Unknown").upper(),
                    "Description": f.get("description", "")[:100],
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

            # Details
            for finding in findings:
                with st.expander(f"{finding.get('contract_name', 'Unknown')}"):
                    st.write(f"**Description:** {finding.get('description', 'N/A')}")
                    st.write(f"**Deal Impact:** {finding.get('deal_impact', 'N/A')}")
                    st.write(f"**Recommendation:** {finding.get('recommendation', 'N/A')}")
        else:
            st.info(f"No {selected_clause.replace('_', ' ')} clauses found in the analyzed contracts.")
    else:
        st.error(f"Search failed: {result.get('error', 'Unknown error')}")

# Contract List
st.markdown("---")
st.subheader("Available Contracts")

if contracts:
    import pandas as pd

    df_data = []
    for c in contracts:
        df_data.append({
            "Contract Name": c.get("contract_name", "Unknown"),
            "Type": c.get("contract_type", "Unknown"),
            "Counterparty": c.get("counterparty", "Unknown"),
            "Value": c.get("value", "N/A"),
            "Expiration": c.get("expiration_date", "N/A"),
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No contracts loaded. The system includes mock VDR data for demonstration.")
