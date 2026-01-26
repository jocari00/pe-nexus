"""ValueCreationMonitor Agent - Monitors portfolio company performance.

This agent tracks KPIs, generates alerts, and produces LP reports for
portfolio companies in the PE-Nexus system.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.agents.base import AgentOutput, AgentState, BaseAgent

from .kpi_tracker import (
    AlertSeverity,
    KPIAnalysisResult,
    KPITracker,
    get_kpi_tracker,
)
from .lp_reporter import LPReport, LPReporter, get_lp_reporter
from .mock_data import (
    PortfolioCompany,
    PortfolioStatus,
    get_all_companies,
    get_companies_by_status,
    get_company_by_id,
    get_portfolio_summary,
)

logger = logging.getLogger(__name__)


class ValueCreationMonitorAgent(BaseAgent):
    """
    Autonomous agent for monitoring portfolio company performance.

    Capabilities:
    - Track KPIs against targets and budgets
    - Generate variance analysis and alerts
    - Monitor value creation initiative progress
    - Generate quarterly LP reports
    - Provide portfolio-level dashboards

    Modes:
    - dashboard: Get portfolio-level summary and status
    - analyze: Analyze a specific company's KPIs
    - alerts: Get all active alerts across portfolio
    - report: Generate LP quarterly report
    - company_detail: Get detailed info for a company
    - list_companies: List all portfolio companies
    """

    def __init__(self):
        """Initialize the ValueCreationMonitor agent."""
        super().__init__(
            name="ValueCreationMonitor",
            description="Monitors portfolio company KPIs and generates LP reports",
            max_iterations=3,
        )
        self._kpi_tracker = get_kpi_tracker()
        self._lp_reporter = get_lp_reporter()

    def get_system_prompt(self) -> str:
        """System prompt for portfolio monitoring."""
        return """You are a Portfolio Monitoring Analyst at a private equity firm.
Your role is to track portfolio company performance, identify issues early, and communicate
effectively with Limited Partners.

Focus areas:
1. Financial Performance - Revenue, EBITDA, margins vs plan
2. Operational KPIs - Company-specific metrics that drive value
3. Value Creation Initiatives - Progress on strategic plans
4. Risk Identification - Early warning signs of underperformance
5. LP Communication - Clear, concise reporting for investors

When analyzing companies:
- Compare actuals to budget and prior periods
- Identify trends (improving, stable, declining)
- Flag items requiring attention (Red/Yellow/Green)
- Provide actionable recommendations
- Maintain objectivity while highlighting concerns

