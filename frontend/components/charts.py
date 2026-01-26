"""
PE-Nexus Chart Components.

Visual components for scores, sparklines, and progress indicators.
"""

import streamlit as st
from typing import List, Optional
from .theme import get_score_color, get_score_tier, COLORS


def render_score_gauge(
    score: float,
    max_score: float = 100,
    label: Optional[str] = None,
    size: str = "medium",  # "small", "medium", "large"
) -> None:
    """
    Render a circular score gauge.

    Uses SVG for a clean visual representation.
    """
    percentage = (score / max_score) * 100
    score_color = get_score_color(score)
    score_tier = get_score_tier(score)

    # Size configurations
    sizes = {
        "small": {"width": 60, "stroke": 6, "font": 14},
        "medium": {"width": 100, "stroke": 8, "font": 24},
        "large": {"width": 140, "stroke": 10, "font": 32},
    }
    config = sizes.get(size, sizes["medium"])

    width = config["width"]
    stroke = config["stroke"]
    font_size = config["font"]
    radius = (width - stroke) / 2
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1 - percentage / 100)

    label_html = f'<div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;">{label}</div>' if label else ""

    gauge_html = f"""
    <div style="text-align: center;">
        <svg width="{width}" height="{width}" viewBox="0 0 {width} {width}">
            <!-- Background circle -->
            <circle
                cx="{width/2}"
                cy="{width/2}"
                r="{radius}"
                fill="none"
                stroke="{COLORS['bg_hover']}"
                stroke-width="{stroke}"
            />
            <!-- Progress circle -->
            <circle
                cx="{width/2}"
                cy="{width/2}"
                r="{radius}"
                fill="none"
                stroke="{score_color}"
                stroke-width="{stroke}"
                stroke-linecap="round"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{dash_offset}"
                transform="rotate(-90 {width/2} {width/2})"
                style="transition: stroke-dashoffset 0.5s ease;"
            />
            <!-- Score text -->
            <text
                x="{width/2}"
                y="{width/2}"
                text-anchor="middle"
                dominant-baseline="central"
                fill="{score_color}"
                font-size="{font_size}"
                font-weight="700"
                font-family="'SF Mono', monospace"
            >{score:.0f}</text>
        </svg>
        {label_html}
    </div>
    """

    st.markdown(gauge_html, unsafe_allow_html=True)


def render_mini_sparkline(
    values: List[float],
    width: int = 100,
    height: int = 30,
    color: Optional[str] = None,
    show_trend: bool = True,
) -> None:
    """
    Render a mini sparkline chart.

    Shows trend direction with simple line visualization.
    """
    if not values or len(values) < 2:
        st.markdown('<span style="color: var(--text-muted);">--</span>', unsafe_allow_html=True)
        return

    # Determine trend
    trend = "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "flat"
    line_color = color or (COLORS["accent_green"] if trend == "up" else COLORS["accent_red"] if trend == "down" else COLORS["text_secondary"])

    # Normalize values to fit in height
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1
    padding = 2

    # Generate SVG path points
    points = []
    for i, val in enumerate(values):
        x = padding + (i / (len(values) - 1)) * (width - 2 * padding)
        y = height - padding - ((val - min_val) / val_range) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")

    polyline_points = " ".join(points)

    # Trend indicator
    trend_html = ""
    if show_trend:
        if trend == "up":
            trend_html = f'<span style="color: {COLORS["accent_green"]}; font-size: 0.75rem; margin-left: 0.25rem;">+{((values[-1] - values[0]) / values[0] * 100):.1f}%</span>'
        elif trend == "down":
            trend_html = f'<span style="color: {COLORS["accent_red"]}; font-size: 0.75rem; margin-left: 0.25rem;">{((values[-1] - values[0]) / values[0] * 100):.1f}%</span>'

    sparkline_html = f"""
    <div style="display: inline-flex; align-items: center;">
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            <polyline
                points="{polyline_points}"
                fill="none"
                stroke="{line_color}"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
        </svg>
        {trend_html}
    </div>
    """

    st.markdown(sparkline_html, unsafe_allow_html=True)


