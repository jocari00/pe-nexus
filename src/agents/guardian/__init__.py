"""LegalGuardian Agent Module - Analyzes contracts for legal risks and red flags."""

from .agent import LegalGuardianAgent, create_guardian
from .mock_data import MOCK_CONTRACTS, ContractType, RiskLevel

__all__ = [
    "LegalGuardianAgent",
    "create_guardian",
    "MOCK_CONTRACTS",
    "ContractType",
    "RiskLevel",
]
