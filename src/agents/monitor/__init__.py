"""ValueCreationMonitor Agent package.

Provides portfolio company monitoring, KPI tracking, and LP report generation.
"""

from .agent import ValueCreationMonitorAgent, create_vcm
from .kpi_tracker import (
    AlertSeverity,
    KPIAlert,
    KPIAnalysisResult,
    KPITracker,
    TrendDirection,
    VarianceAnalysis,
    get_kpi_tracker,
)
from .lp_reporter import (
    CompanyUpdate,
    LPReport,
    LPReporter,
    PortfolioMetrics,
    get_lp_reporter,
)
from .mock_data import (
    BudgetData,
    KPICategory,
    MonthlyFinancials,
    OperationalKPI,
    PortfolioCompany,
    PortfolioStatus,
    get_all_companies,
    get_companies_by_industry,
    get_companies_by_status,
    get_company_by_id,
    get_portfolio_summary,
)

__all__ = [
    # Agent
    "ValueCreationMonitorAgent",
    "create_vcm",
    # KPI Tracker
    "KPITracker",
    "KPIAnalysisResult",
    "KPIAlert",
    "VarianceAnalysis",
    "AlertSeverity",
    "TrendDirection",
    "get_kpi_tracker",
    # LP Reporter
    "LPReporter",
    "LPReport",
    "CompanyUpdate",
    "PortfolioMetrics",
    "get_lp_reporter",
    # Mock Data
    "PortfolioCompany",
    "PortfolioStatus",
    "MonthlyFinancials",
    "BudgetData",
    "OperationalKPI",
    "KPICategory",
    "get_all_companies",
    "get_company_by_id",
    "get_companies_by_status",
    "get_companies_by_industry",
    "get_portfolio_summary",
]
