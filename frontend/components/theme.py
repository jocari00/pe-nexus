"""
PE-Nexus Light Theme - Modern Mailchimp-inspired styling.

This module provides light mode CSS injection and color/font constants
for a clean, professional aesthetic.
"""

import streamlit as st

# =============================================================================
# COLOR PALETTE (Mailchimp-inspired Light Theme)
# =============================================================================

COLORS = {
    # Primary Backgrounds
    "bg_primary": "#F5F7FB",      # Light gray-blue background
    "bg_secondary": "#FFFFFF",    # White
    "bg_card": "#FFFFFF",         # White cards
    "bg_hover": "#EEF2F7",        # Subtle hover
    "bg_input": "#FFFFFF",        # Input field backgrounds

    # Borders
    "border_default": "#E5E7EB",
    "border_muted": "#F3F4F6",
    "border_highlight": "#3B82F6",

    # Text
    "text_primary": "#111827",    # Darker text
    "text_secondary": "#374151",  # Dark gray
    "text_muted": "#4B5563",      # Medium gray (Accessible)
    "text_link": "#3B82F6",       # Links

    # Accents
    "accent_blue": "#3B82F6",     # Primary blue
    "accent_green": "#10B981",    # Positive/success
    "accent_yellow": "#F59E0B",   # Warning
    "accent_orange": "#F97316",   # High priority
    "accent_red": "#EF4444",      # Danger/critical
    "accent_purple": "#8B5CF6",   # Special highlights

    # Score Colors
    "score_high": "#10B981",      # 75-100
    "score_medium": "#F59E0B",    # 50-74
    "score_low": "#EF4444",       # 0-49

    # Status Colors
    "status_outperforming": "#3B82F6",
    "status_on_track": "#10B981",
    "status_watch": "#F59E0B",
    "status_at_risk": "#EF4444",
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================

FONTS = {
    "mono": "'SF Mono', 'Fira Code', 'Consolas', monospace",
    "sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",

    # Sizes
    "size_xs": "0.75rem",
    "size_sm": "0.875rem",
    "size_base": "1rem",
    "size_lg": "1.125rem",
    "size_xl": "1.25rem",
    "size_2xl": "1.5rem",
    "size_3xl": "2rem",
}


def get_score_color(score: float) -> str:
    """Get color based on score value (0-100)."""
    if score >= 75:
        return COLORS["score_high"]
    elif score >= 50:
        return COLORS["score_medium"]
    else:
        return COLORS["score_low"]


def get_score_tier(score: float) -> str:
    """Get tier label based on score."""
    if score >= 75:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "LOW"


# =============================================================================
# LIGHT THEME CSS (Mailchimp-inspired)
# =============================================================================

LIGHT_THEME_CSS = """
<style>
/* ==========================================================================
   PE-NEXUS LIGHT THEME - Mailchimp-Inspired
   ========================================================================== */

/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Root Variables */
:root {
    --bg-primary: #F5F7FB;
    --bg-secondary: #FFFFFF;
    --bg-card: #FFFFFF;
    --bg-hover: #EEF2F7;
    --border-default: #E5E7EB;
    --border-muted: #F3F4F6;
    --text-primary: #111827;
    --text-secondary: #374151;
    --text-muted: #4B5563;
    --accent-blue: #3B82F6;
    --accent-green: #10B981;
    --accent-yellow: #F59E0B;
    --accent-red: #EF4444;
    --accent-purple: #8B5CF6;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Global Font Family - Targeted to Text Elements only to preserve Icons */
.stApp, .stMarkdown, h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

/* Ensure Material Icons are not overridden */
.material-icons, .material-symbols-outlined {
    font-family: 'Material Icons' !important;
}

/* Main App Background */
.stApp {
    background-color: var(--bg-primary);
}

[data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary);
}

[data-testid="stHeader"] {
    background-color: var(--bg-primary);
}

/* Hide Sidebar for single-page mode */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Main content area */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Text Colors */
.stMarkdown, .stText, p, span, label {
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
}

/* ==========================================================================
   TOP HEADER / NAVBAR
   ========================================================================== */

.top-navbar {
    background-color: var(--bg-secondary);
    padding: 0.75rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-default);
    margin: -1.5rem -1rem 1.5rem -1rem;
}

.logo {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent-blue);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.search-box {
    display: flex;
    align-items: center;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    width: 300px;
}

/* ==========================================================================
   BREADCRUMB
   ========================================================================== */

.breadcrumb {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
}

.breadcrumb a {
    color: var(--text-secondary);
    text-decoration: none;
}

.breadcrumb a:hover {
    color: var(--accent-blue);
}

/* ==========================================================================
   COMPANY PROFILE HEADER
   ========================================================================== */

.profile-header {
    background-color: var(--bg-secondary);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-default);
}

.profile-header-content {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.profile-logo {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--accent-blue) 0%, #1E40AF 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 2rem;
    font-weight: 700;
}

.profile-info {
    flex: 1;
}

.profile-name {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.profile-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    background-color: rgba(16, 185, 129, 0.1);
    color: var(--accent-green);
    border: 1px solid rgba(16, 185, 129, 0.2);
}

.profile-meta {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

.profile-metrics {
    display: flex;
    gap: 2rem;
    margin-left: auto;
}

.profile-metric {
    text-align: center;
}

.profile-metric-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent-blue);
}

.profile-metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.profile-actions {
    display: flex;
    gap: 0.75rem;
}

.btn-secondary {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    border: 1px solid var(--border-default);
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background-color: var(--bg-hover);
    border-color: var(--accent-blue);
}

.btn-primary {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    border: none;
    background-color: var(--accent-blue);
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    background-color: #2563EB;
}

/* ==========================================================================
   TAB NAVIGATION
   ========================================================================== */

.tab-nav {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border-default);
    margin-bottom: 1.5rem;
}

.tab-item {
    padding: 0.75rem 1.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
}

.tab-item:hover {
    color: var(--text-primary);
}

.tab-item.active {
    color: var(--accent-blue);
    border-bottom-color: var(--accent-blue);
}

/* Streamlit Tabs Override */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    gap: 0;
    border-bottom: 1px solid var(--border-default);
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: var(--text-secondary);
    border-radius: 0;
    padding: 0.75rem 1.5rem;
    border-bottom: 2px solid transparent;
}

.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: var(--accent-blue) !important;
    border-bottom-color: var(--accent-blue) !important;
}

/* ==========================================================================
   PROFILE CARDS
   ========================================================================== */

.profile-card {
    background-color: var(--bg-card);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-default);
    margin-bottom: 1rem;
}

.profile-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.profile-card-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.profile-card-action {
    font-size: 0.875rem;
    color: var(--accent-blue);
    cursor: pointer;
}

/* ==========================================================================
   METRICS ROW
   ========================================================================== */

.metrics-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.metric-box {
    flex: 1;
    background-color: var(--bg-card);
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-default);
    text-align: center;
}

.metric-box-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.metric-box-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.metric-box-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ==========================================================================
   COMPANY BROWSE GRID
   ========================================================================== */

.company-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1rem;
}

.company-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 12px;
    padding: 1.25rem;
    transition: all 0.2s ease;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
}

.company-card:hover {
    border-color: var(--accent-blue);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.company-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
}

.company-card-logo {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--accent-blue) 0%, #1E40AF 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.25rem;
    font-weight: 700;
}

.company-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.company-sector {
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.company-financials {
    display: flex;
    gap: 1.5rem;
    margin: 0.75rem 0;
    font-size: 0.875rem;
}

.company-financial-item {
    color: var(--text-secondary);
}

.company-financial-value {
    color: var(--text-primary);
    font-weight: 600;
}

.company-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-muted);
}

/* ==========================================================================
   NEXUS SCORE BADGE
   ========================================================================== */

.nexus-score {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.nexus-score-label {
    font-size: 0.625rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.nexus-score-value {
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'SF Mono', 'Fira Code', monospace !important;
}

.nexus-score-high {
    color: var(--accent-green);
}

.nexus-score-medium {
    color: var(--accent-yellow);
}

.nexus-score-low {
    color: var(--accent-red);
}

/* ==========================================================================
   TAGS & BADGES
   ========================================================================== */

.tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.5rem;
    margin-bottom: 0.25rem;
}

.tag-high-growth {
    background-color: rgba(16, 185, 129, 0.1);
    color: var(--accent-green);
}

.tag-pe-interest {
    background-color: rgba(59, 130, 246, 0.1);
    color: var(--accent-blue);
}

.tag-outperforming {
    background-color: rgba(59, 130, 246, 0.1);
    color: var(--accent-blue);
}

.tag-at-risk {
    background-color: rgba(239, 68, 68, 0.1);
    color: var(--accent-red);
}

.tag-watch {
    background-color: rgba(245, 158, 11, 0.1);
    color: var(--accent-yellow);
}

.tag-expansion {
    background-color: rgba(139, 92, 246, 0.1);
    color: var(--accent-purple);
}

.tag-default {
    background-color: rgba(107, 114, 128, 0.1);
    color: var(--text-secondary);
}

/* ==========================================================================
   ABOUT COMPANY SECTION
   ========================================================================== */

.about-section {
    line-height: 1.6;
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

.tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
}

.social-icons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.social-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background-color: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.social-icon:hover {
    background-color: var(--accent-blue);
    color: white;
}

/* ==========================================================================
   CONTACTS SECTION
   ========================================================================== */

.contact-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
}

.contact-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
}

.contact-info {
    flex: 1;
}

.contact-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
}

.contact-role {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* ==========================================================================
   NEWS ITEMS
   ========================================================================== */

.news-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-muted);
}

.news-item:last-child {
    border-bottom: none;
}

.news-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--accent-blue);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    flex-shrink: 0;
}

.news-content {
    flex: 1;
}

.news-author {
    font-size: 0.75rem;
    color: var(--accent-blue);
    font-weight: 500;
}

.news-date {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-left: 0.5rem;
}

.news-title {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

/* ==========================================================================
   CHARTS
   ========================================================================== */

.chart-container {
    background-color: var(--bg-card);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-default);
    margin-bottom: 1rem;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.chart-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
}

.chart-legend {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

/* ==========================================================================
   COMPETITOR ROW
   ========================================================================== */

.competitor-row {
    display: flex;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-muted);
}

.competitor-row:last-child {
    border-bottom: none;
}

.competitor-logo {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background-color: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.75rem;
}

.competitor-info {
    flex: 1;
}

.competitor-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
}

.competitor-desc {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.competitor-trend {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ==========================================================================
   SECTION HEADERS
   ========================================================================== */

.section-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-muted);
}

/* ==========================================================================
   VERDICT / RECOMMENDATION BOX
   ========================================================================== */

.verdict-container {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-primary) 100%);
    border: 2px solid var(--border-default);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
}

.verdict-recommendation {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 1rem 0;
}

.verdict-approve {
    color: var(--accent-green);
}

.verdict-conditional {
    color: var(--accent-yellow);
}

.verdict-reject {
    color: var(--accent-red);
}

/* ==========================================================================
   METRIC CARDS
   ========================================================================== */

.metric-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    text-align: center;
    box-shadow: var(--shadow-sm);
}

.metric-card-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.metric-card-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    font-family: 'SF Mono', monospace !important;
}

.metric-card-delta {
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.metric-delta-positive {
    color: var(--accent-green);
}

.metric-delta-negative {
    color: var(--accent-red);
}

.metric-delta-neutral {
    color: var(--text-secondary);
}

/* ==========================================================================
   PROGRESS BAR
   ========================================================================== */

.progress-container {
    background-color: var(--bg-primary);
    border-radius: 9999px;
    height: 8px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    border-radius: 9999px;
    transition: width 0.3s ease;
}

.progress-high {
    background-color: var(--accent-green);
}

.progress-medium {
    background-color: var(--accent-yellow);
}

.progress-low {
    background-color: var(--accent-red);
}

/* ==========================================================================
   STREAMLIT OVERRIDES
   ========================================================================== */

/* Buttons */
.stButton > button {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    transition: all 0.2s ease;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: var(--bg-hover);
    border-color: var(--accent-blue);
    color: var(--accent-blue);
}

.stButton > button[kind="primary"] {
    background-color: var(--accent-blue);
    color: white;
    border: none;
}

.stButton > button[kind="primary"]:hover {
    background-color: #2563EB;
}

/* Text inputs */
.stTextInput > div > div > input {
    background-color: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    color: var(--text-primary);
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

/* Select boxes */
.stSelectbox > div > div {
    background-color: var(--bg-card);
    border-color: var(--border-default);
    border-radius: 8px;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    color: var(--text-primary);
}

.streamlit-expanderContent {
    background-color: var(--bg-card);
    border: 1px solid var(--border-default);
    border-top: none;
    border-radius: 0 0 8px 8px;
}

/* Dividers */
hr {
    border-color: var(--border-muted);
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* ==========================================================================
   BACK BUTTON
   ========================================================================== */

.back-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    padding: 0.5rem 0;
    transition: color 0.2s ease;
}

.back-button:hover {
    color: var(--accent-blue);
}

/* ==========================================================================
   ALERTS
   ========================================================================== */

.alert-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.alert-critical {
    background-color: rgba(239, 68, 68, 0.1);
    color: var(--accent-red);
}

.alert-high {
    background-color: rgba(249, 115, 22, 0.1);
    color: #F97316;
}

.alert-medium {
    background-color: rgba(245, 158, 11, 0.1);
    color: var(--accent-yellow);
}

.alert-low {
    background-color: rgba(16, 185, 129, 0.1);
    color: var(--accent-green);
}

/* ==========================================================================
   INFO BOXES
   ========================================================================== */

.info-box {
    background-color: rgba(59, 130, 246, 0.05);
    border-left: 4px solid var(--accent-blue);
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
}

.warning-box {
    background-color: rgba(245, 158, 11, 0.05);
    border-left: 4px solid var(--accent-yellow);
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
}

.success-box {
    background-color: rgba(16, 185, 129, 0.05);
    border-left: 4px solid var(--accent-green);
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
}

</style>
"""


def apply_theme():
    """Apply the light theme CSS to the Streamlit app."""
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


# Alias for backward compatibility
def apply_dark_theme():
    """Apply theme (now redirects to light theme)."""
    apply_theme()

