"""PE-Nexus Agent Framework."""

from .base import AgentOutput, AgentState, BaseAgent
from .navigator import (
    ConnectionPath,
    NetworkGraph,
    PathFinder,
    RelationshipNavigatorAgent,
    RelationshipType,
    create_navigator,
)
from .scout import (
    DealScorer,
    IntelligenceScoutAgent,
    JobSignal,
    MacroContext,
    NewsSignal,
    ScoredDeal,
    SignalStrength,
    SignalType,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentState",
    "AgentOutput",
    # Scout
    "IntelligenceScoutAgent",
    "DealScorer",
    "ScoredDeal",
    "NewsSignal",
    "JobSignal",
    "MacroContext",
    "SignalType",
    "SignalStrength",
    # Navigator
    "RelationshipNavigatorAgent",
    "create_navigator",
    "PathFinder",
    "ConnectionPath",
    "NetworkGraph",
    "RelationshipType",
]
