"""
PE-Nexus - Unified Company Intelligence Platform
Single-page application with company browse and detail views.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from components.theme import apply_theme
from components.company_views import (
    render_top_navbar, render_browse_view, render_detail_view,
    render_portfolio_dashboard, render_portfolio_company_detail
)
from components.agent_views import render_agent_deep_dive
# Mock data mock_data imports are used inside the components now, 
# but we might need API client initialization if we want it global, 
# though it's better to keep it where used or in a context.
# We'll leave it to the components to fetch what they need.


# Page configuration
st.set_page_config(
    page_title="PE-Nexus | Company Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply light theme
apply_theme()

# Initialize session state (ensure all keys are present)
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "deal_flow"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "ai_transparency_open" not in st.session_state:
    st.session_state.ai_transparency_open = False


def render_ai_transparency_sidebar():
    """Render the PAIR Principles / AI Transparency Sidebar."""
    with st.sidebar:
        st.header("AI Transparency")
        st.info("PE-Nexus is built with Privacy, Fairness, and Explainability in mind.")
        
        with st.expander("How AI Works Here"):
            st.write("""
            **Scout Agent**: Aggregates public market data.
            **Strategist Agent**: Uses standard financial modeling templates.
            **Guardian Agent**: Rules-based compliance checking.
            
            We do not train models on your private deal flow.
            """)
        
        with st.expander("Data Privacy"):
            st.write("Your data remains in your private cloud environment. No data leaves VDE boundaries.")
        
        st.caption(f"v0.1.0 | FAIR Compliant")


def main():
    """Main application entry point."""
    render_top_navbar()
    render_ai_transparency_sidebar()
    
    # Logic to switch views
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