def render_progress_bar(
    value: float,
    max_value: float = 100,
    label: Optional[str] = None,
    show_percentage: bool = True,
    height: int = 8,
) -> None:
    """Render a horizontal progress bar."""
    percentage = min((value / max_value) * 100, 100)
    bar_color = get_score_color(percentage)

    tier = get_score_tier(percentage)
    progress_class = f"progress-{'high' if tier == 'HIGH' else 'medium' if tier == 'MEDIUM' else 'low'}"

    label_html = f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">{label}</div>' if label else ""
    percentage_html = f'<span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.5rem;">{percentage:.0f}%</span>' if show_percentage else ""

    progress_html = f"""
    <div>
        {label_html}
        <div style="display: flex; align-items: center;">
            <div class="progress-container" style="flex: 1; height: {height}px;">
                <div class="progress-bar {progress_class}" style="width: {percentage}%;"></div>
            </div>
            {percentage_html}
        </div>
    </div>
    """

    st.markdown(progress_html, unsafe_allow_html=True)


def render_score_breakdown(
    breakdown: dict,
    labels: Optional[dict] = None,
) -> None:
    """
    Render a score breakdown showing component scores using native Streamlit components.

    breakdown: {"market": 85, "health": 72, "risk": 30, ...}
    labels: {"market": "Market Position", ...}
    """
    default_labels = {
        "market": "Market Position",
        "health": "Financial Health",
        "risk": "Risk Level",
        "confidence": "IC Confidence",
        "returns": "Returns Potential",
    }
    labels = labels or default_labels

    with st.container(border=True):
        st.caption("SCORE BREAKDOWN")
        for key, score in breakdown.items():
            label = labels.get(key, key.title())
            
            # For risk, lower is better, but bar should reflect "safety" or just raw score?
            # Convention: Higher bar = Better for non-risk. For risk, let's just show the raw score.
            # Actually, standard visual is usually 0-100.
            
            # Use native progress bar
            st.markdown(f"**{label}**")
            st.progress(score / 100, text=f"{score}/100")


def render_mini_metric(
    value: str,
    label: str,
    trend: Optional[str] = None,  # "up", "down", "flat"
    trend_value: Optional[str] = None,
) -> None:
    """Render a compact inline metric."""
    trend_html = ""
    if trend and trend_value:
        trend_color = COLORS["accent_green"] if trend == "up" else COLORS["accent_red"] if trend == "down" else COLORS["text_secondary"]
        trend_prefix = "+" if trend == "up" else ""
        trend_html = f'<span style="color: {trend_color}; font-size: 0.75rem;"> {trend_prefix}{trend_value}</span>'

    metric_html = f"""
    <div style="text-align: center; padding: 0.5rem;">
        <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); font-family: 'SF Mono', monospace;">
            {value}{trend_html}
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.03em;">
            {label}
        </div>
    </div>
    """

    st.markdown(metric_html, unsafe_allow_html=True)


def render_risk_indicator(
    level: str,  # "critical", "high", "medium", "low"
    count: int = 0,
) -> None:
    """Render a risk level indicator."""
    level_configs = {
        "critical": {"color": COLORS["accent_red"], "bg": "rgba(248, 81, 73, 0.15)"},
        "high": {"color": COLORS["accent_orange"], "bg": "rgba(219, 109, 40, 0.15)"},
        "medium": {"color": COLORS["accent_yellow"], "bg": "rgba(210, 153, 34, 0.15)"},
        "low": {"color": COLORS["accent_green"], "bg": "rgba(63, 185, 80, 0.15)"},
    }

    config = level_configs.get(level.lower(), level_configs["medium"])

    indicator_html = f"""
    <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: {config['bg']}; padding: 0.375rem 0.75rem; border-radius: 6px;">
        <div style="width: 8px; height: 8px; border-radius: 50%; background-color: {config['color']};"></div>
        <span style="color: {config['color']}; font-weight: 600; font-size: 0.875rem;">{level.upper()}</span>
        {f'<span style="color: var(--text-secondary); font-size: 0.75rem;">({count})</span>' if count > 0 else ''}
    </div>
    """

    st.markdown(indicator_html, unsafe_allow_html=True)
