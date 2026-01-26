"""
FAIR Principles Compliance Page
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_api_client

st.set_page_config(
    page_title="FAIR Compliance | PE-Nexus",
    page_icon="clipboard",
    layout="wide",
)

# Header
st.title("FAIR Principles Compliance")
st.markdown("**Research Data Management Standards**")

# Explanation box
st.info("""
**What are FAIR Principles?**

The FAIR Principles are a set of guiding standards to make data and software:
- **F**indable - Easy to discover by humans and machines
- **A**ccessible - Retrievable via standardized protocols
- **I**nteroperable - Works with other data and systems
- **R**eusable - Well-documented for replication and reuse

These principles are critical for academic research, open science, and software sustainability.

**Why FAIR matters for PE-Nexus:**
- Enables reproducibility of financial analyses
- Supports academic research and citation
- Facilitates integration with other systems
- Ensures long-term accessibility
""")

st.markdown("---")

# Get API client and check backend
api = get_api_client()
health = api.health_check()

if health.get("status") == "offline":
    st.error("Backend is offline. Please start the FastAPI server.")
    st.stop()

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["Score Dashboard", "Principles Detail", "Documentation Files", "JSON-LD Metadata"])

# =============================================================================
# Tab 1: Score Dashboard
# =============================================================================
with tab1:
    st.subheader("FAIR Compliance Score")

    score_result = api.fair_score()

    if "error" not in score_result:
        # Overall score
        overall = score_result.get("overall_percentage", 0)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Large percentage display
            color = "#28A745" if overall >= 70 else "#FFC107" if overall >= 50 else "#DC3545"
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background-color: {color}15; border-radius: 15px; border: 2px solid {color};">
                <h1 style="color: {color}; font-size: 4rem; margin: 0;">{overall}%</h1>
                <p style="font-size: 1.2rem; margin: 10px 0 0 0;">Overall FAIR Compliance</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Category scores
        st.subheader("Category Breakdown")

        categories = score_result.get("category_scores", {})

        cat_col1, cat_col2, cat_col3, cat_col4 = st.columns(4)

        with cat_col1:
            findable = categories.get("findable", "0/4")
            f_score = float(findable.split("/")[0])
            f_max = float(findable.split("/")[1])
            f_pct = (f_score / f_max) * 100 if f_max > 0 else 0
            st.metric(
                label="Findable",
                value=findable,
                delta=f"{f_pct:.0f}%",
            )
            st.progress(f_pct / 100)

        with cat_col2:
            accessible = categories.get("accessible", "0/4")
            a_score = float(accessible.split("/")[0])
            a_max = float(accessible.split("/")[1])
            a_pct = (a_score / a_max) * 100 if a_max > 0 else 0
            st.metric(
                label="Accessible",
                value=accessible,
                delta=f"{a_pct:.0f}%",
            )
            st.progress(a_pct / 100)

        with cat_col3:
            interop = categories.get("interoperable", "0/3")
            i_score = float(interop.split("/")[0])
            i_max = float(interop.split("/")[1])
            i_pct = (i_score / i_max) * 100 if i_max > 0 else 0
            st.metric(
                label="Interoperable",
                value=interop,
                delta=f"{i_pct:.0f}%",
            )
            st.progress(i_pct / 100)

        with cat_col4:
            reusable = categories.get("reusable", "0/4")
            r_score = float(reusable.split("/")[0])
            r_max = float(reusable.split("/")[1])
            r_pct = (r_score / r_max) * 100 if r_max > 0 else 0
            st.metric(
                label="Reusable",
                value=reusable,
                delta=f"{r_pct:.0f}%",
            )
            st.progress(r_pct / 100)

        # Principle counts
        st.markdown("---")
        st.subheader("Principle Status")

        counts = score_result.get("principle_counts", {})

        status_col1, status_col2, status_col3 = st.columns(3)

        with status_col1:
            compliant = counts.get("compliant", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #28A74520; border-radius: 10px;">
                <h2 style="color: #28A745; margin: 0;">{compliant}</h2>
                <p style="margin: 0;">Compliant</p>
            </div>
            """, unsafe_allow_html=True)

        with status_col2:
            partial = counts.get("partial", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #FFC10720; border-radius: 10px;">
                <h2 style="color: #FFC107; margin: 0;">{partial}</h2>
                <p style="margin: 0;">Partial</p>
            </div>
            """, unsafe_allow_html=True)

        with status_col3:
            non_compliant = counts.get("non_compliant", 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #DC354520; border-radius: 10px;">
                <h2 style="color: #DC3545; margin: 0;">{non_compliant}</h2>
                <p style="margin: 0;">Non-Compliant</p>
            </div>
            """, unsafe_allow_html=True)

        # Status message
        status_msg = score_result.get("status", "")
        if status_msg:
            st.success(f"**Status:** {status_msg}")

        # Next steps
        next_steps = score_result.get("next_steps", [])
        if next_steps:
            st.subheader("Next Steps for 100% Compliance")
            for step in next_steps:
                st.markdown(f"- {step}")

    else:
        st.error(f"Failed to load FAIR score: {score_result.get('error', 'Unknown error')}")

