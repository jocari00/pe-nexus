"""LP Report Generator for ValueCreationMonitor agent.

Generates quarterly LP (Limited Partner) reports with portfolio performance
summaries, individual company updates, and value creation narratives.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .kpi_tracker import KPIAnalysisResult, TrendDirection
from .mock_data import (
    PortfolioCompany,
    PortfolioStatus,
    get_all_companies,
    get_portfolio_summary,
)


@dataclass
class CompanyUpdate:
    """Individual company update for LP report."""
    company_id: str
    company_name: str
    industry: str
    status: str
    status_color: str  # green, yellow, red
    headline: str
    performance_summary: str
    key_metrics: dict
    initiatives_update: str
    outlook: str
    concerns: list[str]


@dataclass
class PortfolioMetrics:
    """Aggregate portfolio metrics."""
    total_invested: float
    total_companies: int
    weighted_revenue_growth: float
    weighted_ebitda_growth: float
    companies_on_track: int
    companies_at_risk: int
    aggregate_irr: float  # Estimated
    aggregate_moic: float  # Estimated


@dataclass
class LPReport:
    """Complete LP quarterly report."""
    report_id: str
    quarter: int
    year: int
    generated_at: str
    fund_name: str

    # Executive Summary
    executive_summary: str
    key_highlights: list[str]
    key_concerns: list[str]

    # Portfolio Overview
    portfolio_metrics: PortfolioMetrics
    status_breakdown: dict[str, int]

    # Individual Company Updates
    company_updates: list[CompanyUpdate]

    # Value Creation Summary
    value_creation_narrative: str
    initiatives_summary: dict

    # Outlook
    outlook_narrative: str
    upcoming_milestones: list[str]

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "quarter": self.quarter,
            "year": self.year,
            "generated_at": self.generated_at,
            "fund_name": self.fund_name,
            "executive_summary": self.executive_summary,
            "key_highlights": self.key_highlights,
            "key_concerns": self.key_concerns,
            "portfolio_metrics": {
                "total_invested": self.portfolio_metrics.total_invested,
                "total_companies": self.portfolio_metrics.total_companies,
                "weighted_revenue_growth": self.portfolio_metrics.weighted_revenue_growth,
                "weighted_ebitda_growth": self.portfolio_metrics.weighted_ebitda_growth,
                "companies_on_track": self.portfolio_metrics.companies_on_track,
                "companies_at_risk": self.portfolio_metrics.companies_at_risk,
                "aggregate_irr": self.portfolio_metrics.aggregate_irr,
                "aggregate_moic": self.portfolio_metrics.aggregate_moic,
            },
            "status_breakdown": self.status_breakdown,
            "company_updates": [
                {
                    "company_id": u.company_id,
                    "company_name": u.company_name,
                    "industry": u.industry,
                    "status": u.status,
                    "status_color": u.status_color,
                    "headline": u.headline,
                    "performance_summary": u.performance_summary,
                    "key_metrics": u.key_metrics,
                    "initiatives_update": u.initiatives_update,
                    "outlook": u.outlook,
                    "concerns": u.concerns,
                }
                for u in self.company_updates
            ],
            "value_creation_narrative": self.value_creation_narrative,
            "initiatives_summary": self.initiatives_summary,
            "outlook_narrative": self.outlook_narrative,
            "upcoming_milestones": self.upcoming_milestones,
        }


class LPReporter:
    """
    LP Report generation engine.

    Generates quarterly reports for Limited Partners with portfolio
    performance summaries, company updates, and value creation narratives.
    """

    def __init__(self, fund_name: str = "PE-Nexus Fund I"):
        self.fund_name = fund_name
        self._report_counter = 0

    def _generate_report_id(self, quarter: int, year: int) -> str:
        """Generate unique report ID."""
        self._report_counter += 1
        return f"lp-report-{year}Q{quarter}-{self._report_counter:03d}"

    def generate_report(
        self,
        quarter: int,
        year: int,
        kpi_analyses: Optional[list[KPIAnalysisResult]] = None,
    ) -> LPReport:
        """
        Generate a complete LP quarterly report.

        Args:
            quarter: Quarter number (1-4)
            year: Year
            kpi_analyses: Optional pre-computed KPI analyses for companies

        Returns:
            Complete LP report
        """
        companies = get_all_companies()
        summary = get_portfolio_summary()

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(companies)

        # Generate company updates
        company_updates = [
            self._generate_company_update(company, kpi_analyses)
            for company in companies
        ]

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            companies, portfolio_metrics, quarter, year
        )

        # Identify highlights and concerns
        highlights = self._identify_highlights(companies, company_updates)
        concerns = self._identify_concerns(companies, company_updates)

        # Generate value creation narrative
        value_creation = self._generate_value_creation_narrative(companies)

        # Generate initiatives summary
        initiatives = self._summarize_initiatives(companies)

        # Generate outlook
        outlook = self._generate_outlook(companies, quarter, year)
        milestones = self._identify_upcoming_milestones(companies)

        return LPReport(
            report_id=self._generate_report_id(quarter, year),
            quarter=quarter,
            year=year,
            generated_at=datetime.now().isoformat(),
            fund_name=self.fund_name,
            executive_summary=executive_summary,
            key_highlights=highlights,
            key_concerns=concerns,
            portfolio_metrics=portfolio_metrics,
            status_breakdown=summary["status_breakdown"],
            company_updates=company_updates,
            value_creation_narrative=value_creation,
            initiatives_summary=initiatives,
            outlook_narrative=outlook,
            upcoming_milestones=milestones,
        )

    def _calculate_portfolio_metrics(
        self,
        companies: list[PortfolioCompany],
    ) -> PortfolioMetrics:
        """Calculate aggregate portfolio metrics."""
        total_invested = sum(
            float(c.entry_ev) * c.ownership_pct / 100
            for c in companies
        )

        # Calculate weighted growth rates
        total_weight = 0
        weighted_rev_growth = 0
        weighted_ebitda_growth = 0

        for company in companies:
            if len(company.monthly_actuals) >= 6:
                weight = float(company.entry_ev) * company.ownership_pct / 100

                # Calculate 6-month revenue growth
                rev_start = float(company.monthly_actuals[0].revenue)
                rev_end = float(company.monthly_actuals[-1].revenue)
                if rev_start > 0:
                    rev_growth = (rev_end - rev_start) / rev_start
                    weighted_rev_growth += rev_growth * weight

                # Calculate 6-month EBITDA growth
                ebitda_start = float(company.monthly_actuals[0].ebitda)
                ebitda_end = float(company.monthly_actuals[-1].ebitda)
                if ebitda_start > 0:
                    ebitda_growth = (ebitda_end - ebitda_start) / ebitda_start
                    weighted_ebitda_growth += ebitda_growth * weight

                total_weight += weight

        if total_weight > 0:
            weighted_rev_growth = weighted_rev_growth / total_weight * 100
            weighted_ebitda_growth = weighted_ebitda_growth / total_weight * 100
        else:
            weighted_rev_growth = 0
            weighted_ebitda_growth = 0

        # Count status categories
        on_track = sum(
            1 for c in companies
            if c.status in [PortfolioStatus.ON_TRACK, PortfolioStatus.OUTPERFORMING]
        )
        at_risk = sum(
            1 for c in companies
            if c.status in [PortfolioStatus.AT_RISK, PortfolioStatus.WATCH]
        )

        # Estimate aggregate returns (simplified calculation)
        aggregate_irr = self._estimate_portfolio_irr(companies)
        aggregate_moic = self._estimate_portfolio_moic(companies)

        return PortfolioMetrics(
            total_invested=total_invested,
            total_companies=len(companies),
            weighted_revenue_growth=weighted_rev_growth,
            weighted_ebitda_growth=weighted_ebitda_growth,
            companies_on_track=on_track,
            companies_at_risk=at_risk,
            aggregate_irr=aggregate_irr,
            aggregate_moic=aggregate_moic,
        )

    def _estimate_portfolio_irr(self, companies: list[PortfolioCompany]) -> float:
        """Estimate portfolio-level IRR based on current performance."""
        # Simplified: Use average target exit multiple and holding period
        weighted_irr = 0
        total_weight = 0

        for company in companies:
            entry_cost = float(company.entry_ev) * company.ownership_pct / 100
            months_held = company._calculate_months_held()
            years_held = max(months_held / 12, 0.5)

            # Estimate current multiple based on performance
            if company.status == PortfolioStatus.OUTPERFORMING:
                current_multiple = 1.3
            elif company.status == PortfolioStatus.ON_TRACK:
                current_multiple = 1.15
            elif company.status == PortfolioStatus.WATCH:
                current_multiple = 1.0
            else:
                current_multiple = 0.85

            # Calculate IRR for this investment
            if years_held > 0:
                irr = (current_multiple ** (1 / years_held) - 1) * 100
                weighted_irr += irr * entry_cost
                total_weight += entry_cost

        return weighted_irr / total_weight if total_weight > 0 else 0

    def _estimate_portfolio_moic(self, companies: list[PortfolioCompany]) -> float:
        """Estimate portfolio-level MOIC based on current performance."""
        total_invested = 0
        total_current_value = 0

        for company in companies:
            entry_cost = float(company.entry_ev) * company.ownership_pct / 100
            total_invested += entry_cost

            # Estimate current value based on status
            if company.status == PortfolioStatus.OUTPERFORMING:
                multiplier = 1.3
            elif company.status == PortfolioStatus.ON_TRACK:
                multiplier = 1.15
            elif company.status == PortfolioStatus.WATCH:
                multiplier = 1.0
            else:
                multiplier = 0.85

            total_current_value += entry_cost * multiplier

        return total_current_value / total_invested if total_invested > 0 else 1.0

    def _generate_company_update(
        self,
        company: PortfolioCompany,
        kpi_analyses: Optional[list[KPIAnalysisResult]],
    ) -> CompanyUpdate:
        """Generate update section for a single company."""
        # Determine status color
        status_color = {
            PortfolioStatus.OUTPERFORMING: "green",
            PortfolioStatus.ON_TRACK: "green",
            PortfolioStatus.WATCH: "yellow",
            PortfolioStatus.AT_RISK: "red",
        }.get(company.status, "yellow")

        # Generate headline based on status
        headline = self._generate_company_headline(company)

        # Generate performance summary
        performance = self._generate_performance_summary(company)

        # Extract key metrics
        key_metrics = self._extract_key_metrics(company)

        # Generate initiatives update
        initiatives = self._generate_initiatives_update(company)

        # Generate outlook
        outlook = self._generate_company_outlook(company)

        # Identify concerns
        concerns = self._identify_company_concerns(company)

        return CompanyUpdate(
            company_id=company.company_id,
            company_name=company.name,
            industry=company.industry,
            status=company.status.value,
            status_color=status_color,
            headline=headline,
            performance_summary=performance,
            key_metrics=key_metrics,
            initiatives_update=initiatives,
            outlook=outlook,
            concerns=concerns,
        )

    def _generate_company_headline(self, company: PortfolioCompany) -> str:
        """Generate a headline for company update."""
        if company.status == PortfolioStatus.OUTPERFORMING:
            return f"{company.name} continues to exceed expectations with strong execution"
        elif company.status == PortfolioStatus.ON_TRACK:
            return f"{company.name} delivers solid performance in line with plan"
        elif company.status == PortfolioStatus.WATCH:
            return f"{company.name} facing headwinds; management focused on recovery"
        else:
            return f"{company.name} requires increased attention; turnaround plan in development"

    def _generate_performance_summary(self, company: PortfolioCompany) -> str:
        """Generate performance summary paragraph."""
        if not company.monthly_actuals or not company.monthly_budget:
            return "Limited financial data available for the period."

        latest_actual = company.monthly_actuals[-1]
        matching_budget = None
        for b in company.monthly_budget:
            if b.month == latest_actual.month:
                matching_budget = b
                break

        if not matching_budget:
            matching_budget = company.monthly_budget[-1]

        rev_actual = float(latest_actual.revenue)
        rev_budget = float(matching_budget.revenue)
        rev_variance = ((rev_actual - rev_budget) / rev_budget * 100) if rev_budget else 0

        ebitda_actual = float(latest_actual.ebitda)
        ebitda_budget = float(matching_budget.ebitda)
        ebitda_variance = ((ebitda_actual - ebitda_budget) / ebitda_budget * 100) if ebitda_budget else 0

        # Calculate margin
        actual_margin = (ebitda_actual / rev_actual * 100) if rev_actual else 0

        if rev_variance >= 5:
            rev_text = f"Revenue of ${rev_actual:.1f}M exceeded plan by {rev_variance:.1f}%"
        elif rev_variance >= -5:
            rev_text = f"Revenue of ${rev_actual:.1f}M was in line with plan"
        else:
            rev_text = f"Revenue of ${rev_actual:.1f}M was {abs(rev_variance):.1f}% below plan"

        if ebitda_variance >= 5:
            ebitda_text = f"EBITDA margin of {actual_margin:.1f}% reflected operating leverage"
        elif ebitda_variance >= -5:
            ebitda_text = f"EBITDA margin of {actual_margin:.1f}% was in line with expectations"
        else:
            ebitda_text = f"EBITDA margin of {actual_margin:.1f}% was compressed due to cost pressures"

        return f"{rev_text}. {ebitda_text}. {company.status_reason}"

    def _extract_key_metrics(self, company: PortfolioCompany) -> dict:
        """Extract key metrics for display."""
        metrics = {}

        if company.monthly_actuals:
            latest = company.monthly_actuals[-1]
            metrics["ltm_revenue"] = f"${float(latest.revenue) * 12:.1f}M"
            metrics["ltm_ebitda"] = f"${float(latest.ebitda) * 12:.1f}M"
            margin = float(latest.ebitda) / float(latest.revenue) * 100 if float(latest.revenue) else 0
            metrics["ebitda_margin"] = f"{margin:.1f}%"
            metrics["cash_balance"] = f"${float(latest.cash_balance):.1f}M"
            metrics["debt_balance"] = f"${float(latest.debt_balance):.1f}M"

        # Add top 3 operational KPIs
        for kpi in company.operational_kpis[:3]:
            metrics[kpi.name] = f"{kpi.current_value} {kpi.unit}"

        return metrics

    def _generate_initiatives_update(self, company: PortfolioCompany) -> str:
        """Generate update on value creation initiatives."""
        if not company.initiatives:
            return "No active initiatives to report."

        completed = [i for i in company.initiatives if i.get("status") == "completed"]
        on_track = [i for i in company.initiatives if i.get("status") == "on_track"]
        at_risk = [i for i in company.initiatives if i.get("status") in ["at_risk", "delayed"]]

        parts = []
        if completed:
            names = ", ".join(i.get("name", "") for i in completed)
            parts.append(f"Completed: {names}")
        if on_track:
            names = ", ".join(f"{i.get('name', '')} ({i.get('completion', 0)}%)" for i in on_track)
            parts.append(f"On track: {names}")
        if at_risk:
            names = ", ".join(f"{i.get('name', '')} ({i.get('status', '')})" for i in at_risk)
            parts.append(f"Requires attention: {names}")

        return ". ".join(parts) + "."

    def _generate_company_outlook(self, company: PortfolioCompany) -> str:
        """Generate outlook statement for company."""
        if company.status == PortfolioStatus.OUTPERFORMING:
            return (
                f"Management expects continued momentum into next quarter. "
                f"Exit planning underway for potential {company.exit_strategy.lower()} "
                f"targeting {company.target_exit_year}."
            )
        elif company.status == PortfolioStatus.ON_TRACK:
            return (
                f"On track to meet annual targets. Key focus areas include "
                f"maintaining growth trajectory and advancing value creation initiatives."
            )
        elif company.status == PortfolioStatus.WATCH:
            return (
                f"Near-term focus on operational improvement and cost management. "
                f"Board meeting scheduled to review recovery plan and resource requirements."
            )
        else:
            return (
                f"Management team developing comprehensive turnaround plan. "
                f"Considering operational restructuring and potential management changes. "
                f"Weekly monitoring cadence implemented."
            )

    def _identify_company_concerns(self, company: PortfolioCompany) -> list[str]:
        """Identify specific concerns for a company."""
        concerns = []

        if company.status == PortfolioStatus.AT_RISK:
            concerns.append("Overall performance significantly below plan")

        if company.monthly_actuals:
            latest = company.monthly_actuals[-1]
            # Check cash position
            if float(latest.cash_balance) < 3:
                concerns.append(f"Low cash balance (${float(latest.cash_balance):.1f}M)")

        # Check at-risk initiatives
        at_risk = [i for i in company.initiatives if i.get("status") in ["at_risk", "delayed"]]
        for i in at_risk:
            if i.get("impact") == "High":
                concerns.append(f"High-impact initiative '{i.get('name')}' at risk")

        # Check declining KPIs
        declining = [k for k in company.operational_kpis if k.trend == "down"]
        if len(declining) >= 3:
            concerns.append(f"{len(declining)} KPIs showing declining trends")

        return concerns[:4]  # Limit to top 4

    def _generate_executive_summary(
        self,
        companies: list[PortfolioCompany],
        metrics: PortfolioMetrics,
        quarter: int,
        year: int,
    ) -> str:
        """Generate executive summary paragraph."""
        quarter_name = f"Q{quarter} {year}"

        # Performance characterization
        if metrics.companies_on_track >= len(companies) * 0.8:
            performance = "strong"
        elif metrics.companies_at_risk <= 1:
            performance = "solid"
        else:
            performance = "mixed"

        # Revenue growth characterization
        if metrics.weighted_revenue_growth >= 15:
            growth_desc = "robust revenue growth"
        elif metrics.weighted_revenue_growth >= 5:
            growth_desc = "steady revenue growth"
        elif metrics.weighted_revenue_growth >= 0:
            growth_desc = "flat revenue performance"
        else:
            growth_desc = "revenue headwinds"

        summary = (
            f"{self.fund_name} delivered {performance} performance in {quarter_name}, "
            f"with {growth_desc} of {metrics.weighted_revenue_growth:.1f}% across the portfolio. "
            f"Of our {metrics.total_companies} portfolio companies, "
            f"{metrics.companies_on_track} are performing on or above plan, "
            f"while {metrics.companies_at_risk} require increased attention. "
            f"Aggregate estimated portfolio MOIC stands at {metrics.aggregate_moic:.2f}x "
            f"with an estimated IRR of {metrics.aggregate_irr:.1f}%."
        )

        return summary

    def _identify_highlights(
        self,
        companies: list[PortfolioCompany],
        updates: list[CompanyUpdate],
    ) -> list[str]:
        """Identify key highlights for executive summary."""
        highlights = []

        # Outperforming companies
        outperforming = [c for c in companies if c.status == PortfolioStatus.OUTPERFORMING]
        if outperforming:
            names = ", ".join(c.name for c in outperforming)
            highlights.append(f"{names} exceeding performance targets")

        # Completed initiatives
        completed_count = sum(
            len([i for i in c.initiatives if i.get("status") == "completed"])
            for c in companies
        )
        if completed_count > 0:
            highlights.append(f"{completed_count} value creation initiative(s) completed this quarter")

        # Strong KPIs
        for company in companies:
            for kpi in company.operational_kpis:
                if kpi.current_value >= kpi.target_value * 1.2 and kpi.trend == "up":
                    highlights.append(f"{company.name}: Strong {kpi.name} (+20% vs target)")
                    break

        return highlights[:5]

    def _identify_concerns(
        self,
        companies: list[PortfolioCompany],
        updates: list[CompanyUpdate],
    ) -> list[str]:
        """Identify key concerns for executive summary."""
        concerns = []

        # At-risk companies
        at_risk = [c for c in companies if c.status == PortfolioStatus.AT_RISK]
        if at_risk:
            for c in at_risk:
                concerns.append(f"{c.name} on at-risk watch list")

        # Companies on watch
        watch = [c for c in companies if c.status == PortfolioStatus.WATCH]
        if watch:
            names = ", ".join(c.name for c in watch)
            concerns.append(f"{names} on watch list requiring close monitoring")

        # At-risk initiatives
        for company in companies:
            for i in company.initiatives:
                if i.get("status") == "at_risk" and i.get("impact") == "High":
                    concerns.append(
                        f"{company.name}: '{i.get('name')}' initiative at risk"
                    )

        return concerns[:5]

    def _generate_value_creation_narrative(
        self,
        companies: list[PortfolioCompany],
    ) -> str:
        """Generate value creation section narrative."""
        total_initiatives = sum(len(c.initiatives) for c in companies)
        completed = sum(
            len([i for i in c.initiatives if i.get("status") == "completed"])
            for c in companies
        )
        on_track = sum(
            len([i for i in c.initiatives if i.get("status") == "on_track"])
            for c in companies
        )
        at_risk = sum(
            len([i for i in c.initiatives if i.get("status") in ["at_risk", "delayed"]])
            for c in companies
        )

        return (
            f"The portfolio has {total_initiatives} active value creation initiatives "
            f"across all companies. This quarter, {completed} initiative(s) were completed, "
            f"{on_track} remain on track, and {at_risk} require attention. "
            f"Key focus areas include operational efficiency, revenue growth acceleration, "
            f"and strategic market expansion. The deal teams continue to work closely with "
            f"management to execute against the value creation plans developed at acquisition."
        )

    def _summarize_initiatives(self, companies: list[PortfolioCompany]) -> dict:
        """Summarize initiatives across portfolio."""
        by_status = {"completed": 0, "on_track": 0, "at_risk": 0, "delayed": 0, "planning": 0}
        by_impact = {"High": 0, "Medium": 0, "Low": 0}

        for company in companies:
            for i in company.initiatives:
                status = i.get("status", "unknown")
                if status in by_status:
                    by_status[status] += 1
                impact = i.get("impact", "Medium")
                if impact in by_impact:
                    by_impact[impact] += 1

        return {
            "by_status": by_status,
            "by_impact": by_impact,
            "total": sum(len(c.initiatives) for c in companies),
        }

    def _generate_outlook(
        self,
        companies: list[PortfolioCompany],
        quarter: int,
        year: int,
    ) -> str:
        """Generate portfolio outlook section."""
        next_quarter = quarter + 1 if quarter < 4 else 1
        next_year = year if quarter < 4 else year + 1

        # Check for upcoming exits
        potential_exits = [
            c for c in companies
            if c.target_exit_year == next_year and c.status in [
                PortfolioStatus.OUTPERFORMING, PortfolioStatus.ON_TRACK
            ]
        ]

        outlook = (
            f"Looking ahead to Q{next_quarter} {next_year}, we expect continued execution "
            f"against our value creation plans. "
        )

        if potential_exits:
            names = ", ".join(c.name for c in potential_exits)
            outlook += f"We are actively exploring exit opportunities for {names}. "

        # Add focus areas
        at_risk_count = sum(
            1 for c in companies
            if c.status in [PortfolioStatus.AT_RISK, PortfolioStatus.WATCH]
        )
        if at_risk_count > 0:
            outlook += (
                f"Increased focus will be placed on the {at_risk_count} company(ies) "
                f"requiring additional support, with monthly board review cadence implemented."
            )

        return outlook

    def _identify_upcoming_milestones(self, companies: list[PortfolioCompany]) -> list[str]:
        """Identify upcoming milestones across portfolio."""
        milestones = []

        for company in companies:
            # Near-completion initiatives
            for i in company.initiatives:
                if i.get("status") == "on_track" and i.get("completion", 0) >= 75:
                    milestones.append(
                        f"{company.name}: {i.get('name')} expected completion ({i.get('completion')}% done)"
                    )

            # Exit readiness
            if company.status == PortfolioStatus.OUTPERFORMING:
                milestones.append(f"{company.name}: Exit process preparation")

        return milestones[:6]


# Singleton instance
_lp_reporter: Optional[LPReporter] = None


def get_lp_reporter(fund_name: str = "PE-Nexus Fund I") -> LPReporter:
    """Get the LP reporter instance."""
    global _lp_reporter
    if _lp_reporter is None:
        _lp_reporter = LPReporter(fund_name=fund_name)
    return _lp_reporter
