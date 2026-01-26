"""
PE-Nexus Card Components.

Reusable card components for the Deal Command Center UI.
"""

import streamlit as st
from typing import Optional, List
from .theme import get_score_color, get_score_tier, COLORS


def render_company_card(
    rank: int,
    company_name: str,
    sector: str,
    nexus_score: float,
    revenue: float,
    ebitda: float,
    summary: str,
    tags: List[str],
    company_id: str,
    show_deep_dive: bool = True,
) -> bool:
    """
    Render a company card for the leaderboard.

    Returns True if the Deep Dive button was clicked.
    """
    score_color = get_score_color(nexus_score)
    score_tier = get_score_tier(nexus_score)
    score_class = f"nexus-score-{'high' if score_tier == 'HIGH' else 'medium' if score_tier == 'MEDIUM' else 'low'}"

    # Build tags HTML
    tags_html = ""
    for tag in tags:
        tag_lower = tag.lower().replace(" ", "-").replace("_", "-")
        tag_class = f"tag-{tag_lower}" if tag_lower in ["high-growth", "pe-interest", "outperforming", "at-risk", "watch", "expansion"] else "tag-default"
        tags_html += f'<span class="tag {tag_class}">{tag}</span>'

    card_html = f"""
    <div class="company-card" id="card-{company_id}">
        <div class="company-card-header">
            <div>
                <span class="company-rank">#{rank}</span>
                <span class="company-name">{company_name}</span>
                <div class="company-sector">{sector}</div>
            </div>
            <div class="nexus-score">
                <span class="nexus-score-label">Nexus Score</span>
                <span class="nexus-score-value {score_class}">{nexus_score:.0f}</span>
            </div>
        </div>

        <div class="company-financials">
            <span class="company-financial-item">
                Revenue: <span class="company-financial-value">${revenue:.1f}M</span>
            </span>
            <span class="company-financial-item">
                EBITDA: <span class="company-financial-value">${ebitda:.1f}M</span>
            </span>
            <span class="company-financial-item">
                Margin: <span class="company-financial-value">{(ebitda/revenue*100):.1f}%</span>
            </span>
        </div>

        <div class="company-summary">"{summary}"</div>

        <div class="company-footer">
            <div>{tags_html}</div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # Deep Dive button as actual Streamlit button for interactivity
    if show_deep_dive:
        return st.button(
            "Deep Dive",
            key=f"deep_dive_{company_id}",
            type="primary",
            use_container_width=False,
        )

    return False


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_direction: Optional[str] = None,  # "positive", "negative", "neutral"
) -> None:
    """Render a metric card with optional delta indicator."""
    delta_class = ""
    delta_html = ""

    if delta:
        if delta_direction == "positive":
            delta_class = "metric-delta-positive"
            delta_prefix = "+"
        elif delta_direction == "negative":
            delta_class = "metric-delta-negative"
            delta_prefix = ""
        else:
            delta_class = "metric-delta-neutral"
            delta_prefix = ""

        delta_html = f'<div class="metric-card-delta {delta_class}">{delta_prefix}{delta}</div>'

    card_html = f"""
    <div class="metric-card">
        <div class="metric-card-label">{label}</div>
        <div class="metric-card-value">{value}</div>
        {delta_html}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_tag(text: str, tag_type: str = "default") -> str:
    """
    Render a tag/badge.

    tag_type: "high-growth", "pe-interest", "outperforming", "at-risk", "watch", "expansion", "default"
    """
    tag_class = f"tag-{tag_type}"
    return f'<span class="tag {tag_class}">{text}</span>'


def render_alert_badge(count: int, severity: str) -> str:
    """
    Render an alert badge.

    severity: "critical", "high", "medium", "low"
    """
    severity_lower = severity.lower()
    return f'<span class="alert-badge alert-{severity_lower}">{count} {severity.title()}</span>'


def render_score_badge(score: float, show_label: bool = True) -> None:
    """Render a Nexus Score badge."""
    score_color = get_score_color(score)
    score_tier = get_score_tier(score)
    score_class = f"nexus-score-{'high' if score_tier == 'HIGH' else 'medium' if score_tier == 'MEDIUM' else 'low'}"

    label_html = '<span class="nexus-score-label">Nexus Score</span>' if show_label else ""

    badge_html = f"""
    <div class="nexus-score">
        {label_html}
        <span class="nexus-score-value {score_class}">{score:.0f}</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)


def render_info_box(content: str, box_type: str = "info") -> None:
    """
    Render an info box.

    box_type: "info", "warning", "success"
    """
    box_class = {
        "info": "info-box-dark",
        "warning": "warning-box-dark",
        "success": "success-box-dark",
    }.get(box_type, "info-box-dark")

    st.markdown(f'<div class="{box_class}">{content}</div>', unsafe_allow_html=True)


def render_section_header(title: str) -> None:
    """Render a section header."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def render_verdict_box(
    recommendation: str,  # "APPROVE", "APPROVE WITH CONDITIONS", "REJECT"
    confidence: float,
    thesis: str,
) -> None:
    """Render the verdict/recommendation box."""
    rec_lower = recommendation.lower()
    if "reject" in rec_lower:
        rec_class = "verdict-reject"
    elif "condition" in rec_lower:
        rec_class = "verdict-conditional"
    else:
        rec_class = "verdict-approve"

    verdict_html = f"""
    <div class="verdict-container">
        <div class="nexus-score-label">Investment Recommendation</div>
        <div class="verdict-recommendation {rec_class}">{recommendation}</div>
        <div class="verdict-confidence">Confidence: {confidence:.0f}%</div>
        <div style="margin-top: 1rem; text-align: left;">
            <p style="color: var(--text-secondary); font-style: italic;">"{thesis}"</p>
        </div>
    </div>
    """

    st.markdown(verdict_html, unsafe_allow_html=True)


def render_back_button() -> bool:
    """Render a back to dashboard button. Returns True if clicked."""
    st.markdown(
        '<div class="back-button">Back to Dashboard</div>',
        unsafe_allow_html=True,
    )
    return st.button("Back to Dashboard", key="back_to_dashboard")


def render_key_finding(
    icon: str,  # e.g., "!" or "OK" or "X"
    text: str,
    severity: str = "medium",  # "critical", "high", "medium", "low"
) -> None:
    """Render a key finding item."""
    severity_colors = {
        "critical": COLORS["accent_red"],
        "high": COLORS["accent_orange"],
        "medium": COLORS["accent_yellow"],
        "low": COLORS["accent_green"],
    }
    color = severity_colors.get(severity.lower(), COLORS["text_secondary"])

    finding_html = f"""
    <div style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem;">
        <span style="color: {color}; font-weight: 600;">{icon}</span>
        <span style="color: var(--text-secondary);">{text}</span>
    </div>
    """

    st.markdown(finding_html, unsafe_allow_html=True)