# =============================================================================
# Tab 2: Principles Detail
# =============================================================================
with tab2:
    st.subheader("FAIR Principles Assessment")

    principles_result = api.fair_principles()

    if "error" not in principles_result:
        principles = principles_result.get("principles", [])

        # Group by category
        categories_order = ["Findable", "Accessible", "Interoperable", "Reusable"]

        for category in categories_order:
            cat_principles = [p for p in principles if p.get("category") == category]

            if cat_principles:
                st.markdown(f"### {category}")

                for p in cat_principles:
                    status = p.get("status", "unknown")
                    score = p.get("score", 0)

                    # Status color
                    if status == "compliant":
                        color = "#28A745"
                        icon = "check-circle"
                        badge = "COMPLIANT"
                    elif status == "partial":
                        color = "#FFC107"
                        icon = "exclamation-circle"
                        badge = "PARTIAL"
                    else:
                        color = "#DC3545"
                        icon = "x-circle"
                        badge = "GAP"

                    with st.expander(f"**{p.get('id')}**: {p.get('principle')} - [{badge}]"):
                        # Status badge
                        st.markdown(f"""
                        <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">
                            {badge} ({score:.1f}/1.0)
                        </span>
                        """, unsafe_allow_html=True)

                        st.markdown("")

                        # Evidence
                        evidence = p.get("evidence", [])
                        if evidence:
                            st.markdown("**Evidence:**")
                            for e in evidence:
                                st.markdown(f"- {e}")

                        # Gap
                        gap = p.get("gap")
                        if gap:
                            st.warning(f"**Gap:** {gap}")

                st.markdown("---")
    else:
        st.error(f"Failed to load principles: {principles_result.get('error', 'Unknown error')}")

