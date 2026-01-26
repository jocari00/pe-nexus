"""Mock data for ValueCreationMonitor agent.

Contains sample portfolio companies with historical financials, budgets, and KPIs
for demonstration and testing purposes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class PortfolioStatus(str, Enum):
    """Portfolio company performance status."""
    ON_TRACK = "on_track"
    WATCH = "watch"
    AT_RISK = "at_risk"
    OUTPERFORMING = "outperforming"


class KPICategory(str, Enum):
    """Categories for KPIs."""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    GROWTH = "growth"
    EFFICIENCY = "efficiency"
    CUSTOMER = "customer"


@dataclass
class MonthlyFinancials:
    """Monthly financial data point."""
    month: str  # YYYY-MM format
    revenue: Decimal
    ebitda: Decimal
    net_income: Decimal
    cash_balance: Decimal
    debt_balance: Decimal
    capex: Decimal = Decimal("0")
    working_capital: Decimal = Decimal("0")


@dataclass
class BudgetData:
    """Budget/plan numbers for comparison."""
    month: str  # YYYY-MM format
    revenue: Decimal
    ebitda: Decimal
    net_income: Decimal
    headcount: int
    capex: Decimal = Decimal("0")


@dataclass
class OperationalKPI:
    """Operational KPI data point."""
    name: str
    category: KPICategory
    current_value: float
    target_value: float
    unit: str
    period: str  # YYYY-MM or YYYY-Q#
    trend: str = "stable"  # up, down, stable


@dataclass
class PortfolioCompany:
    """Complete portfolio company data structure."""
    company_id: str
    name: str
    industry: str
    sub_sector: str
    acquisition_date: str  # YYYY-MM-DD
    entry_ev: Decimal
    entry_ebitda: Decimal
    entry_multiple: float
    ownership_pct: float
    board_seats: int
    deal_lead: str

    # Current state
    status: PortfolioStatus
    status_reason: str

    # Historical data
    monthly_actuals: list[MonthlyFinancials] = field(default_factory=list)
    monthly_budget: list[BudgetData] = field(default_factory=list)
    operational_kpis: list[OperationalKPI] = field(default_factory=list)

    # Value creation initiatives
    initiatives: list[dict] = field(default_factory=list)

    # Exit planning
    exit_strategy: str = ""
    target_exit_year: int = 0
    target_exit_multiple: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        latest_financials = self._get_latest_financials()

        return {
            "id": self.company_id,  # Use 'id' for consistency with synthesis API
            "company_id": self.company_id,
            "name": self.name,
            "industry": self.industry,
            "sector": self.sub_sector,  # Add sector alias
            "sub_sector": self.sub_sector,
            "acquisition_date": self.acquisition_date,
            "entry_ev": float(self.entry_ev),
            "entry_ebitda": float(self.entry_ebitda),
            "entry_multiple": self.entry_multiple,
            "ownership_pct": self.ownership_pct,
            "board_seats": self.board_seats,
            "deal_lead": self.deal_lead,
            "status": self.status.value,
            "status_reason": self.status_reason,
            "exit_strategy": self.exit_strategy,
            "target_exit_year": self.target_exit_year,
            "target_exit_multiple": self.target_exit_multiple,
            "months_held": self._calculate_months_held(),
            # Flatten latest financials to top level for easier access
            "revenue": latest_financials.get("revenue", 0),
            "ebitda": latest_financials.get("ebitda", 0),
            "margin": (latest_financials.get("ebitda", 0) / latest_financials.get("revenue", 1) * 100) if latest_financials.get("revenue", 0) > 0 else 0,
            "cash": latest_financials.get("cash_balance", 0),
            "debt": latest_financials.get("debt_balance", 0),
            # Keep nested for detailed view
            "latest_financials": latest_financials,
            "latest_kpis_summary": self._get_kpi_summary(),
            # Add computed fields for synthesis API
            "revenue_growth": 0.05,  # Placeholder - could calculate from historical data
            "budget_variance": 0.02,  # Placeholder - could calculate from actuals vs budget
            "current_valuation": float(self.entry_ev) * 1.2,  # Placeholder estimate
            "invested_capital": float(self.entry_ev) * self.ownership_pct / 100,
            "irr": 20.0 if self.status == PortfolioStatus.OUTPERFORMING else 15.0 if self.status == PortfolioStatus.ON_TRACK else 5.0,
            "moic": 1.5 if self.status == PortfolioStatus.OUTPERFORMING else 1.2 if self.status == PortfolioStatus.ON_TRACK else 0.95,
            "vcp_progress": 0.65 if self.status == PortfolioStatus.OUTPERFORMING else 0.50,
            "description": f"{self.name} - {self.sub_sector} company",
        }

    def _calculate_months_held(self) -> int:
        """Calculate months since acquisition."""
        acq_date = datetime.strptime(self.acquisition_date, "%Y-%m-%d")
        now = datetime(2025, 12, 31)  # Mock current date
        delta = now - acq_date
        return delta.days // 30

    def _get_latest_financials(self) -> dict:
        """Get most recent financials."""
        if not self.monthly_actuals:
            return {}
        latest = self.monthly_actuals[-1]
        return {
            "month": latest.month,
            "revenue": float(latest.revenue),
            "ebitda": float(latest.ebitda),
            "net_income": float(latest.net_income),
            "cash_balance": float(latest.cash_balance),
            "debt_balance": float(latest.debt_balance),
        }

    def _get_kpi_summary(self) -> dict:
        """Get summary of latest KPIs."""
        if not self.operational_kpis:
            return {"count": 0, "on_target": 0, "below_target": 0}

        on_target = sum(
            1 for k in self.operational_kpis
            if k.current_value >= k.target_value * 0.95
        )
        return {
            "count": len(self.operational_kpis),
            "on_target": on_target,
            "below_target": len(self.operational_kpis) - on_target,
        }


# =============================================================================
# Sample Portfolio Companies
# =============================================================================

def _create_techflow_solutions() -> PortfolioCompany:
    """TechFlow Solutions - B2B SaaS company, performing well."""
    monthly_actuals = [
        MonthlyFinancials("2025-07", Decimal("4.2"), Decimal("0.84"), Decimal("0.42"), Decimal("8.5"), Decimal("15.0")),
        MonthlyFinancials("2025-08", Decimal("4.4"), Decimal("0.88"), Decimal("0.44"), Decimal("8.9"), Decimal("14.8")),
        MonthlyFinancials("2025-09", Decimal("4.5"), Decimal("0.90"), Decimal("0.45"), Decimal("9.2"), Decimal("14.6")),
        MonthlyFinancials("2025-10", Decimal("4.7"), Decimal("0.94"), Decimal("0.47"), Decimal("9.6"), Decimal("14.4")),
        MonthlyFinancials("2025-11", Decimal("4.9"), Decimal("0.98"), Decimal("0.49"), Decimal("10.0"), Decimal("14.2")),
        MonthlyFinancials("2025-12", Decimal("5.1"), Decimal("1.02"), Decimal("0.51"), Decimal("10.5"), Decimal("14.0")),
    ]

    monthly_budget = [
        BudgetData("2025-07", Decimal("4.0"), Decimal("0.80"), Decimal("0.40"), 85),
        BudgetData("2025-08", Decimal("4.2"), Decimal("0.84"), Decimal("0.42"), 88),
        BudgetData("2025-09", Decimal("4.4"), Decimal("0.88"), Decimal("0.44"), 90),
        BudgetData("2025-10", Decimal("4.6"), Decimal("0.92"), Decimal("0.46"), 92),
        BudgetData("2025-11", Decimal("4.8"), Decimal("0.96"), Decimal("0.48"), 95),
        BudgetData("2025-12", Decimal("5.0"), Decimal("1.00"), Decimal("0.50"), 97),
    ]

    kpis = [
        OperationalKPI("ARR Growth Rate", KPICategory.GROWTH, 28.5, 25.0, "%", "2025-Q4", "up"),
        OperationalKPI("Net Revenue Retention", KPICategory.CUSTOMER, 118.0, 115.0, "%", "2025-Q4", "up"),
        OperationalKPI("CAC Payback Period", KPICategory.EFFICIENCY, 14.0, 18.0, "months", "2025-Q4", "down"),
        OperationalKPI("Gross Margin", KPICategory.FINANCIAL, 78.5, 75.0, "%", "2025-Q4", "stable"),
        OperationalKPI("Employee Headcount", KPICategory.OPERATIONAL, 102, 97, "FTEs", "2025-Q4", "up"),
        OperationalKPI("Customer Churn Rate", KPICategory.CUSTOMER, 1.8, 2.5, "%", "2025-Q4", "down"),
    ]

    initiatives = [
        {"name": "Enterprise Sales Expansion", "status": "on_track", "impact": "High", "completion": 75},
        {"name": "AI Feature Integration", "status": "on_track", "impact": "Medium", "completion": 60},
        {"name": "APAC Market Entry", "status": "planning", "impact": "High", "completion": 15},
    ]

    return PortfolioCompany(
        company_id="pc-001",
        name="TechFlow Solutions",
        industry="Technology",
        sub_sector="B2B SaaS",
        acquisition_date="2023-03-15",
        entry_ev=Decimal("80.0"),
        entry_ebitda=Decimal("8.0"),
        entry_multiple=10.0,
        ownership_pct=75.0,
        board_seats=2,
        deal_lead="Sarah Chen",
        status=PortfolioStatus.OUTPERFORMING,
        status_reason="Exceeding revenue plan by 8%, strong NRR and expanding margins",
        monthly_actuals=monthly_actuals,
        monthly_budget=monthly_budget,
        operational_kpis=kpis,
        initiatives=initiatives,
        exit_strategy="Strategic sale to enterprise software company",
        target_exit_year=2026,
        target_exit_multiple=12.0,
    )


def _create_midwest_manufacturing() -> PortfolioCompany:
    """Midwest Manufacturing - Industrial company, on watch list."""
    monthly_actuals = [
        MonthlyFinancials("2025-07", Decimal("12.5"), Decimal("1.88"), Decimal("0.75"), Decimal("4.2"), Decimal("28.0")),
        MonthlyFinancials("2025-08", Decimal("12.3"), Decimal("1.72"), Decimal("0.62"), Decimal("3.8"), Decimal("27.8")),
        MonthlyFinancials("2025-09", Decimal("11.8"), Decimal("1.53"), Decimal("0.47"), Decimal("3.4"), Decimal("27.6")),
        MonthlyFinancials("2025-10", Decimal("11.5"), Decimal("1.38"), Decimal("0.35"), Decimal("3.1"), Decimal("27.4")),
        MonthlyFinancials("2025-11", Decimal("11.2"), Decimal("1.23"), Decimal("0.22"), Decimal("2.7"), Decimal("27.2")),
        MonthlyFinancials("2025-12", Decimal("11.0"), Decimal("1.10"), Decimal("0.11"), Decimal("2.5"), Decimal("27.0")),
    ]

    monthly_budget = [
        BudgetData("2025-07", Decimal("13.0"), Decimal("2.08"), Decimal("0.91"), 245),
        BudgetData("2025-08", Decimal("13.2"), Decimal("2.11"), Decimal("0.92"), 248),
        BudgetData("2025-09", Decimal("13.5"), Decimal("2.16"), Decimal("0.95"), 250),
        BudgetData("2025-10", Decimal("13.8"), Decimal("2.21"), Decimal("0.97"), 252),
        BudgetData("2025-11", Decimal("14.0"), Decimal("2.24"), Decimal("0.98"), 255),
        BudgetData("2025-12", Decimal("14.2"), Decimal("2.27"), Decimal("1.00"), 258),
    ]

    kpis = [
        OperationalKPI("EBITDA Margin", KPICategory.FINANCIAL, 10.0, 16.0, "%", "2025-Q4", "down"),
        OperationalKPI("Capacity Utilization", KPICategory.OPERATIONAL, 68.0, 80.0, "%", "2025-Q4", "down"),
        OperationalKPI("On-Time Delivery", KPICategory.CUSTOMER, 82.0, 95.0, "%", "2025-Q4", "down"),
        OperationalKPI("Inventory Turns", KPICategory.EFFICIENCY, 4.2, 6.0, "x", "2025-Q4", "down"),
        OperationalKPI("Employee Headcount", KPICategory.OPERATIONAL, 238, 258, "FTEs", "2025-Q4", "down"),
        OperationalKPI("Scrap Rate", KPICategory.EFFICIENCY, 4.5, 2.5, "%", "2025-Q4", "up"),
    ]

    initiatives = [
        {"name": "Lean Manufacturing Program", "status": "delayed", "impact": "High", "completion": 35},
        {"name": "Supply Chain Optimization", "status": "at_risk", "impact": "High", "completion": 20},
        {"name": "New Product Line Launch", "status": "on_track", "impact": "Medium", "completion": 55},
    ]

    return PortfolioCompany(
        company_id="pc-002",
        name="Midwest Manufacturing Co.",
        industry="Industrials",
        sub_sector="Precision Manufacturing",
        acquisition_date="2022-08-20",
        entry_ev=Decimal("120.0"),
        entry_ebitda=Decimal("20.0"),
        entry_multiple=6.0,
        ownership_pct=85.0,
        board_seats=3,
        deal_lead="Michael Roberts",
        status=PortfolioStatus.AT_RISK,
        status_reason="Revenue 23% below plan, margin compression from input costs, operational issues",
        monthly_actuals=monthly_actuals,
        monthly_budget=monthly_budget,
        operational_kpis=kpis,
        initiatives=initiatives,
        exit_strategy="Sale to strategic acquirer or larger PE platform",
        target_exit_year=2027,
        target_exit_multiple=7.0,
    )


def _create_healthbridge_services() -> PortfolioCompany:
    """HealthBridge Services - Healthcare services, performing on track."""
    monthly_actuals = [
        MonthlyFinancials("2025-07", Decimal("8.2"), Decimal("1.48"), Decimal("0.74"), Decimal("6.5"), Decimal("18.0")),
        MonthlyFinancials("2025-08", Decimal("8.4"), Decimal("1.51"), Decimal("0.76"), Decimal("6.8"), Decimal("17.8")),
        MonthlyFinancials("2025-09", Decimal("8.5"), Decimal("1.53"), Decimal("0.77"), Decimal("7.0"), Decimal("17.6")),
        MonthlyFinancials("2025-10", Decimal("8.6"), Decimal("1.55"), Decimal("0.77"), Decimal("7.2"), Decimal("17.4")),
        MonthlyFinancials("2025-11", Decimal("8.8"), Decimal("1.58"), Decimal("0.79"), Decimal("7.5"), Decimal("17.2")),
        MonthlyFinancials("2025-12", Decimal("9.0"), Decimal("1.62"), Decimal("0.81"), Decimal("7.8"), Decimal("17.0")),
    ]

    monthly_budget = [
        BudgetData("2025-07", Decimal("8.0"), Decimal("1.44"), Decimal("0.72"), 156),
        BudgetData("2025-08", Decimal("8.2"), Decimal("1.48"), Decimal("0.74"), 158),
        BudgetData("2025-09", Decimal("8.4"), Decimal("1.51"), Decimal("0.76"), 160),
        BudgetData("2025-10", Decimal("8.6"), Decimal("1.55"), Decimal("0.77"), 162),
        BudgetData("2025-11", Decimal("8.8"), Decimal("1.58"), Decimal("0.79"), 164),
        BudgetData("2025-12", Decimal("9.0"), Decimal("1.62"), Decimal("0.81"), 166),
    ]

    kpis = [
        OperationalKPI("Revenue per Patient", KPICategory.FINANCIAL, 285.0, 280.0, "$", "2025-Q4", "up"),
        OperationalKPI("Patient Satisfaction", KPICategory.CUSTOMER, 4.6, 4.5, "score", "2025-Q4", "stable"),
        OperationalKPI("Staff Utilization", KPICategory.EFFICIENCY, 78.0, 80.0, "%", "2025-Q4", "stable"),
        OperationalKPI("Claims Denial Rate", KPICategory.OPERATIONAL, 3.2, 4.0, "%", "2025-Q4", "down"),
        OperationalKPI("Employee Headcount", KPICategory.OPERATIONAL, 165, 166, "FTEs", "2025-Q4", "stable"),
        OperationalKPI("Same-Store Growth", KPICategory.GROWTH, 6.5, 6.0, "%", "2025-Q4", "up"),
    ]

    initiatives = [
        {"name": "New Clinic Expansion (3 sites)", "status": "on_track", "impact": "High", "completion": 70},
        {"name": "Revenue Cycle Management System", "status": "on_track", "impact": "Medium", "completion": 90},
        {"name": "Telehealth Platform Launch", "status": "completed", "impact": "Medium", "completion": 100},
    ]

    return PortfolioCompany(
        company_id="pc-003",
        name="HealthBridge Services",
        industry="Healthcare",
        sub_sector="Outpatient Services",
        acquisition_date="2023-11-01",
        entry_ev=Decimal("90.0"),
        entry_ebitda=Decimal("15.0"),
        entry_multiple=6.0,
        ownership_pct=70.0,
        board_seats=2,
        deal_lead="Jennifer Walsh",
        status=PortfolioStatus.ON_TRACK,
        status_reason="Meeting budget targets, clinic expansion proceeding on schedule",
        monthly_actuals=monthly_actuals,
        monthly_budget=monthly_budget,
        operational_kpis=kpis,
        initiatives=initiatives,
        exit_strategy="Strategic sale to healthcare system or PE rollup",
        target_exit_year=2028,
        target_exit_multiple=8.0,
    )


def _create_greenleaf_brands() -> PortfolioCompany:
    """GreenLeaf Brands - Consumer products company, on watch."""
    monthly_actuals = [
        MonthlyFinancials("2025-07", Decimal("6.8"), Decimal("0.95"), Decimal("0.41"), Decimal("3.2"), Decimal("12.0")),
        MonthlyFinancials("2025-08", Decimal("6.5"), Decimal("0.85"), Decimal("0.33"), Decimal("2.9"), Decimal("12.2")),
        MonthlyFinancials("2025-09", Decimal("6.7"), Decimal("0.90"), Decimal("0.36"), Decimal("2.7"), Decimal("12.4")),
        MonthlyFinancials("2025-10", Decimal("7.2"), Decimal("1.01"), Decimal("0.43"), Decimal("2.9"), Decimal("12.2")),
        MonthlyFinancials("2025-11", Decimal("7.8"), Decimal("1.17"), Decimal("0.55"), Decimal("3.4"), Decimal("12.0")),
        MonthlyFinancials("2025-12", Decimal("8.5"), Decimal("1.36"), Decimal("0.68"), Decimal("4.0"), Decimal("11.8")),
    ]

    monthly_budget = [
        BudgetData("2025-07", Decimal("7.0"), Decimal("1.05"), Decimal("0.49"), 78),
        BudgetData("2025-08", Decimal("7.0"), Decimal("1.05"), Decimal("0.49"), 78),
        BudgetData("2025-09", Decimal("7.2"), Decimal("1.08"), Decimal("0.50"), 80),
        BudgetData("2025-10", Decimal("7.5"), Decimal("1.13"), Decimal("0.53"), 82),
        BudgetData("2025-11", Decimal("8.0"), Decimal("1.20"), Decimal("0.56"), 84),
        BudgetData("2025-12", Decimal("9.0"), Decimal("1.35"), Decimal("0.63"), 86),
    ]

    kpis = [
        OperationalKPI("Gross Margin", KPICategory.FINANCIAL, 42.0, 45.0, "%", "2025-Q4", "down"),
        OperationalKPI("Distribution Points", KPICategory.GROWTH, 12500, 15000, "stores", "2025-Q4", "up"),
        OperationalKPI("Inventory Days", KPICategory.EFFICIENCY, 95, 75, "days", "2025-Q4", "up"),
        OperationalKPI("Brand Awareness", KPICategory.CUSTOMER, 28.0, 35.0, "%", "2025-Q4", "up"),
        OperationalKPI("eCommerce % of Sales", KPICategory.GROWTH, 32.0, 40.0, "%", "2025-Q4", "up"),
        OperationalKPI("Customer Repeat Rate", KPICategory.CUSTOMER, 38.0, 45.0, "%", "2025-Q4", "stable"),
    ]

    initiatives = [
        {"name": "D2C eCommerce Relaunch", "status": "on_track", "impact": "High", "completion": 85},
        {"name": "Retailer Margin Restructuring", "status": "at_risk", "impact": "High", "completion": 30},
        {"name": "New Product SKU Launch", "status": "delayed", "impact": "Medium", "completion": 45},
    ]

    return PortfolioCompany(
        company_id="pc-004",
        name="GreenLeaf Brands",
        industry="Consumer",
        sub_sector="Natural Products",
        acquisition_date="2024-02-01",
        entry_ev=Decimal("65.0"),
        entry_ebitda=Decimal("10.0"),
        entry_multiple=6.5,
        ownership_pct=80.0,
        board_seats=2,
        deal_lead="David Park",
        status=PortfolioStatus.WATCH,
        status_reason="Q4 recovery underway but full-year behind plan, margin pressure from input costs",
        monthly_actuals=monthly_actuals,
        monthly_budget=monthly_budget,
        operational_kpis=kpis,
        initiatives=initiatives,
        exit_strategy="Strategic sale to CPG major or financial sponsor",
        target_exit_year=2028,
        target_exit_multiple=8.0,
    )


def _create_cyberguard_systems() -> PortfolioCompany:
    """CyberGuard Systems - Cybersecurity company, new acquisition."""
    monthly_actuals = [
        MonthlyFinancials("2025-10", Decimal("3.2"), Decimal("0.48"), Decimal("0.19"), Decimal("12.0"), Decimal("8.0")),
        MonthlyFinancials("2025-11", Decimal("3.4"), Decimal("0.54"), Decimal("0.24"), Decimal("11.8"), Decimal("7.8")),
        MonthlyFinancials("2025-12", Decimal("3.6"), Decimal("0.61"), Decimal("0.29"), Decimal("11.6"), Decimal("7.6")),
    ]

    monthly_budget = [
        BudgetData("2025-10", Decimal("3.0"), Decimal("0.45"), Decimal("0.18"), 62),
        BudgetData("2025-11", Decimal("3.2"), Decimal("0.48"), Decimal("0.19"), 65),
        BudgetData("2025-12", Decimal("3.4"), Decimal("0.51"), Decimal("0.20"), 68),
    ]

    kpis = [
        OperationalKPI("ARR", KPICategory.FINANCIAL, 42.0, 40.0, "$M", "2025-Q4", "up"),
        OperationalKPI("ARR Growth Rate", KPICategory.GROWTH, 45.0, 40.0, "%", "2025-Q4", "up"),
        OperationalKPI("Net Dollar Retention", KPICategory.CUSTOMER, 125.0, 120.0, "%", "2025-Q4", "up"),
        OperationalKPI("Sales Efficiency", KPICategory.EFFICIENCY, 0.85, 0.80, "ratio", "2025-Q4", "up"),
        OperationalKPI("Employee Headcount", KPICategory.OPERATIONAL, 70, 68, "FTEs", "2025-Q4", "up"),
        OperationalKPI("Enterprise Logo Adds", KPICategory.GROWTH, 12, 10, "logos", "2025-Q4", "up"),
    ]

    initiatives = [
        {"name": "100-Day Integration Plan", "status": "on_track", "impact": "High", "completion": 85},
        {"name": "Sales Team Expansion", "status": "on_track", "impact": "High", "completion": 40},
        {"name": "Product Roadmap Acceleration", "status": "on_track", "impact": "Medium", "completion": 25},
    ]

    return PortfolioCompany(
        company_id="pc-005",
        name="CyberGuard Systems",
        industry="Technology",
        sub_sector="Cybersecurity",
        acquisition_date="2025-09-01",
        entry_ev=Decimal("100.0"),
        entry_ebitda=Decimal("5.0"),
        entry_multiple=20.0,
        ownership_pct=90.0,
        board_seats=3,
        deal_lead="Sarah Chen",
        status=PortfolioStatus.OUTPERFORMING,
        status_reason="Exceeding 100-day plan targets, strong pipeline and customer expansion",
        monthly_actuals=monthly_actuals,
        monthly_budget=monthly_budget,
        operational_kpis=kpis,
        initiatives=initiatives,
        exit_strategy="Strategic sale or growth equity recap",
        target_exit_year=2029,
        target_exit_multiple=25.0,
    )


# =============================================================================
# Portfolio Data Access Functions
# =============================================================================

# Global portfolio companies list
PORTFOLIO_COMPANIES: list[PortfolioCompany] = [
    _create_techflow_solutions(),
    _create_midwest_manufacturing(),
    _create_healthbridge_services(),
    _create_greenleaf_brands(),
    _create_cyberguard_systems(),
]


def get_all_companies() -> list[PortfolioCompany]:
    """Get all portfolio companies."""
    return PORTFOLIO_COMPANIES


def get_company_by_id(company_id: str) -> Optional[PortfolioCompany]:
    """Get a specific portfolio company by ID."""
    for company in PORTFOLIO_COMPANIES:
        if company.company_id == company_id:
            return company
    return None


def get_companies_by_status(status: PortfolioStatus) -> list[PortfolioCompany]:
    """Get portfolio companies filtered by status."""
    return [c for c in PORTFOLIO_COMPANIES if c.status == status]


def get_companies_by_industry(industry: str) -> list[PortfolioCompany]:
    """Get portfolio companies filtered by industry."""
    return [c for c in PORTFOLIO_COMPANIES if c.industry.lower() == industry.lower()]


def get_portfolio_summary() -> dict:
    """Get high-level portfolio summary statistics."""
    total_invested = sum(float(c.entry_ev) * c.ownership_pct / 100 for c in PORTFOLIO_COMPANIES)

    status_counts = {
        "outperforming": len(get_companies_by_status(PortfolioStatus.OUTPERFORMING)),
        "on_track": len(get_companies_by_status(PortfolioStatus.ON_TRACK)),
        "watch": len(get_companies_by_status(PortfolioStatus.WATCH)),
        "at_risk": len(get_companies_by_status(PortfolioStatus.AT_RISK)),
    }

    return {
        "total_companies": len(PORTFOLIO_COMPANIES),
        "total_invested_capital": total_invested,
        "status_breakdown": status_counts,
        "industries": list(set(c.industry for c in PORTFOLIO_COMPANIES)),
        "average_holding_period_months": sum(c._calculate_months_held() for c in PORTFOLIO_COMPANIES) // len(PORTFOLIO_COMPANIES),
    }
