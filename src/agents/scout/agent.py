"""IntelligenceScout Agent - Identifies potential acquisition targets from market signals.

This agent monitors news, job postings, and macroeconomic data to identify
companies that may be acquisition targets, then scores and ranks them.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from src.agents.base import AgentOutput, AgentState, BaseAgent
from src.schemas.deal import DealStage
from src.schemas.events import EventType

from .mock_data import MOCK_COMPANIES
from .scorer import DealScorer, ScoredDeal
from .sources import (
    JobAnalyzer,
    JobSignal,
    MacroAnalyzer,
    MacroContext,
    NewsAnalyzer,
    NewsSignal,
)

logger = logging.getLogger(__name__)


class IntelligenceScoutAgent(BaseAgent):
    """
    Autonomous agent for identifying potential acquisition targets.

    Capabilities:
    - Monitors news for M&A signals, strategic reviews, and company events
    - Analyzes job posting data for growth/distress signals
    - Incorporates macroeconomic context for market timing
    - Computes composite deal scores with full rationale
    - Generates investment thesis summaries using LLM

    Workflow:
    1. Initialize data source adapters
    2. Gather signals from news, jobs, and macro sources
    3. Score opportunities using weighted algorithm
    4. Enhance with LLM-generated rationale (if available)
    5. Return ranked opportunities with full traceability
    """

    def __init__(
        self,
        target_industries: Optional[list[str]] = None,
        min_score_threshold: float = 3.5,
    ):
        """
        Initialize the IntelligenceScout agent.

        Args:
            target_industries: Preferred industries for the fund
            min_score_threshold: Minimum score to include in results
        """
        super().__init__(
            name="IntelligenceScout",
            description="Identifies acquisition targets from market signals",
            max_iterations=3,
        )

        # Initialize source adapters
        self.news_analyzer = NewsAnalyzer()
        self.job_analyzer = JobAnalyzer()
        self.macro_analyzer = MacroAnalyzer()

        # Initialize scorer
        self.scorer = DealScorer(target_industries=target_industries)
        self.min_score_threshold = min_score_threshold
        self.target_industries = target_industries or []

    def get_system_prompt(self) -> str:
        """System prompt for LLM interactions."""
        return """You are an Investment Intelligence Analyst at a private equity firm.
Your role is to analyze market signals and identify compelling acquisition opportunities.

When analyzing a company, you should:
1. Synthesize news, hiring patterns, and market conditions
2. Identify the core investment thesis
3. Highlight key risks and mitigants
4. Recommend concrete next steps

Be concise but insightful. Focus on actionable intelligence that helps
the deal team decide whether to pursue an opportunity.