# =============================================================================
# Tab 3: Documentation Files
# =============================================================================
with tab3:
    st.subheader("FAIR Documentation Files")

    files_result = api.fair_files()

    if "error" not in files_result:
        # Root files
        st.markdown("### Root Directory Files")

        root_files = files_result.get("root_files", [])

        for f in root_files:
            status_color = "#28A745" if f.get("status") == "present" else "#DC3545"
            st.markdown(f"""
            <div style="border-left: 3px solid {status_color}; padding: 8px 15px; margin: 5px 0; background-color: #f8f9fa;">
                <strong><code>{f.get('file')}</code></strong>
                <span style="color: #666; margin-left: 10px;">{f.get('purpose')}</span>
            </div>
            """, unsafe_allow_html=True)

        # GitHub files
        st.markdown("### GitHub Directory Files")

        github_files = files_result.get("github_files", [])

        for f in github_files:
            status_color = "#28A745" if f.get("status") == "present" else "#DC3545"
            st.markdown(f"""
            <div style="border-left: 3px solid {status_color}; padding: 8px 15px; margin: 5px 0; background-color: #f8f9fa;">
                <strong><code>{f.get('file')}</code></strong>
                <span style="color: #666; margin-left: 10px;">{f.get('purpose')}</span>
            </div>
            """, unsafe_allow_html=True)

        # Docs files
        st.markdown("### Documentation Files")

        docs_files = files_result.get("docs_files", [])

        for f in docs_files:
            status_color = "#28A745" if f.get("status") == "present" else "#DC3545"
            st.markdown(f"""
            <div style="border-left: 3px solid {status_color}; padding: 8px 15px; margin: 5px 0; background-color: #f8f9fa;">
                <strong><code>{f.get('file')}</code></strong>
                <span style="color: #666; margin-left: 10px;">{f.get('purpose')}</span>
            </div>
            """, unsafe_allow_html=True)

        # Code features
        st.markdown("### Code-Level FAIR Features")

        code_features = files_result.get("code_features", [])

        for f in code_features:
            st.markdown(f"""
            <div style="border-left: 3px solid #17A2B8; padding: 8px 15px; margin: 5px 0; background-color: #f8f9fa;">
                <strong>{f.get('feature')}</strong>
                <span style="color: #666; margin-left: 10px;">
                    <code>{f.get('location')}</code> | FAIR: {f.get('fair_principle')}
                </span>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.error(f"Failed to load files: {files_result.get('error', 'Unknown error')}")

# =============================================================================
# Tab 4: JSON-LD Metadata
# =============================================================================
with tab4:
    st.subheader("Machine-Readable Metadata")

    st.markdown("""
    This JSON-LD metadata follows the [CodeMeta](https://codemeta.github.io/) specification,
    enabling machine-readable software metadata for discovery and citation.
    """)

    metadata_result = api.fair_metadata()

    if "error" not in metadata_result:
        # Display key info
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Project Information**")
            st.write(f"- **Name:** {metadata_result.get('name')}")
            st.write(f"- **Version:** {metadata_result.get('version')}")
            st.write(f"- **License:** MIT")
            st.write(f"- **Language:** {metadata_result.get('programmingLanguage')}")
            st.write(f"- **Category:** {metadata_result.get('applicationCategory')}")

        with col2:
            st.markdown("**FAIR Compliance**")
            compliance = metadata_result.get("fairCompliance", {})
            scores = compliance.get("scores", {})
            st.write(f"- **Assessment Date:** {compliance.get('assessmentDate')}")
            st.write(f"- **Overall Score:** {scores.get('percentage', 0)}%")
            st.write(f"- **Status:** {compliance.get('status')}")

        st.markdown("---")

        # Raw JSON-LD
        st.markdown("### Raw JSON-LD")

        import json
        st.code(json.dumps(metadata_result, indent=2), language="json")

        # Download button
        st.download_button(
            label="Download JSON-LD Metadata",
            data=json.dumps(metadata_result, indent=2),
            file_name="pe-nexus-metadata.jsonld",
            mime="application/ld+json",
        )

        # API endpoint info
        st.markdown("### API Endpoints")

        st.markdown("""
        Access FAIR metadata programmatically:

        | Endpoint | Description |
        |----------|-------------|
        | `GET /fair/metadata` | JSON-LD metadata |
        | `GET /fair/principles` | Detailed principles assessment |
        | `GET /fair/score` | Compliance score summary |
        | `GET /fair/files` | Documentation files list |

        **Example:**
        ```bash
        curl http://localhost:8000/fair/metadata
        ```
        """)

    else:
        st.error(f"Failed to load metadata: {metadata_result.get('error', 'Unknown error')}")

# Footer
st.markdown("---")
st.markdown("""
**References:**
- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [CodeMeta](https://codemeta.github.io/)
- [Citation File Format](https://citation-file-format.github.io/)
- [Zenodo](https://zenodo.org/)
""")
