"""KPI Tracker for ValueCreationMonitor agent.

Provides KPI calculation, variance analysis, trend detection, and alert generation
for portfolio company monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from .mock_data import (
    BudgetData,
    KPICategory,
    MonthlyFinancials,
    OperationalKPI,
    PortfolioCompany,
    PortfolioStatus,
)


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TrendDirection(str, Enum):
    """Trend direction indicator."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class VarianceAnalysis:
    """Financial variance analysis result."""
    metric: str
    actual: float
    budget: float
    variance: float
    variance_pct: float
    favorable: bool
    explanation: str = ""


@dataclass
class KPIAlert:
    """Alert generated from KPI monitoring."""
    alert_id: str
    company_id: str
    company_name: str
    severity: AlertSeverity
    category: str
    metric: str
    message: str
    current_value: float
    threshold_value: float
    variance_pct: float
    recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "severity": self.severity.value,
            "category": self.category,
            "metric": self.metric,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "variance_pct": self.variance_pct,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


@dataclass
class KPIAnalysisResult:
    """Complete KPI analysis result for a company."""
    company_id: str
    company_name: str
    analysis_period: str
    status: PortfolioStatus
    status_change: Optional[str]  # e.g., "upgraded from watch" or "downgraded from on_track"

    # Financial analysis
    financial_variances: list[VarianceAnalysis]
    ytd_revenue: float
    ytd_revenue_vs_budget_pct: float
    ytd_ebitda: float
    ytd_ebitda_vs_budget_pct: float

    # KPI summary
    kpis_on_target: int
    kpis_below_target: int
    kpis_above_target: int
    key_strengths: list[str]
    key_concerns: list[str]

    # Alerts
    alerts: list[KPIAlert]
    critical_alerts: int
    high_alerts: int

    # Trends
    revenue_trend: TrendDirection
    margin_trend: TrendDirection
    cash_trend: TrendDirection

    # Value creation
    initiatives_on_track: int
    initiatives_at_risk: int

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "analysis_period": self.analysis_period,
            "status": self.status.value,
            "status_change": self.status_change,
            "financial_summary": {
                "ytd_revenue": self.ytd_revenue,
                "ytd_revenue_vs_budget_pct": self.ytd_revenue_vs_budget_pct,
                "ytd_ebitda": self.ytd_ebitda,
                "ytd_ebitda_vs_budget_pct": self.ytd_ebitda_vs_budget_pct,
            },
            "financial_variances": [
                {
                    "metric": v.metric,
                    "actual": v.actual,
                    "budget": v.budget,
                    "variance": v.variance,
                    "variance_pct": v.variance_pct,
                    "favorable": v.favorable,
                    "explanation": v.explanation,
                }
                for v in self.financial_variances
            ],
            "kpi_summary": {
                "on_target": self.kpis_on_target,
                "below_target": self.kpis_below_target,
                "above_target": self.kpis_above_target,
            },
            "key_strengths": self.key_strengths,
            "key_concerns": self.key_concerns,
            "alerts": [a.to_dict() for a in self.alerts],
            "alert_summary": {
                "critical": self.critical_alerts,
                "high": self.high_alerts,
                "total": len(self.alerts),
            },
            "trends": {
                "revenue": self.revenue_trend.value,
                "margin": self.margin_trend.value,
                "cash": self.cash_trend.value,
            },
            "initiatives": {
                "on_track": self.initiatives_on_track,
                "at_risk": self.initiatives_at_risk,
            },
        }


