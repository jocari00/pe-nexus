"""AdversarialIC Agent Module - Investment committee debate with Bull/Bear perspectives."""

from .agent import AdversarialICAgent, create_ic_agent
from .bull_agent import BullAgent
from .bear_agent import BearAgent

__all__ = [
    "AdversarialICAgent",
    "create_ic_agent",
    "BullAgent",
    "BearAgent",
]