Format your analysis as:
- Investment Thesis (2-3 sentences)
- Key Signals (bullet points)
- Key Risks (bullet points)
- Recommended Actions (bullet points)
"""

    def _process_node(self, state: AgentState) -> AgentState:
        """Main processing logic for the Scout agent."""
        state["current_step"] = "process"
        state["iterations"] = state.get("iterations", 0) + 1

        try:
            input_data = state.get("input_data", {})
            mode = input_data.get("mode", "analyze")

            if mode == "analyze":
                # Analyze specific company
                result = self._analyze_company(input_data, state)
            elif mode == "scan":
                # Scan industry for opportunities
                result = self._scan_industry(input_data, state)
            elif mode == "signals":
                # Just fetch recent signals
                result = self._get_signals(input_data, state)
            else:
                state["errors"].append(f"Unknown mode: {mode}")
                return state

            state["output_data"] = result
            state["steps_completed"].append("process")

        except Exception as e:
            logger.error(f"{self.name}: Processing failed: {e}", exc_info=True)
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    def _analyze_company(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Analyze a specific company for deal potential."""
        company_name = input_data.get("company_name")
        if not company_name:
            state["errors"].append("company_name is required for analyze mode")
            return {}

        industry = input_data.get("industry", "")
        sub_sector = input_data.get("sub_sector", "")

        # Use synchronous mock data fetching
        news_signals = self._fetch_news_sync(company_name)
        job_signals = self._fetch_jobs_sync(company_name)
        macro_context = self._fetch_macro_sync()

        # Score the opportunity
        scored_deal = self.scorer.calculate_score(
            company_name=company_name,
            industry=industry,
            sub_sector=sub_sector,
            news_signals=news_signals,
            job_signals=job_signals,
            macro_context=macro_context,
        )

        # Enhance with LLM-generated thesis if available
        if self._client is not None:
            scored_deal = self._enhance_with_llm(
                scored_deal, news_signals, job_signals, macro_context
            )

        # Store extraction for traceability
        extraction_record = {
            "type": "deal_score",
            "company_name": company_name,
            "score": scored_deal.total_score,
            "tier": scored_deal.score_tier,
            "source_count": len(scored_deal.sources),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["extractions"].append(extraction_record)
        state["confidence_scores"]["deal_score"] = min(
            0.95, 0.5 + len(news_signals) * 0.05 + len(job_signals) * 0.03
        )

        return {
            "analysis_type": "company",
            "scored_deal": scored_deal.to_dict(),
            "signal_summary": {
                "news_count": len(news_signals),
                "job_count": len(job_signals),
                "macro_sentiment": macro_context.market_sentiment,
            },
        }

    def _scan_industry(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Scan an industry for potential opportunities."""
        industry = input_data.get("industry")
        limit = input_data.get("limit", 10)

        # Use mock companies if no industry specified
        companies = MOCK_COMPANIES
        if industry:
            companies = [c for c in MOCK_COMPANIES if industry.lower() in c["industry"].lower()]

        # Fetch macro context once (sync)
        macro_context = self._fetch_macro_sync()

        scored_deals = []
        for company in companies[:limit]:
            # Fetch signals for each company (sync)
            news_signals = self._fetch_news_sync(company["name"])
            job_signals = self._fetch_jobs_sync(company["name"])

            # Score
            scored_deal = self.scorer.calculate_score(
                company_name=company["name"],
                industry=company["industry"],
                sub_sector=company["sub_sector"],
                news_signals=news_signals,
                job_signals=job_signals,
                macro_context=macro_context,
                company_profile=company,
            )

            if scored_deal.total_score >= self.min_score_threshold:
                scored_deals.append(scored_deal)

        # Sort by score descending
        scored_deals.sort(key=lambda x: x.total_score, reverse=True)

        # Store extraction records
        for deal in scored_deals:
            state["extractions"].append({
                "type": "deal_score",
                "company_name": deal.company_name,
                "score": deal.total_score,
                "tier": deal.score_tier,
            })

        return {
            "analysis_type": "industry_scan",
            "industry": industry or "all",
            "total_scanned": len(companies),
            "opportunities_found": len(scored_deals),
            "scored_deals": [d.to_dict() for d in scored_deals],
            "macro_context": {
                "sentiment": macro_context.market_sentiment,
                "interest_rate": macro_context.interest_rate,
                "vix": macro_context.vix_index,
            },
        }

    def _get_signals(
        self, input_data: dict[str, Any], state: AgentState
    ) -> dict[str, Any]:
        """Fetch recent market signals without scoring."""
        company_name = input_data.get("company_name")
        industry = input_data.get("industry")

        # Use synchronous mock data fetching
        news_signals = self._fetch_news_sync(company_name)
        job_signals = self._fetch_jobs_sync(company_name)
        macro_context = self._fetch_macro_sync()

        return {
            "analysis_type": "signals",
            "news_signals": [
                {
                    "company": s.company_name,
                    "headline": s.headline,
                    "signal_type": s.signal_type.value,
                    "sentiment": s.sentiment_score,
                    "relevance": s.relevance_score,
                }
                for s in news_signals
            ],
            "job_signals": [
                {
                    "company": s.company_name,
                    "signal_type": s.signal_type.value,
                    "job_title": s.job_title,
                    "posting_count": s.posting_count,
                    "is_leadership": s.is_leadership,
                }
                for s in job_signals
            ],
            "macro_context": {
                "sentiment": macro_context.market_sentiment,
                "gdp_growth": macro_context.gdp_growth,
                "interest_rate": macro_context.interest_rate,
                "unemployment": macro_context.unemployment_rate,
                "vix": macro_context.vix_index,
            },
        }

    def _enhance_with_llm(
        self,
        scored_deal: ScoredDeal,
        news_signals: list[NewsSignal],
        job_signals: list[JobSignal],
        macro_context: MacroContext,
    ) -> ScoredDeal:
        """Enhance scored deal with LLM-generated investment thesis."""
        try:
            # Build context for LLM
            news_summary = "\n".join([
                f"- {s.headline} (sentiment: {s.sentiment_score:.2f})"
                for s in sorted(news_signals, key=lambda x: -x.relevance_score)[:5]
            ])

            job_summary = "\n".join([
                f"- {s.job_title} ({s.posting_count} postings)"
                for s in job_signals if s.is_leadership
            ][:5])

            prompt = f"""Analyze this potential acquisition target:

Company: {scored_deal.company_name}
Industry: {scored_deal.industry} / {scored_deal.sub_sector}
Deal Score: {scored_deal.total_score:.1f}/10 ({scored_deal.score_tier})

Recent News:
{news_summary or "No significant news"}

Leadership Hiring Activity:
{job_summary or "No leadership positions identified"}

Macro Context:
- Market Sentiment: {macro_context.market_sentiment}
- Interest Rate: {macro_context.interest_rate}%
- VIX: {macro_context.vix_index}

Score Components:
{chr(10).join([f"- {c.name}: {c.raw_score:.1f}/10 ({c.rationale})" for c in scored_deal.components])}

Provide your analysis in JSON format:
{{
    "investment_thesis": "2-3 sentence thesis",
    "key_signals": ["signal 1", "signal 2", ...],
    "risks": ["risk 1", "risk 2", ...],
    "recommended_next_steps": ["step 1", "step 2", ...]
}}
"""

            response = self.call_llm(
                messages=[{"role": "user", "content": prompt}],
                system=self.get_system_prompt(),
                max_tokens=1024,
            )

            # Parse response using the helper method
            text = self.get_text_from_response(response)
            if text:
                # Extract JSON from response
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = json.loads(text[json_start:json_end])

                    scored_deal.investment_thesis = analysis.get("investment_thesis", "")
                    if analysis.get("key_signals"):
                        scored_deal.key_signals = analysis["key_signals"]
                    if analysis.get("risks"):
                        scored_deal.risks = analysis["risks"]
                    if analysis.get("recommended_next_steps"):
                        scored_deal.recommended_next_steps = analysis["recommended_next_steps"]

                    logger.info(f"Enhanced {scored_deal.company_name} with LLM thesis")

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
            # Keep algorithmic results, just note the failure
            if not scored_deal.investment_thesis:
                scored_deal.investment_thesis = (
                    f"Algorithmic analysis identified {scored_deal.company_name} as a "
                    f"{scored_deal.score_tier.lower()} opportunity based on {len(scored_deal.key_signals)} signals."
                )

        return scored_deal

    def _fetch_news_sync(self, company_name: Optional[str] = None) -> list[NewsSignal]:
        """Fetch news signals synchronously using mock data."""
        from .mock_data import MOCK_NEWS_SIGNALS

        signals = MOCK_NEWS_SIGNALS.copy()
        if company_name:
            # First try exact/partial match
            matched = [s for s in signals if company_name.lower() in s.company_name.lower()]
            if matched:
                return matched
            # If no match, generate signals for this company using CloudSync as template
            cloudsync_signals = [s for s in signals if "cloudsync" in s.company_name.lower()]
            if cloudsync_signals:
                # Create new signals with the searched company name
                from copy import deepcopy
                generated = []
                for s in cloudsync_signals:
                    new_signal = deepcopy(s)
                    new_signal.company_name = company_name
                    # Modify headlines to use the company name
                    new_signal.headline = s.headline.replace("CloudSync Technologies", company_name)
                    new_signal.summary = s.summary.replace("CloudSync Technologies", company_name).replace("CloudSync", company_name)
                    generated.append(new_signal)
                return generated
        return signals

    def _fetch_jobs_sync(self, company_name: Optional[str] = None) -> list[JobSignal]:
        """Fetch job signals synchronously using mock data."""
        from .mock_data import MOCK_JOB_SIGNALS

        signals = MOCK_JOB_SIGNALS.copy()
        if company_name:
            # First try exact/partial match
            matched = [s for s in signals if company_name.lower() in s.company_name.lower()]
            if matched:
                return matched
            # If no match, generate signals for this company using CloudSync as template
            cloudsync_signals = [s for s in signals if "cloudsync" in s.company_name.lower()]
            if cloudsync_signals:
                from copy import deepcopy
                generated = []
                for s in cloudsync_signals:
                    new_signal = deepcopy(s)
                    new_signal.company_name = company_name
                    generated.append(new_signal)
                return generated
        return signals

    def _fetch_macro_sync(self) -> MacroContext:
        """Fetch macro context synchronously using mock data."""
        from .mock_data import MOCK_MACRO_CONTEXT

        return MOCK_MACRO_CONTEXT

    def _is_processing_complete(self, state: AgentState) -> bool:
        """Check if processing is complete."""
        return bool(state.get("output_data")) or bool(state.get("errors"))

    async def analyze_company(
        self,
        company_name: str,
        industry: str = "",
        sub_sector: str = "",
        deal_id: Optional[UUID] = None,
    ) -> AgentOutput:
        """
        Convenience method to analyze a specific company.

        Args:
            company_name: Name of target company
            industry: Industry sector
            sub_sector: Industry sub-sector
            deal_id: Optional deal ID for context

        Returns:
            AgentOutput with scored deal
        """
        input_data = {
            "mode": "analyze",
            "company_name": company_name,
            "industry": industry,
            "sub_sector": sub_sector,
        }

        output = await self.run(input_data=input_data, deal_id=deal_id)

        # Publish event if deal was scored
        if output.success and output.output_data.get("scored_deal"):
            scored = output.output_data["scored_deal"]
            await self.event_bus.publish(
                event_type=EventType.DEAL_SOURCED,
                deal_id=deal_id,
                agent_name=self.name,
                payload={
                    "company_name": company_name,
                    "score": scored["total_score"],
                    "tier": scored["score_tier"],
                    "key_signals": scored.get("key_signals", []),
                },
            )

        return output

    async def scan_industry(
        self,
        industry: Optional[str] = None,
        limit: int = 10,
    ) -> AgentOutput:
        """
        Convenience method to scan an industry for opportunities.

        Args:
            industry: Industry to scan (None for all)
            limit: Maximum number of companies to scan

        Returns:
            AgentOutput with ranked opportunities
        """
        input_data = {
            "mode": "scan",
            "industry": industry,
            "limit": limit,
        }

        return await self.run(input_data=input_data)

    async def get_market_signals(
        self,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AgentOutput:
        """
        Get recent market signals without scoring.

        Args:
            company_name: Filter to specific company
            industry: Filter to specific industry

        Returns:
            AgentOutput with signal data
        """
        input_data = {
            "mode": "signals",
            "company_name": company_name,
            "industry": industry,
        }

        return await self.run(input_data=input_data)

    async def close(self) -> None:
        """Clean up resources."""
        await self.news_analyzer.close()
        await self.job_analyzer.close()
        await self.macro_analyzer.close()