class KPITracker:
    """
    KPI calculation and tracking engine.

    Provides variance analysis, trend detection, and alert generation
    for portfolio company performance monitoring.
    """

    # Threshold configurations
    REVENUE_VARIANCE_CRITICAL = -0.20  # -20% vs budget
    REVENUE_VARIANCE_HIGH = -0.10  # -10% vs budget
    REVENUE_VARIANCE_MEDIUM = -0.05  # -5% vs budget

    MARGIN_VARIANCE_CRITICAL = -0.25  # -25% relative margin decline
    MARGIN_VARIANCE_HIGH = -0.15  # -15% relative margin decline

    CASH_RUNWAY_CRITICAL = 3  # months
    CASH_RUNWAY_HIGH = 6  # months

    def __init__(self):
        self._alert_counter = 0

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        return f"alert-{datetime.now().strftime('%Y%m%d')}-{self._alert_counter:04d}"

    def analyze_company(
        self,
        company: PortfolioCompany,
        period: str = "quarterly",
    ) -> KPIAnalysisResult:
        """
        Perform comprehensive KPI analysis for a portfolio company.

        Args:
            company: Portfolio company to analyze
            period: Analysis period (quarterly, annual, ytd)

        Returns:
            Complete KPI analysis result
        """
        # Calculate financial variances
        variances = self._calculate_financial_variances(company)

        # Calculate YTD metrics
        ytd_metrics = self._calculate_ytd_metrics(company)

        # Analyze operational KPIs
        kpi_analysis = self._analyze_operational_kpis(company)

        # Detect trends
        revenue_trend = self._detect_trend([float(m.revenue) for m in company.monthly_actuals])
        margin_trend = self._detect_margin_trend(company)
        cash_trend = self._detect_trend([float(m.cash_balance) for m in company.monthly_actuals])

        # Generate alerts
        alerts = self._generate_alerts(company, variances, kpi_analysis)

        # Analyze initiatives
        initiatives_on_track = sum(1 for i in company.initiatives if i.get("status") == "on_track")
        initiatives_at_risk = sum(1 for i in company.initiatives if i.get("status") in ["at_risk", "delayed"])

        # Identify strengths and concerns
        strengths, concerns = self._identify_strengths_concerns(company, variances, kpi_analysis)

        return KPIAnalysisResult(
            company_id=company.company_id,
            company_name=company.name,
            analysis_period=period,
            status=company.status,
            status_change=None,  # Would compare to previous period in real implementation
            financial_variances=variances,
            ytd_revenue=ytd_metrics["ytd_revenue"],
            ytd_revenue_vs_budget_pct=ytd_metrics["ytd_revenue_variance_pct"],
            ytd_ebitda=ytd_metrics["ytd_ebitda"],
            ytd_ebitda_vs_budget_pct=ytd_metrics["ytd_ebitda_variance_pct"],
            kpis_on_target=kpi_analysis["on_target"],
            kpis_below_target=kpi_analysis["below_target"],
            kpis_above_target=kpi_analysis["above_target"],
            key_strengths=strengths,
            key_concerns=concerns,
            alerts=alerts,
            critical_alerts=sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            high_alerts=sum(1 for a in alerts if a.severity == AlertSeverity.HIGH),
            revenue_trend=revenue_trend,
            margin_trend=margin_trend,
            cash_trend=cash_trend,
            initiatives_on_track=initiatives_on_track,
            initiatives_at_risk=initiatives_at_risk,
        )

    def _calculate_financial_variances(
        self,
        company: PortfolioCompany,
    ) -> list[VarianceAnalysis]:
        """Calculate variance between actuals and budget."""
        variances = []

        if not company.monthly_actuals or not company.monthly_budget:
            return variances

        # Get latest month for comparison
        latest_actual = company.monthly_actuals[-1]
        matching_budget = None

        for budget in company.monthly_budget:
            if budget.month == latest_actual.month:
                matching_budget = budget
                break

        if not matching_budget:
            # Use latest budget if no exact match
            matching_budget = company.monthly_budget[-1]

        # Revenue variance
        rev_actual = float(latest_actual.revenue)
        rev_budget = float(matching_budget.revenue)
        rev_variance = rev_actual - rev_budget
        rev_variance_pct = (rev_variance / rev_budget) * 100 if rev_budget else 0

        variances.append(VarianceAnalysis(
            metric="Revenue",
            actual=rev_actual,
            budget=rev_budget,
            variance=rev_variance,
            variance_pct=rev_variance_pct,
            favorable=rev_variance >= 0,
            explanation=self._explain_variance("Revenue", rev_variance_pct),
        ))

        # EBITDA variance
        ebitda_actual = float(latest_actual.ebitda)
        ebitda_budget = float(matching_budget.ebitda)
        ebitda_variance = ebitda_actual - ebitda_budget
        ebitda_variance_pct = (ebitda_variance / ebitda_budget) * 100 if ebitda_budget else 0

        variances.append(VarianceAnalysis(
            metric="EBITDA",
            actual=ebitda_actual,
            budget=ebitda_budget,
            variance=ebitda_variance,
            variance_pct=ebitda_variance_pct,
            favorable=ebitda_variance >= 0,
            explanation=self._explain_variance("EBITDA", ebitda_variance_pct),
        ))

        # Net Income variance
        ni_actual = float(latest_actual.net_income)
        ni_budget = float(matching_budget.net_income)
        ni_variance = ni_actual - ni_budget
        ni_variance_pct = (ni_variance / ni_budget) * 100 if ni_budget else 0

        variances.append(VarianceAnalysis(
            metric="Net Income",
            actual=ni_actual,
            budget=ni_budget,
            variance=ni_variance,
            variance_pct=ni_variance_pct,
            favorable=ni_variance >= 0,
            explanation=self._explain_variance("Net Income", ni_variance_pct),
        ))

        # EBITDA Margin variance
        actual_margin = (ebitda_actual / rev_actual) * 100 if rev_actual else 0
        budget_margin = (ebitda_budget / rev_budget) * 100 if rev_budget else 0
        margin_variance = actual_margin - budget_margin

        variances.append(VarianceAnalysis(
            metric="EBITDA Margin",
            actual=actual_margin,
            budget=budget_margin,
            variance=margin_variance,
            variance_pct=margin_variance,  # Already in percentage points
            favorable=margin_variance >= 0,
            explanation=self._explain_margin_variance(margin_variance),
        ))

        return variances

    def _calculate_ytd_metrics(self, company: PortfolioCompany) -> dict:
        """Calculate year-to-date metrics."""
        ytd_revenue = sum(float(m.revenue) for m in company.monthly_actuals)
        ytd_ebitda = sum(float(m.ebitda) for m in company.monthly_actuals)

        ytd_budget_revenue = sum(float(b.revenue) for b in company.monthly_budget)
        ytd_budget_ebitda = sum(float(b.ebitda) for b in company.monthly_budget)

        return {
            "ytd_revenue": ytd_revenue,
            "ytd_ebitda": ytd_ebitda,
            "ytd_revenue_variance_pct": ((ytd_revenue - ytd_budget_revenue) / ytd_budget_revenue * 100) if ytd_budget_revenue else 0,
            "ytd_ebitda_variance_pct": ((ytd_ebitda - ytd_budget_ebitda) / ytd_budget_ebitda * 100) if ytd_budget_ebitda else 0,
        }

    def _analyze_operational_kpis(self, company: PortfolioCompany) -> dict:
        """Analyze operational KPIs against targets."""
        on_target = 0
        below_target = 0
        above_target = 0

        for kpi in company.operational_kpis:
            # Determine if lower is better (e.g., churn rate, CAC payback)
            lower_is_better = kpi.name.lower() in [
                "cac payback period",
                "customer churn rate",
                "scrap rate",
                "inventory days",
                "claims denial rate",
            ]

            if lower_is_better:
                if kpi.current_value <= kpi.target_value:
                    above_target += 1
                elif kpi.current_value <= kpi.target_value * 1.10:  # Within 10%
                    on_target += 1
                else:
                    below_target += 1
            else:
                if kpi.current_value >= kpi.target_value:
                    above_target += 1
                elif kpi.current_value >= kpi.target_value * 0.90:  # Within 10%
                    on_target += 1
                else:
                    below_target += 1

        return {
            "on_target": on_target,
            "below_target": below_target,
            "above_target": above_target,
        }

    def _detect_trend(self, values: list[float]) -> TrendDirection:
        """Detect trend direction from a series of values."""
        if len(values) < 3:
            return TrendDirection.STABLE

        # Calculate month-over-month changes
        changes = []
        for i in range(1, len(values)):
            if values[i - 1] != 0:
                pct_change = (values[i] - values[i - 1]) / values[i - 1]
                changes.append(pct_change)

        if not changes:
            return TrendDirection.STABLE

        avg_change = sum(changes) / len(changes)
        volatility = max(changes) - min(changes) if len(changes) > 1 else 0

        # High volatility indicates volatile trend
        if volatility > 0.15:  # More than 15% swing
            return TrendDirection.VOLATILE

        # Consistent direction
        if avg_change > 0.02:  # Growing more than 2% on average
            return TrendDirection.IMPROVING
        elif avg_change < -0.02:  # Declining more than 2% on average
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    def _detect_margin_trend(self, company: PortfolioCompany) -> TrendDirection:
        """Detect EBITDA margin trend."""
        if len(company.monthly_actuals) < 3:
            return TrendDirection.STABLE

        margins = []
        for m in company.monthly_actuals:
            if float(m.revenue) > 0:
                margin = float(m.ebitda) / float(m.revenue)
                margins.append(margin)

        return self._detect_trend(margins)

    def _generate_alerts(
        self,
        company: PortfolioCompany,
        variances: list[VarianceAnalysis],
        kpi_analysis: dict,
    ) -> list[KPIAlert]:
        """Generate alerts based on analysis results."""
        alerts = []

        # Revenue variance alerts
        for v in variances:
            if v.metric == "Revenue" and not v.favorable:
                if v.variance_pct <= self.REVENUE_VARIANCE_CRITICAL * 100:
                    alerts.append(KPIAlert(
                        alert_id=self._generate_alert_id(),
                        company_id=company.company_id,
                        company_name=company.name,
                        severity=AlertSeverity.CRITICAL,
                        category="Financial",
                        metric="Revenue",
                        message=f"Revenue {v.variance_pct:.1f}% below budget - critical variance",
                        current_value=v.actual,
                        threshold_value=v.budget,
                        variance_pct=v.variance_pct,
                        recommendation="Immediate management review required. Identify root causes and develop recovery plan.",
                    ))
                elif v.variance_pct <= self.REVENUE_VARIANCE_HIGH * 100:
                    alerts.append(KPIAlert(
                        alert_id=self._generate_alert_id(),
                        company_id=company.company_id,
                        company_name=company.name,
                        severity=AlertSeverity.HIGH,
                        category="Financial",
                        metric="Revenue",
                        message=f"Revenue {v.variance_pct:.1f}% below budget",
                        current_value=v.actual,
                        threshold_value=v.budget,
                        variance_pct=v.variance_pct,
                        recommendation="Review sales pipeline and customer retention metrics. Update forecast.",
                    ))

            # EBITDA margin alerts
            if v.metric == "EBITDA Margin" and not v.favorable:
                if v.variance_pct <= -5:  # 5+ percentage points below
                    alerts.append(KPIAlert(
                        alert_id=self._generate_alert_id(),
                        company_id=company.company_id,
                        company_name=company.name,
                        severity=AlertSeverity.HIGH,
                        category="Financial",
                        metric="EBITDA Margin",
                        message=f"EBITDA margin {abs(v.variance_pct):.1f}pp below budget",
                        current_value=v.actual,
                        threshold_value=v.budget,
                        variance_pct=v.variance_pct,
                        recommendation="Analyze cost structure and pricing. Review for operational inefficiencies.",
                    ))

        # Cash position alerts
        if company.monthly_actuals:
            latest = company.monthly_actuals[-1]
            monthly_burn = 0

            if len(company.monthly_actuals) >= 3:
                # Calculate average monthly cash burn
                recent = company.monthly_actuals[-3:]
                cash_change = float(recent[-1].cash_balance) - float(recent[0].cash_balance)
                monthly_burn = -cash_change / 2 if cash_change < 0 else 0

            if monthly_burn > 0:
                runway_months = float(latest.cash_balance) / monthly_burn
                if runway_months < self.CASH_RUNWAY_CRITICAL:
                    alerts.append(KPIAlert(
                        alert_id=self._generate_alert_id(),
                        company_id=company.company_id,
                        company_name=company.name,
                        severity=AlertSeverity.CRITICAL,
                        category="Liquidity",
                        metric="Cash Runway",
                        message=f"Cash runway of {runway_months:.1f} months at current burn rate",
                        current_value=runway_months,
                        threshold_value=self.CASH_RUNWAY_CRITICAL,
                        variance_pct=0,
                        recommendation="Urgent: Evaluate financing options, cost reduction, or working capital optimization.",
                    ))

        # Operational KPI alerts
        for kpi in company.operational_kpis:
            lower_is_better = kpi.name.lower() in [
                "cac payback period", "customer churn rate", "scrap rate",
                "inventory days", "claims denial rate",
            ]

            if lower_is_better:
                variance_pct = ((kpi.current_value - kpi.target_value) / kpi.target_value * 100) if kpi.target_value else 0
                is_bad = kpi.current_value > kpi.target_value * 1.25  # 25% worse
            else:
                variance_pct = ((kpi.current_value - kpi.target_value) / kpi.target_value * 100) if kpi.target_value else 0
                is_bad = kpi.current_value < kpi.target_value * 0.75  # 25% worse

            if is_bad:
                alerts.append(KPIAlert(
                    alert_id=self._generate_alert_id(),
                    company_id=company.company_id,
                    company_name=company.name,
                    severity=AlertSeverity.MEDIUM,
                    category="Operational",
                    metric=kpi.name,
                    message=f"{kpi.name} significantly {'above' if lower_is_better else 'below'} target",
                    current_value=kpi.current_value,
                    threshold_value=kpi.target_value,
                    variance_pct=variance_pct,
                    recommendation=f"Review {kpi.category.value} operations and identify improvement actions.",
                ))

        # Initiative alerts
        for initiative in company.initiatives:
            if initiative.get("status") == "at_risk" and initiative.get("impact") == "High":
                alerts.append(KPIAlert(
                    alert_id=self._generate_alert_id(),
                    company_id=company.company_id,
                    company_name=company.name,
                    severity=AlertSeverity.HIGH,
                    category="Value Creation",
                    metric=f"Initiative: {initiative.get('name')}",
                    message=f"High-impact initiative '{initiative.get('name')}' is at risk",
                    current_value=initiative.get("completion", 0),
                    threshold_value=100,
                    variance_pct=initiative.get("completion", 0) - 100,
                    recommendation="Review initiative blockers and resource allocation. Consider escalation.",
                ))

        return alerts

    def _identify_strengths_concerns(
        self,
        company: PortfolioCompany,
        variances: list[VarianceAnalysis],
        kpi_analysis: dict,
    ) -> tuple[list[str], list[str]]:
        """Identify key strengths and concerns for executive summary."""
        strengths = []
        concerns = []

        # Check financial variances
        for v in variances:
            if v.metric == "Revenue":
                if v.variance_pct >= 5:
                    strengths.append(f"Revenue {v.variance_pct:.1f}% above plan")
                elif v.variance_pct <= -10:
                    concerns.append(f"Revenue {abs(v.variance_pct):.1f}% below plan")

            if v.metric == "EBITDA Margin":
                if v.variance_pct >= 2:
                    strengths.append(f"EBITDA margin {v.variance_pct:.1f}pp above target")
                elif v.variance_pct <= -3:
                    concerns.append(f"EBITDA margin {abs(v.variance_pct):.1f}pp below target")

        # Check KPIs
        strong_kpis = [
            k for k in company.operational_kpis
            if k.current_value >= k.target_value * 1.10
        ]
        weak_kpis = [
            k for k in company.operational_kpis
            if k.current_value < k.target_value * 0.85
        ]

        if strong_kpis:
            top_kpi = max(strong_kpis, key=lambda k: k.current_value / k.target_value if k.target_value else 0)
            strengths.append(f"Strong {top_kpi.name} performance")

        if weak_kpis:
            bottom_kpi = min(weak_kpis, key=lambda k: k.current_value / k.target_value if k.target_value else 1)
            concerns.append(f"Underperforming on {bottom_kpi.name}")

        # Check initiatives
        completed = sum(1 for i in company.initiatives if i.get("status") == "completed")
        at_risk = sum(1 for i in company.initiatives if i.get("status") in ["at_risk", "delayed"])

        if completed > 0:
            strengths.append(f"{completed} value creation initiative(s) completed")
        if at_risk > 0:
            concerns.append(f"{at_risk} initiative(s) at risk or delayed")

        # Check status
        if company.status == PortfolioStatus.OUTPERFORMING:
            strengths.insert(0, "Consistently exceeding performance targets")
        elif company.status == PortfolioStatus.AT_RISK:
            concerns.insert(0, "Portfolio company on at-risk watch list")

        return strengths[:5], concerns[:5]  # Limit to top 5 each

    def _explain_variance(self, metric: str, variance_pct: float) -> str:
        """Generate explanation text for variance."""
        if variance_pct >= 10:
            return f"{metric} significantly exceeds budget, indicating strong performance"
        elif variance_pct >= 5:
            return f"{metric} moderately above budget"
        elif variance_pct >= -5:
            return f"{metric} in line with budget (within 5%)"
        elif variance_pct >= -10:
            return f"{metric} moderately below budget, monitoring required"
        else:
            return f"{metric} significantly below budget, remediation needed"

    def _explain_margin_variance(self, margin_variance: float) -> str:
        """Generate explanation for margin variance."""
        if margin_variance >= 2:
            return "Margin expansion driven by operating leverage or cost efficiencies"
        elif margin_variance >= 0:
            return "Margins stable and in line with expectations"
        elif margin_variance >= -2:
            return "Slight margin pressure, likely from mix or input cost changes"
        else:
            return "Significant margin compression requiring operational review"


# Singleton instance
_kpi_tracker: Optional[KPITracker] = None


def get_kpi_tracker() -> KPITracker:
    """Get the singleton KPI tracker instance."""
    global _kpi_tracker
    if _kpi_tracker is None:
        _kpi_tracker = KPITracker()
    return _kpi_tracker
