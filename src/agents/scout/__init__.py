"""IntelligenceScout Agent Module.

Provides autonomous sourcing capabilities for identifying
potential acquisition targets from market signals.
"""

from .agent import IntelligenceScoutAgent
from .scorer import DealScorer, ScoredDeal
from .sources import (
    JobAnalyzer,
    JobSignal,
    MacroAnalyzer,
    MacroContext,
    MacroIndicator,
    NewsAnalyzer,
    NewsSignal,
    SignalStrength,
    SignalType,
)

__all__ = [
    # Agent
    "IntelligenceScoutAgent",
    # Scorer
    "DealScorer",
    "ScoredDeal",
    # Sources
    "NewsAnalyzer",
    "JobAnalyzer",
    "MacroAnalyzer",
    # Data models
    "NewsSignal",
    "JobSignal",
    "MacroContext",
    "MacroIndicator",
    "SignalType",
    "SignalStrength",
]
