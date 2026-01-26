
import streamlit as st
from components.cards import render_metric_card
from components.charts import render_score_breakdown
from utils.mock_data import get_mock_company_detail

def render_scout_section(scout_data: dict):
    """Render Scout Agent data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([3, 1])
        with c_head:
            st.subheader("🔍 Market Intelligence")
            st.caption("AI Agent analyzing market signals and competitive landscape.")
        with c_btn:
            if st.button("Deep Dive", key="btn_scout", help="View detailed AI reasoning and data sources", use_container_width=True):
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
            
        with st.expander("Why am I seeing this?"):
            st.write("The Scout Agent aggregates data from news feeds, industry reports, and market databases to score opportunities based on your investment thesis alignment.")
        st.caption("🤖 AI Generated Content - Verify with original sources")


def render_navigator_section(navigator_data: dict):
    """Render Navigator Agent data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([3, 1])
        with c_head:
            st.subheader("🤝 Relationship Intelligence")
            st.caption("AI Agent mapping path to key decision makers.")
        with c_btn:
            if st.button("Deep Dive", key="btn_navigator", help="View graph analysis and connection paths", use_container_width=True):
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
        
        with st.expander("Privacy & Data Source"):
            st.write("Relationship data is synthesized from public professional networks (e.g. LinkedIn) and your firm's internal CRM. No private emails are scanned.")
        st.caption("🤖 AI Generated Content - Connections are probabilistic")


def render_financial_section(financial_data: dict, strategist_data: dict, key_suffix: str = ""):
    """Render financial and strategist data."""
    with st.container(border=True):
        c_head, c_btn = st.columns([3, 1])
        with c_head:
            st.subheader("💰 Financial Analysis")
        with c_btn:
            if st.button("Deep Dive", key=f"btn_strategist{key_suffix}", help="View financial models and assumptions", use_container_width=True):
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
        st.caption("LBO MODEL PROJECTIONS (AI GENERATED)")
        
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
                
        with st.expander("Model Confidence"):
            st.write("This projection uses standard LBO templates. Confidence is medium as private financial data may be incomplete.")
        st.caption("🤖 AI Generated Content - For estimation only")


def render_risk_section(guardian_data: dict):
    """Render Guardian Agent risk analysis."""
    with st.container(border=True):
        c_head, c_btn = st.columns([3, 1])
        with c_head:
            st.subheader("⚠️ Risk Analysis")
        with c_btn:
            if st.button("Deep Dive", key="btn_guardian", help="View detected legal risks and compliance issues", use_container_width=True):
                st.session_state.selected_agent = "Guardian Agent"
                st.rerun()
        
        st.caption("🤖 AI Generated Content - Legal review required")
        
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
                st.progress(bar_value / 100, text=f"{label}: {score}") 
    
    with col2:
        with st.container(border=True):
            c_head, c_btn = st.columns([3, 1])
            with c_head:
                st.subheader("🎯 Investment Recommendation")
            with c_btn:
                if st.button("Agent Analysis →", key=f"btn_ic{key_suffix}", help="View Investment Committee reasoning"):
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
            
            # PAIR: Feedback
            c_feed1, c_feed2 = st.columns([1, 4])
            with c_feed1:
                st.caption("Was this helpful?")
            with c_feed2:
                b1, b2 = st.columns([1, 10])
                with b1: st.button("👍", key=f"up_{key_suffix}")
                with b2: st.button("👎", key=f"down_{key_suffix}")


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

    # PAIR: Explicit Disclaimer
    st.markdown(f"""
    <div style="background-color: #FFF7ED; border: 1px solid #FFEDD5; color: #9A3412; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
        <span>🤖</span>
        <span><strong>AI Agent Output:</strong> This analysis was generated by the <strong>{agent_name}</strong>. It simulates human reasoning but may hallucinate facts. check sources below.</span>
    </div>
    """, unsafe_allow_html=True)
    
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

    # PAIR: Feedback & Overridability (Human-in-the-loop)
    st.divider()
    st.subheader("👨‍💻 Human Review")
    
    f1, f2 = st.columns([2, 2])
    with f1:
        st.caption("Rate this agent's performance:")
        c1, c2 = st.columns([1, 4])
        with c1: st.button("👍 Helpful", key=f"fdbk_up_{hash(agent_name)}")
        with c2: st.button("👎 Issues", key=f"fdbk_down_{hash(agent_name)}")
        
    with f2:
        st.caption("Action:")
        st.button("Override / Edit Analysis", key=f"edit_{hash(agent_name)}")