When generating reports:
- Lead with key insights and actions needed
- Use data to support narratives
- Be transparent about challenges
- Provide forward-looking commentary
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for the Monitor agent."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "dashboard")

            if mode == "dashboard":
                result = self._get_dashboard(input_data, state)
            elif mode == "analyze":
                result = self._analyze_company(input_data, state)
            elif mode == "alerts":
                result = self._get_alerts(input_data, state)
            elif mode == "report":
                result = self._generate_lp_report(input_data, state)
            elif mode == "company_detail":
                result = self._get_company_detail(input_data, state)
            elif mode == "list_companies":
                result = self._list_companies(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _get_dashboard(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Get portfolio-level dashboard summary."""
        companies = get_all_companies()
        summary = get_portfolio_summary()

        # Analyze each company for current status
        company_summaries = []
        total_alerts = 0
        critical_alerts = 0

        for company in companies:
            analysis = self._kpi_tracker.analyze_company(company)
            total_alerts += len(analysis.alerts)
            critical_alerts += analysis.critical_alerts

            company_summaries.append({
                "company_id": company.company_id,
                "name": company.name,
                "industry": company.industry,
                "status": company.status.value,
                "ytd_revenue_variance": f"{analysis.ytd_revenue_vs_budget_pct:+.1f}%",
                "ytd_ebitda_variance": f"{analysis.ytd_ebitda_vs_budget_pct:+.1f}%",
                "revenue_trend": analysis.revenue_trend.value,
                "alert_count": len(analysis.alerts),
                "critical_alerts": analysis.critical_alerts,
            })

        # Record extraction
        extraction_record = {
            "type": "portfolio_dashboard",
            "companies_analyzed": len(companies),
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Flag for review if critical alerts
        if critical_alerts > 0:
            state["requires_review"] = True

        state["confidence_scores"]["dashboard"] = 0.95

        return {
            "mode": "dashboard",
            "summary": summary,
            "companies": company_summaries,
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _analyze_company(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Analyze KPIs for a specific company."""
        company_id = input_data.get("company_id")
        period = input_data.get("period", "quarterly")

        if not company_id:
            state["errors"].append("company_id is required for analysis")
            return {}

        company = get_company_by_id(company_id)
        if not company:
            state["errors"].append(f"Company not found: {company_id}")
            return {}

        # Perform KPI analysis
        analysis = self._kpi_tracker.analyze_company(company, period)

        # Optionally enhance with LLM commentary
        commentary = None
        if self._client is not None:
            commentary = self._generate_analysis_commentary(company, analysis)

        # Record extraction
        extraction_record = {
            "type": "kpi_analysis",
            "company_id": company_id,
            "company_name": company.name,
            "alerts_generated": len(analysis.alerts),
            "critical_alerts": analysis.critical_alerts,
            "llm_enhanced": commentary is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Flag for review if critical alerts or at-risk status
        if analysis.critical_alerts > 0 or company.status == PortfolioStatus.AT_RISK:
            state["requires_review"] = True

        state["confidence_scores"]["kpi_analysis"] = 0.90 if self._client else 0.80

        result = {
            "mode": "analyze",
            "analysis": analysis.to_dict(),
        }

        if commentary:
            result["commentary"] = commentary

        return result

    def _generate_analysis_commentary(
        self,
        company: PortfolioCompany,
        analysis: KPIAnalysisResult,
    ) -> Optional[str]:
        """Use LLM to generate insightful commentary on analysis."""
        prompt = f"""Analyze the following portfolio company performance data and provide a brief (2-3 paragraph)
executive commentary highlighting key insights, concerns, and recommendations.

Company: {company.name}
Industry: {company.industry}
Status: {analysis.status.value}

Financial Performance:
- YTD Revenue: ${analysis.ytd_revenue:.1f}M ({analysis.ytd_revenue_vs_budget_pct:+.1f}% vs budget)
- YTD EBITDA: ${analysis.ytd_ebitda:.1f}M ({analysis.ytd_ebitda_vs_budget_pct:+.1f}% vs budget)
- Revenue Trend: {analysis.revenue_trend.value}
- Margin Trend: {analysis.margin_trend.value}

Key Strengths: {', '.join(analysis.key_strengths) if analysis.key_strengths else 'None identified'}
Key Concerns: {', '.join(analysis.key_concerns) if analysis.key_concerns else 'None identified'}

Alerts: {analysis.critical_alerts} critical, {analysis.high_alerts} high priority
KPIs: {analysis.kpis_on_target + analysis.kpis_above_target} on/above target, {analysis.kpis_below_target} below target

Value Creation: {analysis.initiatives_on_track} initiatives on track, {analysis.initiatives_at_risk} at risk

Please provide executive-level commentary suitable for a board update or LP communication.
"""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=1024,
            )

            text = self.get_text_from_response(response)
            if text:
                return text.strip()

        except Exception as e:
            logger.warning(f"Failed to generate LLM commentary: {e}")

        return None

    def _get_alerts(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Get all active alerts across portfolio."""
        severity_filter = input_data.get("severity")  # Optional: critical, high, medium, low
        company_filter = input_data.get("company_id")  # Optional: filter by company

        companies = get_all_companies()
        all_alerts = []

        for company in companies:
            if company_filter and company.company_id != company_filter:
                continue

            analysis = self._kpi_tracker.analyze_company(company)
            for alert in analysis.alerts:
                if severity_filter and alert.severity.value != severity_filter:
                    continue
                all_alerts.append(alert.to_dict())

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_alerts.sort(key=lambda a: severity_order.get(a["severity"], 5))

        # Record extraction
        extraction_record = {
            "type": "alerts_query",
            "total_alerts": len(all_alerts),
            "severity_filter": severity_filter,
            "company_filter": company_filter,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # Flag for review if any critical alerts
        critical_count = sum(1 for a in all_alerts if a["severity"] == "critical")
        if critical_count > 0:
            state["requires_review"] = True

        state["confidence_scores"]["alerts"] = 0.95

        return {
            "mode": "alerts",
            "total_alerts": len(all_alerts),
            "critical_count": critical_count,
            "high_count": sum(1 for a in all_alerts if a["severity"] == "high"),
            "alerts": all_alerts,
        }

    def _generate_lp_report(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Generate LP quarterly report."""
        quarter = input_data.get("quarter", 4)
        year = input_data.get("year", 2025)
        fund_name = input_data.get("fund_name", "PE-Nexus Fund I")

        # Update reporter fund name if provided
        reporter = LPReporter(fund_name=fund_name)

        # Generate KPI analyses for all companies
        companies = get_all_companies()
        kpi_analyses = [
            self._kpi_tracker.analyze_company(company)
            for company in companies
        ]

        # Generate report
        report = reporter.generate_report(
            quarter=quarter,
            year=year,
            kpi_analyses=kpi_analyses,
        )

        # Optionally enhance executive summary with LLM
        if self._client is not None:
            enhanced_summary = self._enhance_executive_summary(report)
            if enhanced_summary:
                report.executive_summary = enhanced_summary

        # Record extraction
        extraction_record = {
            "type": "lp_report",
            "report_id": report.report_id,
            "quarter": quarter,
            "year": year,
            "companies_included": len(report.company_updates),
            "llm_enhanced": self._client is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        # LP reports always require review before distribution
        state["requires_review"] = True
        state["confidence_scores"]["lp_report"] = 0.85 if self._client else 0.75

        return {
            "mode": "report",
            "report": report.to_dict(),
        }

    def _enhance_executive_summary(self, report: LPReport) -> Optional[str]:
        """Use LLM to enhance the executive summary."""
        prompt = f"""You are writing an executive summary for a quarterly LP (Limited Partner) report
for {report.fund_name}. Based on the following data, write a compelling 2-3 paragraph executive
summary that:
1. Opens with the overall portfolio performance characterization
2. Highlights key wins and successes
3. Acknowledges challenges transparently
4. Provides forward-looking commentary

Portfolio Metrics:
- Total Companies: {report.portfolio_metrics.total_companies}
- Companies On Track: {report.portfolio_metrics.companies_on_track}
- Companies At Risk: {report.portfolio_metrics.companies_at_risk}
- Weighted Revenue Growth: {report.portfolio_metrics.weighted_revenue_growth:.1f}%
- Estimated Portfolio MOIC: {report.portfolio_metrics.aggregate_moic:.2f}x
- Estimated IRR: {report.portfolio_metrics.aggregate_irr:.1f}%

Key Highlights:
{chr(10).join('- ' + h for h in report.key_highlights)}

Key Concerns:
{chr(10).join('- ' + c for c in report.key_concerns)}

Current Draft:
{report.executive_summary}

Write a polished, professional executive summary suitable for LP distribution.
"""

        try:
            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=1024,
            )

            text = self.get_text_from_response(response)
            if text:
                return text.strip()

        except Exception as e:
            logger.warning(f"Failed to enhance executive summary: {e}")

        return None

    def _get_company_detail(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Get detailed information for a specific company."""
        company_id = input_data.get("company_id")

        if not company_id:
            state["errors"].append("company_id is required")
            return {}

        company = get_company_by_id(company_id)
        if not company:
            state["errors"].append(f"Company not found: {company_id}")
            return {}

        # Get full company data
        company_data = company.to_dict()

        # Add detailed financials
        company_data["monthly_actuals"] = [
            {
                "month": m.month,
                "revenue": float(m.revenue),
                "ebitda": float(m.ebitda),
                "net_income": float(m.net_income),
                "cash_balance": float(m.cash_balance),
                "debt_balance": float(m.debt_balance),
            }
            for m in company.monthly_actuals
        ]

        company_data["monthly_budget"] = [
            {
                "month": b.month,
                "revenue": float(b.revenue),
                "ebitda": float(b.ebitda),
                "net_income": float(b.net_income),
                "headcount": b.headcount,
            }
            for b in company.monthly_budget
        ]

        company_data["operational_kpis"] = [
            {
                "name": k.name,
                "category": k.category.value,
                "current_value": k.current_value,
                "target_value": k.target_value,
                "unit": k.unit,
                "period": k.period,
                "trend": k.trend,
                "on_target": k.current_value >= k.target_value * 0.90,
            }
            for k in company.operational_kpis
        ]

        company_data["initiatives"] = company.initiatives

        # Record extraction
        extraction_record = {
            "type": "company_detail",
            "company_id": company_id,
            "company_name": company.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)

        state["confidence_scores"]["company_detail"] = 0.95

        return {
            "mode": "company_detail",
            "company": company_data,
        }

    def _list_companies(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """List all portfolio companies."""
        status_filter = input_data.get("status")  # Optional: on_track, watch, at_risk, outperforming
        industry_filter = input_data.get("industry")  # Optional: Technology, Healthcare, etc.

        companies = get_all_companies()

        if status_filter:
            try:
                status = PortfolioStatus(status_filter)
                companies = [c for c in companies if c.status == status]
            except ValueError:
                pass

        if industry_filter:
            companies = [
                c for c in companies
                if c.industry.lower() == industry_filter.lower()
            ]

        # Use to_dict() to get full company data including financials
        company_list = [c.to_dict() for c in companies]

        state["confidence_scores"]["list_companies"] = 0.95

        return {
            "mode": "list_companies",
            "total_count": len(company_list),
            "filters_applied": {
                "status": status_filter,
                "industry": industry_filter,
            },
            "companies": company_list,
        }

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if processing is complete."""
        return bool(state.get("output_data")) or bool(state.get("errors"))

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_dashboard(self) -> AgentOutput:
        """
        Get portfolio-level dashboard summary.

        Returns:
            AgentOutput with portfolio dashboard
        """
        return await self.run(input_data={"mode": "dashboard"})

    async def analyze_company(
        self,
        company_id: str,
        period: str = "quarterly",
    ) -> AgentOutput:
        """
        Analyze KPIs for a specific company.

        Args:
            company_id: ID of the portfolio company
            period: Analysis period (quarterly, annual, ytd)

        Returns:
            AgentOutput with KPI analysis
        """
        input_data = {
            "mode": "analyze",
            "company_id": company_id,
            "period": period,
        }
        return await self.run(input_data=input_data)

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> AgentOutput:
        """
        Get alerts across portfolio.

        Args:
            severity: Optional filter by severity (critical, high, medium, low)
            company_id: Optional filter by company

        Returns:
            AgentOutput with alerts list
        """
        input_data = {
            "mode": "alerts",
            "severity": severity,
            "company_id": company_id,
        }
        return await self.run(input_data=input_data)

    async def generate_lp_report(
        self,
        quarter: int,
        year: int,
        fund_name: str = "PE-Nexus Fund I",
    ) -> AgentOutput:
        """
        Generate LP quarterly report.

        Args:
            quarter: Quarter number (1-4)
            year: Year
            fund_name: Fund name for report header

        Returns:
            AgentOutput with LP report
        """
        input_data = {
            "mode": "report",
            "quarter": quarter,
            "year": year,
            "fund_name": fund_name,
        }
        return await self.run(input_data=input_data)

    async def get_company_detail(
        self,
        company_id: str,
    ) -> AgentOutput:
        """
        Get detailed information for a company.

        Args:
            company_id: ID of the portfolio company

        Returns:
            AgentOutput with company details
        """
        input_data = {
            "mode": "company_detail",
            "company_id": company_id,
        }
        return await self.run(input_data=input_data)

    async def list_companies(
        self,
        status: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AgentOutput:
        """
        List portfolio companies with optional filters.

        Args:
            status: Optional status filter (on_track, watch, at_risk, outperforming)
            industry: Optional industry filter

        Returns:
            AgentOutput with company list
        """
        input_data = {
            "mode": "list_companies",
            "status": status,
            "industry": industry,
        }
        return await self.run(input_data=input_data)


def create_vcm() -> ValueCreationMonitorAgent:
    """Factory function to create a ValueCreationMonitor agent."""
    return ValueCreationMonitorAgent()
