"""Deal scoring algorithm for IntelligenceScout agent.

Computes a composite deal score (0-10) based on market signals,
company profile, and macroeconomic context.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from .sources import (
    JobSignal,
    MacroContext,
    NewsSignal,
    SignalStrength,
    SignalType,
    SourceReference,
)

logger = logging.getLogger(__name__)


@dataclass
class ScoreComponent:
    """Individual component of the deal score."""

    name: str
    weight: float  # Percentage weight (0.0 to 1.0)
    raw_score: float  # Score before weighting (0.0 to 10.0)
    weighted_score: float  # Score after weighting
    rationale: str  # Explanation of the score
    signals_used: list[str] = field(default_factory=list)


@dataclass
class ScoredDeal:
    """Complete scored deal with breakdown and sourcing rationale."""

    score_id: UUID = field(default=None)
    company_name: str = ""
    industry: str = ""
    sub_sector: str = ""
    description: str = ""
    revenue: float = 0.0
    ebitda: float = 0.0
    revenue_growth: float = 0.0

    # Overall score (0-10)
    total_score: float = 0.0
    score_tier: str = ""  # "High Priority", "Medium Priority", "Low Priority", "Pass"

    # Component breakdown
    components: list[ScoreComponent] = field(default_factory=list)

    # Sourcing rationale (LLM-generated)
    investment_thesis: str = ""
    key_signals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)

    # Source references for traceability
    sources: list[SourceReference] = field(default_factory=list)
    scored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "score_id": str(self.score_id),
            "id": str(self.score_id), # Alias for UI
            "company_name": self.company_name,
            "industry": self.industry,
            "sub_sector": self.sub_sector,
            "description": self.description,
            "revenue": self.revenue,
            "ebitda": self.ebitda,
            "revenue_growth": self.revenue_growth,
            "total_score": round(self.total_score, 2),
            "score_tier": self.score_tier,
            "components": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "raw_score": round(c.raw_score, 2),
                    "weighted_score": round(c.weighted_score, 2),
                    "rationale": c.rationale,
                    "signals_used": c.signals_used,
                }
                for c in self.components
            ],
            "investment_thesis": self.investment_thesis,
            "key_signals": self.key_signals,
            "risks": self.risks,
            "recommended_next_steps": self.recommended_next_steps,
            "source_count": len(self.sources),
            "scored_at": self.scored_at.isoformat(),
        }


class DealScorer:
    """
    Computes composite deal scores for potential acquisition targets.
    
    Scoring Components (weights sum to 1.0):
    - News Sentiment (30%): Quality and direction of news coverage
    - Growth Signals (25%): Hiring trends, expansion indicators
    - Market Timing (15%): Macro environment favorability
    - Industry Fit (20%): Sector attractiveness for PE
    - Deal Feasibility (10%): Likelihood of actionable opportunity
    """

    # Component weights
    WEIGHTS = {
        "news_sentiment": 0.30,
        "growth_signals": 0.25,
        "market_timing": 0.15,
        "industry_fit": 0.20,
        "deal_feasibility": 0.10,
    }

    # Score tier thresholds
    TIER_THRESHOLDS = {
        "High Priority": 7.5,
        "Medium Priority": 5.5,
        "Low Priority": 3.5,
    }

    # Industry attractiveness for PE (higher = more attractive)
    INDUSTRY_ATTRACTIVENESS = {
        # High attractiveness
        "technology": 8.5,
        "software": 9.0,
        "healthcare": 8.0,
        "healthcare services": 8.5,
        "medical devices": 8.0,
        "business services": 8.0,
        "financial services": 7.5,

        # Moderate attractiveness
        "industrial manufacturing": 6.5,
        "logistics": 7.0,
        "consumer": 6.0,
        "food & beverage": 6.5,
        "education": 6.5,

        # Lower attractiveness (more cyclical/commodity)
        "retail": 4.5,
        "energy": 5.0,
        "real estate": 5.5,
        "hospitality": 4.0,
    }

    # Signal type scoring
    SIGNAL_SCORES = {
        SignalType.PE_INTEREST: 10.0,
        SignalType.STRATEGIC_REVIEW: 9.5,
        SignalType.ACQUISITION_INTEREST: 9.0,
        SignalType.IPO_CONSIDERATION: 8.0,
        SignalType.RESTRUCTURING: 7.5,  # Can be opportunity
        SignalType.LEADERSHIP_CHANGE: 6.5,
        SignalType.EXPANSION: 7.0,
        SignalType.FUNDING: 6.0,
        SignalType.PARTNERSHIP: 5.5,
        SignalType.NEW_PRODUCT: 5.5,
        SignalType.HIRING: 5.0,
        SignalType.EARNINGS: 4.0,
        SignalType.INDUSTRY_TREND: 3.0,
        SignalType.LAYOFFS: 6.0,  # Can indicate distress opportunity
        SignalType.DEBT_ISSUE: 7.0,  # Distress opportunity
        SignalType.MARKET_ENTRY: 5.0,
        SignalType.REGULATORY: 3.0,
    }

    # Signal strength multipliers
    STRENGTH_MULTIPLIERS = {
        SignalStrength.CRITICAL: 1.5,
        SignalStrength.STRONG: 1.2,
        SignalStrength.MODERATE: 1.0,
        SignalStrength.WEAK: 0.7,
    }

    def __init__(self, target_industries: Optional[list[str]] = None):
        """
        Initialize scorer.

        Args:
            target_industries: Optional list of preferred industries
                               (will boost scores for these)
        """
        self.target_industries = [i.lower() for i in (target_industries or [])]

    def calculate_score(
        self,
        company_name: str,
        industry: str,
        sub_sector: str,
        news_signals: list[NewsSignal],
        job_signals: list[JobSignal],
        macro_context: MacroContext,
        company_profile: Optional[dict] = None,
    ) -> ScoredDeal:
        """
        Calculate composite deal score.

        Args:
            company_name: Target company name
            industry: Primary industry sector
            sub_sector: Industry sub-sector
            news_signals: News signals for this company
            job_signals: Job posting signals
            macro_context: Current macroeconomic context
            company_profile: Optional additional company info

        Returns:
            ScoredDeal with full breakdown
        """
        # Extract profile data
        profile = company_profile or {}
        # Convert revenue/ebitda to millions if large numbers
        rev = profile.get("revenue_estimate", 0)
        rev_m = rev / 1_000_000 if rev > 1_000_000 else rev
        
        # Generate deterministic ID
        score_id = uuid5(NAMESPACE_DNS, company_name)
        
        scored_deal = ScoredDeal(
            score_id=score_id,
            company_name=company_name,
            industry=industry,
            sub_sector=sub_sector,
            description=profile.get("description", ""),
            revenue=rev_m,
            ebitda=rev_m * 0.2, # Rough estimate 20% margin if not provided
            revenue_growth=0.15, # Placeholder growth
        )

        # Calculate each component
        components = []

        # 1. News Sentiment Score
        news_score = self._score_news_sentiment(news_signals)
        components.append(news_score)

        # 2. Growth Signals Score
        growth_score = self._score_growth_signals(news_signals, job_signals)
        components.append(growth_score)

        # 3. Market Timing Score
        timing_score = self._score_market_timing(macro_context, industry)
        components.append(timing_score)

        # 4. Industry Fit Score
        industry_score = self._score_industry_fit(industry, sub_sector)
        components.append(industry_score)

        # 5. Deal Feasibility Score
        feasibility_score = self._score_deal_feasibility(news_signals)
        components.append(feasibility_score)

        scored_deal.components = components

        # Calculate total weighted score
        total = sum(c.weighted_score for c in components)
        scored_deal.total_score = min(10.0, max(0.0, total))

        # Determine tier
        scored_deal.score_tier = self._get_tier(scored_deal.total_score)

        # Collect sources
        for signal in news_signals:
            scored_deal.sources.append(signal.source)
        for signal in job_signals:
            scored_deal.sources.append(signal.source)

        # Generate key signals summary
        scored_deal.key_signals = self._extract_key_signals(news_signals, job_signals)

        # Basic risk identification
        scored_deal.risks = self._identify_risks(news_signals, job_signals, macro_context)

        # Recommended next steps based on tier
        scored_deal.recommended_next_steps = self._get_recommended_steps(
            scored_deal.score_tier, news_signals
        )

        logger.info(
            f"Scored {company_name}: {scored_deal.total_score:.2f} ({scored_deal.score_tier})"
        )

        return scored_deal

    def _score_news_sentiment(self, news_signals: list[NewsSignal]) -> ScoreComponent:
        """Score based on news sentiment and signal quality."""
        if not news_signals:
            return ScoreComponent(
                name="News Sentiment",
                weight=self.WEIGHTS["news_sentiment"],
                raw_score=5.0,  # Neutral if no news
                weighted_score=5.0 * self.WEIGHTS["news_sentiment"],
                rationale="No recent news signals found",
            )

        # Calculate weighted average sentiment
        total_weight = 0.0
        weighted_sentiment = 0.0
        signals_used = []

        for signal in news_signals:
            # Weight by signal strength and relevance
            multiplier = self.STRENGTH_MULTIPLIERS.get(signal.signal_strength, 1.0)
            signal_weight = signal.relevance_score * multiplier

            # Convert sentiment (-1 to 1) to score (0 to 10)
            sentiment_score = (signal.sentiment_score + 1) * 5

            weighted_sentiment += sentiment_score * signal_weight
            total_weight += signal_weight
            signals_used.append(f"{signal.headline[:50]}...")

        if total_weight > 0:
            raw_score = weighted_sentiment / total_weight
        else:
            raw_score = 5.0

        # Boost for high-value signal types
        ma_signals = [s for s in news_signals if s.signal_type in {
            SignalType.PE_INTEREST, SignalType.STRATEGIC_REVIEW,
            SignalType.ACQUISITION_INTEREST
        }]
        if ma_signals:
            raw_score = min(10.0, raw_score + 1.5)

        avg_sentiment = sum(s.sentiment_score for s in news_signals) / len(news_signals)
        sentiment_desc = "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "mixed"

        return ScoreComponent(
            name="News Sentiment",
            weight=self.WEIGHTS["news_sentiment"],
            raw_score=raw_score,
            weighted_score=raw_score * self.WEIGHTS["news_sentiment"],
            rationale=f"{len(news_signals)} news signals with {sentiment_desc} sentiment",
            signals_used=signals_used[:5],  # Top 5
        )

    def _score_growth_signals(
        self, news_signals: list[NewsSignal], job_signals: list[JobSignal]
    ) -> ScoreComponent:
        """Score based on growth/hiring indicators."""
        signals_used = []
        raw_score = 5.0  # Neutral baseline

        # Analyze hiring trend
        total_postings = sum(max(0, s.posting_count) for s in job_signals)
        leadership_hires = sum(1 for s in job_signals if s.is_leadership)
        layoffs = [s for s in job_signals if s.signal_type == SignalType.LAYOFFS]

        if total_postings > 30:
            raw_score += 2.0
            signals_used.append(f"Aggressive hiring: {total_postings} open positions")
        elif total_postings > 10:
            raw_score += 1.0
            signals_used.append(f"Active hiring: {total_postings} positions")

        if leadership_hires >= 2:
            raw_score += 1.0
            signals_used.append(f"{leadership_hires} leadership positions open")

        if layoffs:
            raw_score -= 0.5  # Slight negative, but could be turnaround opportunity
            signals_used.append("Recent layoff activity detected")

        # Analyze growth signals from news
        expansion_news = [
            s for s in news_signals
            if s.signal_type in {SignalType.EXPANSION, SignalType.MARKET_ENTRY, SignalType.FUNDING}
        ]
        if expansion_news:
            raw_score += len(expansion_news) * 0.5
            signals_used.append(f"{len(expansion_news)} expansion-related news items")

        raw_score = min(10.0, max(0.0, raw_score))

        return ScoreComponent(
            name="Growth Signals",
            weight=self.WEIGHTS["growth_signals"],
            raw_score=raw_score,
            weighted_score=raw_score * self.WEIGHTS["growth_signals"],
            rationale=f"Growth analysis based on {len(job_signals)} job signals, {len(news_signals)} news",
            signals_used=signals_used,
        )

    def _score_market_timing(
        self, macro_context: MacroContext, industry: str
    ) -> ScoreComponent:
        """Score based on macroeconomic conditions and sector timing."""
        raw_score = 5.0  # Neutral baseline
        signals_used = []

        # Market sentiment
        if macro_context.market_sentiment == "bullish":
            raw_score += 1.0
            signals_used.append("Bullish market sentiment")
        elif macro_context.market_sentiment == "bearish":
            raw_score -= 1.0
            signals_used.append("Bearish market sentiment")

        # Interest rates (higher = harder to finance deals)
        if macro_context.interest_rate:
            if macro_context.interest_rate < 3.0:
                raw_score += 1.0
                signals_used.append("Favorable interest rate environment")
            elif macro_context.interest_rate > 6.0:
                raw_score -= 1.0
                signals_used.append("High interest rate environment")

        # VIX (volatility)
        if macro_context.vix_index:
            if macro_context.vix_index < 15:
                raw_score += 0.5
                signals_used.append("Low market volatility (VIX)")
            elif macro_context.vix_index > 30:
                raw_score -= 1.0
                signals_used.append("High market volatility (VIX)")

        # Sector-specific indicators
        industry_lower = industry.lower()
        sector_score = macro_context.sector_indicators.get(industry_lower)
        if sector_score:
            if sector_score > 0.6:
                raw_score += 1.0
                signals_used.append(f"Strong sector outlook for {industry}")
            elif sector_score < 0.3:
                raw_score -= 0.5
                signals_used.append(f"Weak sector outlook for {industry}")

        raw_score = min(10.0, max(0.0, raw_score))

        return ScoreComponent(
            name="Market Timing",
            weight=self.WEIGHTS["market_timing"],
            raw_score=raw_score,
            weighted_score=raw_score * self.WEIGHTS["market_timing"],
            rationale=f"Macro analysis: {macro_context.market_sentiment} sentiment",
            signals_used=signals_used,
        )

    def _score_industry_fit(self, industry: str, sub_sector: str) -> ScoreComponent:
        """Score based on industry attractiveness for PE."""
        signals_used = []

        # Look up base attractiveness
        industry_lower = industry.lower()
        sub_sector_lower = sub_sector.lower()

        raw_score = self.INDUSTRY_ATTRACTIVENESS.get(
            sub_sector_lower,
            self.INDUSTRY_ATTRACTIVENESS.get(industry_lower, 5.5)
        )
        signals_used.append(f"Industry: {industry}/{sub_sector}")

        # Boost if in target industries
        if self.target_industries:
            if industry_lower in self.target_industries or sub_sector_lower in self.target_industries:
                raw_score = min(10.0, raw_score + 1.0)
                signals_used.append("Matches fund target industries")

        return ScoreComponent(
            name="Industry Fit",
            weight=self.WEIGHTS["industry_fit"],
            raw_score=raw_score,
            weighted_score=raw_score * self.WEIGHTS["industry_fit"],
            rationale=f"PE attractiveness assessment for {industry}",
            signals_used=signals_used,
        )

    def _score_deal_feasibility(self, news_signals: list[NewsSignal]) -> ScoreComponent:
        """Score likelihood of actionable deal opportunity."""
        signals_used = []
        raw_score = 5.0  # Neutral baseline

        # High-value deal signals
        ma_signals = [
            s for s in news_signals
            if s.signal_type in {
                SignalType.PE_INTEREST,
                SignalType.STRATEGIC_REVIEW,
                SignalType.ACQUISITION_INTEREST,
                SignalType.IPO_CONSIDERATION,
            }
        ]

        if ma_signals:
            # Strong indicator of actionable opportunity
            best_signal = max(ma_signals, key=lambda s: self.SIGNAL_SCORES.get(s.signal_type, 0))
            raw_score = self.SIGNAL_SCORES.get(best_signal.signal_type, 7.0)
            signals_used.append(f"Active deal signal: {best_signal.signal_type.value}")

        # Leadership change can indicate transition opportunity
        leadership_signals = [
            s for s in news_signals
            if s.signal_type == SignalType.LEADERSHIP_CHANGE
        ]
        if leadership_signals and not ma_signals:
            raw_score = max(raw_score, 6.5)
            signals_used.append("Leadership transition may create opportunity")

        # Distress signals can indicate restructuring opportunity
        distress_signals = [
            s for s in news_signals
            if s.signal_type in {SignalType.RESTRUCTURING, SignalType.LAYOFFS, SignalType.DEBT_ISSUE}
        ]
        if distress_signals and not ma_signals:
            raw_score = max(raw_score, 6.0)
            signals_used.append("Distress situation may create opportunity")

        if not signals_used:
            signals_used.append("No specific deal triggers identified")

        return ScoreComponent(
            name="Deal Feasibility",
            weight=self.WEIGHTS["deal_feasibility"],
            raw_score=raw_score,
            weighted_score=raw_score * self.WEIGHTS["deal_feasibility"],
            rationale=f"Based on {len(ma_signals)} M&A-related signals",
            signals_used=signals_used,
        )

    def _get_tier(self, score: float) -> str:
        """Determine score tier from total score."""
        if score >= self.TIER_THRESHOLDS["High Priority"]:
            return "High Priority"
        elif score >= self.TIER_THRESHOLDS["Medium Priority"]:
            return "Medium Priority"
        elif score >= self.TIER_THRESHOLDS["Low Priority"]:
            return "Low Priority"
        return "Pass"

    def _extract_key_signals(
        self, news_signals: list[NewsSignal], job_signals: list[JobSignal]
    ) -> list[str]:
        """Extract most important signals for summary."""
        key_signals = []

        # Top news by relevance
        sorted_news = sorted(news_signals, key=lambda s: s.relevance_score, reverse=True)
        for signal in sorted_news[:3]:
            key_signals.append(f"[NEWS] {signal.headline}")

        # Leadership changes from jobs
        for signal in job_signals:
            if signal.is_leadership:
                key_signals.append(f"[HIRING] {signal.job_title} opening")

        return key_signals[:5]

    def _identify_risks(
        self,
        news_signals: list[NewsSignal],
        job_signals: list[JobSignal],
        macro_context: MacroContext,
    ) -> list[str]:
        """Identify key risks from signals."""
        risks = []

        # Negative news sentiment
        negative_news = [s for s in news_signals if s.sentiment_score < -0.3]
        if len(negative_news) > 2:
            risks.append("Multiple negative news articles detected")

        # Layoffs
        layoffs = [s for s in job_signals if s.signal_type == SignalType.LAYOFFS]
        if layoffs:
            risks.append("Recent workforce reductions")

        # Leadership instability
        ceo_search = [s for s in job_signals if "ceo" in s.job_title.lower()]
        if ceo_search:
            risks.append("CEO position open - leadership uncertainty")

        # Macro risks
        if macro_context.vix_index and macro_context.vix_index > 25:
            risks.append("Elevated market volatility")
        if macro_context.interest_rate and macro_context.interest_rate > 6:
            risks.append("High interest rate environment may affect deal financing")

        # Strategic review signals (can be positive but also risk)
        strategic_signals = [s for s in news_signals if s.signal_type in {
            SignalType.STRATEGIC_REVIEW, SignalType.PE_INTEREST
        }]
        if strategic_signals:
            risks.append("Active sale process - potential competition from other bidders")
            risks.append("Limited exclusivity window - need to move quickly")

        # If no risks found, add standard due diligence concerns
        if not risks:
            risks = [
                "Customer concentration risk - needs verification",
                "Management team retention post-acquisition",
                "Technology/IP ownership to be confirmed in diligence",
            ]

        return risks[:5]  # Limit to top 5 risks

    def _get_recommended_steps(
        self, tier: str, news_signals: list[NewsSignal]
    ) -> list[str]:
        """Get recommended next steps based on score tier."""
        if tier == "High Priority":
            steps = [
                "Initiate immediate outreach to management/advisors",
                "Begin preliminary financial analysis",
                "Identify warm paths through network",
                "Schedule deal team briefing",
            ]
            # Check for active process
            active_process = any(
                s.signal_type in {SignalType.STRATEGIC_REVIEW, SignalType.PE_INTEREST}
                for s in news_signals
            )
            if active_process:
                steps.insert(0, "URGENT: Active process detected - expedite outreach")
            return steps

        elif tier == "Medium Priority":
            return [
                "Add to monitoring watchlist",
                "Conduct initial desktop research",
                "Identify potential contacts",
                "Review in next pipeline meeting",
            ]

        elif tier == "Low Priority":
            return [
                "Add to long-term monitoring",
                "Revisit if situation changes",
                "Gather industry context",
            ]

        else:  # Pass
            return [
                "Pass - does not meet current investment criteria",
                "Consider for future review if thesis changes",
            ]
