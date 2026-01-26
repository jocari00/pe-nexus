"""Formatting utilities for the PE-Nexus frontend."""

from typing import Union


def format_currency(value: Union[float, int, None], decimals: int = 1) -> str:
    """Format a number as currency (millions)."""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        try:
            value = float(value.replace("$", "").replace("M", "").replace(",", ""))
        except ValueError:
            return value
    return f"${value:,.{decimals}f}M"


def format_percentage(value: Union[float, int, None], decimals: int = 1) -> str:
    """Format a number as percentage."""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        if "%" in value:
            return value
        try:
            value = float(value)
        except ValueError:
            return value
    # If value is already in percentage form (> 1), don't multiply
    if abs(value) > 1:
        return f"{value:,.{decimals}f}%"
    return f"{value * 100:,.{decimals}f}%"


def format_number(value: Union[float, int, None], decimals: int = 1) -> str:
    """Format a number with commas."""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return value
    return f"{value:,.{decimals}f}"


def format_multiple(value: Union[float, int, None], decimals: int = 1) -> str:
    """Format a number as a multiple (e.g., 8.0x)."""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        if "x" in value.lower():
            return value
        try:
            value = float(value)
        except ValueError:
            return value
    return f"{value:,.{decimals}f}x"


def format_score(value: Union[float, int, None], max_score: float = 10.0) -> str:
    """Format a score (e.g., 7.5/10)."""
    if value is None:
        return "N/A"
    return f"{value:.1f}/{max_score:.0f}"


def get_status_color(status: str, dark_mode: bool = True) -> str:
    """Get color for status indicators.

    Args:
        status: Status string
        dark_mode: If True, returns dark theme colors
    """
    if dark_mode:
        # Dark theme colors (Bloomberg-inspired)
        status_colors = {
            "on_track": "#3FB950",      # Green
            "outperforming": "#58A6FF", # Blue
            "watch": "#D29922",         # Yellow
            "at_risk": "#F85149",       # Red
            "critical": "#F85149",      # Red
            "high": "#DB6D28",          # Orange
            "medium": "#D29922",        # Yellow
            "low": "#3FB950",           # Green
        }
    else:
        # Light theme colors (legacy)
        status_colors = {
            "on_track": "#28A745",
            "outperforming": "#17A2B8",
            "watch": "#FFC107",
            "at_risk": "#DC3545",
            "critical": "#DC3545",
            "high": "#FD7E14",
            "medium": "#FFC107",
            "low": "#28A745",
        }
    return status_colors.get(status.lower(), "#8B949E")


def get_status_emoji(status: str) -> str:
    """Get emoji for status indicators."""
    status_emojis = {
        "on_track": "OK",
        "outperforming": "STAR",
        "watch": "!",
        "at_risk": "X",
        "critical": "!!",
        "high": "!",
        "medium": "~",
        "low": "OK",
    }
    return status_emojis.get(status.lower(), "?")


def format_risk_level(level: str, dark_mode: bool = True) -> tuple[str, str]:
    """Get formatted risk level with color.

    Args:
        level: Risk level string
        dark_mode: If True, returns dark theme colors

    Returns:
        Tuple of (color, formatted_label)
    """
    level_lower = level.lower()
    if dark_mode:
        colors = {
            "critical": ("#F85149", "CRITICAL"),
            "high": ("#DB6D28", "HIGH"),
            "medium": ("#D29922", "MEDIUM"),
            "low": ("#3FB950", "LOW"),
        }
    else:
        colors = {
            "critical": ("#DC3545", "CRITICAL"),
            "high": ("#FD7E14", "HIGH"),
            "medium": ("#FFC107", "MEDIUM"),
            "low": ("#28A745", "LOW"),
        }
    return colors.get(level_lower, ("#8B949E", level.upper()))


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
