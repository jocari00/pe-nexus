"""Data source adapters for IntelligenceScout agent.

Provides adapters for news, job postings, and macroeconomic data
to identify potential acquisition targets.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Types of market signals."""

    # Growth signals
    EXPANSION = "expansion"
    HIRING = "hiring"
    FUNDING = "funding"
    PARTNERSHIP = "partnership"
    NEW_PRODUCT = "new_product"
    MARKET_ENTRY = "market_entry"

    # Distress signals
    LAYOFFS = "layoffs"
    RESTRUCTURING = "restructuring"
    LEADERSHIP_CHANGE = "leadership_change"
    DEBT_ISSUE = "debt_issue"

    # M&A signals
    ACQUISITION_INTEREST = "acquisition_interest"
    STRATEGIC_REVIEW = "strategic_review"
    IPO_CONSIDERATION = "ipo_consideration"
    PE_INTEREST = "pe_interest"

    # Neutral/informational
    EARNINGS = "earnings"
    INDUSTRY_TREND = "industry_trend"
    REGULATORY = "regulatory"


class SignalStrength(str, Enum):
    """Strength/importance of a signal."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class SourceReference:
    """Reference to original data source."""

    source_id: UUID = field(default_factory=uuid4)
    source_type: str = ""  # news, job_board, fred, etc.
    source_name: str = ""  # NewsAPI, LinkedIn, FRED, etc.
    url: Optional[str] = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data: dict = field(default_factory=dict)


@dataclass
class NewsSignal:
    """Signal extracted from news article."""

    signal_id: UUID = field(default_factory=uuid4)
    company_name: str = ""
    headline: str = ""
    summary: str = ""
    signal_type: SignalType = SignalType.INDUSTRY_TREND
    signal_strength: SignalStrength = SignalStrength.MODERATE
    sentiment_score: float = 0.0  # -1.0 to 1.0
    published_at: Optional[datetime] = None
    source: SourceReference = field(default_factory=SourceReference)
    keywords: list[str] = field(default_factory=list)
    relevance_score: float = 0.0  # 0.0 to 1.0


@dataclass
class JobSignal:
    """Signal extracted from job posting data."""

    signal_id: UUID = field(default_factory=uuid4)
    company_name: str = ""
    signal_type: SignalType = SignalType.HIRING
    signal_strength: SignalStrength = SignalStrength.MODERATE
    job_title: str = ""
    department: str = ""
    location: str = ""
    posting_count: int = 1
    is_leadership: bool = False  # C-suite, VP, Director level
    source: SourceReference = field(default_factory=SourceReference)


@dataclass
class MacroIndicator:
    """Macroeconomic indicator from FRED."""

    indicator_id: str = ""  # FRED series ID
    name: str = ""
    value: Decimal = Decimal("0")
    previous_value: Optional[Decimal] = None
    change_percent: Optional[float] = None
    observation_date: Optional[datetime] = None
    frequency: str = ""  # daily, monthly, quarterly
    source: SourceReference = field(default_factory=SourceReference)


@dataclass
class MacroContext:
    """Overall macroeconomic context for deal scoring."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    gdp_growth: Optional[float] = None
    interest_rate: Optional[float] = None
    unemployment_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
    vix_index: Optional[float] = None
    market_sentiment: str = "neutral"  # bullish, bearish, neutral
    sector_indicators: dict[str, float] = field(default_factory=dict)
    indicators: list[MacroIndicator] = field(default_factory=list)


class BaseSourceAdapter(ABC):
    """Abstract base for data source adapters."""

    def __init__(self, name: str):
        self.name = name
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client (lazy initialization)."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def fetch(self, **kwargs) -> Any:
        """Fetch data from source."""
        pass

    def _create_source_ref(
        self, source_type: str, url: Optional[str] = None, raw_data: Optional[dict] = None
    ) -> SourceReference:
        """Create source reference for traceability."""
        return SourceReference(
            source_type=source_type,
            source_name=self.name,
            url=url,
            raw_data=raw_data or {},
        )


class NewsAnalyzer(BaseSourceAdapter):
    """
    Analyzes news articles for M&A and deal signals.

    Uses NewsAPI when available, falls back to mock data.
    """

    # Keywords for signal classification
    MA_KEYWORDS = {
        "acquisition", "acquire", "merger", "merge", "buyout",
        "takeover", "strategic review", "exploring options",
        "sale process", "seeking buyers", "private equity",
    }
    GROWTH_KEYWORDS = {
        "expansion", "expand", "growth", "growing", "hiring",
        "new market", "launch", "partnership", "funding", "raised",
        "investment", "ipo", "going public",
    }
    DISTRESS_KEYWORDS = {
        "layoff", "restructuring", "bankruptcy", "default",
        "debt", "struggling", "downsizing", "cost cutting",
        "leadership change", "ceo departure", "resign",
    }

    def __init__(self):
        super().__init__("NewsAPI")
        self.api_key = settings.newsapi_key
        self.base_url = "https://newsapi.org/v2"

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def fetch(
        self,
        query: Optional[str] = None,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
        days_back: int = 7,
    ) -> list[NewsSignal]:
        """
        Fetch and analyze news articles.

        Args:
            query: Search query
            company_name: Specific company to search
            industry: Industry sector to filter
            days_back: How many days back to search

        Returns:
            List of NewsSignal objects
        """
        if not self.is_available:
            logger.info("NewsAPI not configured, using mock data")
            return await self._get_mock_signals(company_name, industry)

        try:
            # Build search query
            search_terms = []
            if query:
                search_terms.append(query)
            if company_name:
                search_terms.append(f'"{company_name}"')
            if industry:
                search_terms.append(industry)

            # Add M&A keywords if no specific query
            if not query and not company_name:
                search_terms.append("(acquisition OR merger OR private equity)")

            q = " AND ".join(search_terms) if search_terms else "private equity acquisition"

            response = await self.client.get(
                f"{self.base_url}/everything",
                params={
                    "q": q,
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": 50,
                    "apiKey": self.api_key,
                },
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_articles(data.get("articles", []))

        except httpx.HTTPError as e:
            logger.error(f"NewsAPI error: {e}")
            return await self._get_mock_signals(company_name, industry)

    def _parse_articles(self, articles: list[dict]) -> list[NewsSignal]:
        """Parse API response into NewsSignal objects."""
        signals = []

        for article in articles:
            headline = article.get("title", "")
            description = article.get("description", "") or ""
            content = article.get("content", "") or ""
            full_text = f"{headline} {description} {content}".lower()

            # Extract company name (simplified - real impl would use NER)
            company_name = self._extract_company_name(headline, description)
            if not company_name:
                continue

            # Classify signal
            signal_type, strength = self._classify_signal(full_text)

            # Calculate sentiment (simplified)
            sentiment = self._calculate_sentiment(full_text)

            # Parse published date
            published_at = None
            if article.get("publishedAt"):
                try:
                    published_at = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            signal = NewsSignal(
                company_name=company_name,
                headline=headline,
                summary=description[:500] if description else "",
                signal_type=signal_type,
                signal_strength=strength,
                sentiment_score=sentiment,
                published_at=published_at,
                source=self._create_source_ref(
                    "news",
                    url=article.get("url"),
                    raw_data={"source": article.get("source", {}).get("name")},
                ),
                keywords=self._extract_keywords(full_text),
                relevance_score=self._calculate_relevance(full_text),
            )
            signals.append(signal)

        return signals

    def _extract_company_name(self, headline: str, description: str) -> Optional[str]:
        """Extract company name from article (simplified)."""
        # In production, use NER model
        # For now, look for patterns like "Company X announces..."
        text = f"{headline} {description}"

        # Simple heuristic: look for capitalized words before action verbs
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in {"announces", "reports", "plans", "seeks", "explores"}:
                # Look backward for company name
                company_parts = []
                for j in range(max(0, i - 3), i):
                    if words[j][0].isupper():
                        company_parts.append(words[j])
                if company_parts:
                    return " ".join(company_parts).strip(",:;")

        return None

    def _classify_signal(self, text: str) -> tuple[SignalType, SignalStrength]:
        """Classify the type and strength of signal."""
        text_lower = text.lower()

        # Check M&A signals first (highest priority)
        ma_count = sum(1 for kw in self.MA_KEYWORDS if kw in text_lower)
        if ma_count >= 2:
            return SignalType.ACQUISITION_INTEREST, SignalStrength.STRONG
        if ma_count >= 1:
            return SignalType.STRATEGIC_REVIEW, SignalStrength.MODERATE

        # Check distress signals
        distress_count = sum(1 for kw in self.DISTRESS_KEYWORDS if kw in text_lower)
        if distress_count >= 2:
            if "restructuring" in text_lower:
                return SignalType.RESTRUCTURING, SignalStrength.STRONG
            if "layoff" in text_lower:
                return SignalType.LAYOFFS, SignalStrength.MODERATE
            return SignalType.LEADERSHIP_CHANGE, SignalStrength.MODERATE

        # Check growth signals
        growth_count = sum(1 for kw in self.GROWTH_KEYWORDS if kw in text_lower)
        if growth_count >= 2:
            if "expansion" in text_lower or "new market" in text_lower:
                return SignalType.EXPANSION, SignalStrength.MODERATE
            if "funding" in text_lower or "raised" in text_lower:
                return SignalType.FUNDING, SignalStrength.MODERATE
            return SignalType.HIRING, SignalStrength.WEAK

        return SignalType.INDUSTRY_TREND, SignalStrength.WEAK

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (simplified lexicon-based)."""
        positive_words = {
            "growth", "expand", "profit", "success", "strong",
            "increase", "gain", "positive", "opportunity", "innovative",
        }
        negative_words = {
            "loss", "decline", "struggle", "layoff", "debt",
            "bankruptcy", "fail", "weak", "concern", "risk",
        }

        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract relevant keywords from text."""
        all_keywords = self.MA_KEYWORDS | self.GROWTH_KEYWORDS | self.DISTRESS_KEYWORDS
        text_lower = text.lower()
        return [kw for kw in all_keywords if kw in text_lower]

    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score for PE deal sourcing."""
        text_lower = text.lower()

        score = 0.0

        # M&A keywords are most relevant
        ma_count = sum(1 for kw in self.MA_KEYWORDS if kw in text_lower)
        score += ma_count * 0.15

        # Growth/distress signals are somewhat relevant
        other_count = sum(
            1 for kw in (self.GROWTH_KEYWORDS | self.DISTRESS_KEYWORDS)
            if kw in text_lower
        )
        score += other_count * 0.05

        return min(1.0, score)

    async def _get_mock_signals(
        self,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> list[NewsSignal]:
        """Return mock news signals for demo/testing."""
        from .mock_data import MOCK_NEWS_SIGNALS

        signals = MOCK_NEWS_SIGNALS.copy()

        if company_name:
            signals = [s for s in signals if company_name.lower() in s.company_name.lower()]

        return signals


class JobAnalyzer(BaseSourceAdapter):
    """
    Analyzes job posting data for hiring/layoff signals.

    Uses mock data since LinkedIn/Indeed APIs require enterprise subscriptions.
    """

    LEADERSHIP_TITLES = {
        "ceo", "cfo", "cto", "coo", "cmo", "cpo",
        "chief", "president", "vp", "vice president",
        "director", "head of", "general manager",
    }

    def __init__(self):
        super().__init__("JobAnalyzer")

    async def fetch(
        self,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
    ) -> list[JobSignal]:
        """
        Fetch job signals for a company or industry.

        Note: Uses mock data as real job APIs require paid subscriptions.
        """
        from .mock_data import MOCK_JOB_SIGNALS

        signals = MOCK_JOB_SIGNALS.copy()

        if company_name:
            signals = [s for s in signals if company_name.lower() in s.company_name.lower()]

        return signals

    def analyze_hiring_trend(self, signals: list[JobSignal]) -> dict[str, Any]:
        """Analyze hiring patterns from job signals."""
        if not signals:
            return {"trend": "unknown", "leadership_changes": 0, "total_postings": 0}

        total = sum(s.posting_count for s in signals)
        leadership = sum(1 for s in signals if s.is_leadership)

        # Determine trend
        if total > 20:
            trend = "aggressive_growth"
        elif total > 10:
            trend = "moderate_growth"
        elif total > 0:
            trend = "stable"
        else:
            trend = "contraction"

        return {
            "trend": trend,
            "leadership_changes": leadership,
            "total_postings": total,
            "departments": list({s.department for s in signals}),
        }


class MacroAnalyzer(BaseSourceAdapter):
    """
    Fetches macroeconomic indicators from FRED API.

    Provides market timing context for deal sourcing decisions.
    """

    # Key FRED series for PE deal context
    FRED_SERIES = {
        "GDP": "GDP",  # Gross Domestic Product
        "UNRATE": "UNRATE",  # Unemployment Rate
        "FEDFUNDS": "FEDFUNDS",  # Federal Funds Rate
        "CPIAUCSL": "CPIAUCSL",  # Consumer Price Index (Inflation)
        "VIXCLS": "VIXCLS",  # VIX Index
        "SP500": "SP500",  # S&P 500
        "INDPRO": "INDPRO",  # Industrial Production Index
    }

    def __init__(self):
        super().__init__("FRED")
        self.api_key = settings.fred_api_key
        self.base_url = "https://api.stlouisfed.org/fred"

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def fetch(self, series_ids: Optional[list[str]] = None) -> MacroContext:
        """
        Fetch macroeconomic context from FRED.

        Args:
            series_ids: Specific FRED series to fetch (defaults to key indicators)

        Returns:
            MacroContext with current economic indicators
        """
        if not self.is_available:
            logger.info("FRED API not configured, using mock data")
            return await self._get_mock_context()

        series = series_ids or list(self.FRED_SERIES.values())
        indicators = []

        for series_id in series:
            try:
                indicator = await self._fetch_series(series_id)
                if indicator:
                    indicators.append(indicator)
            except Exception as e:
                logger.warning(f"Failed to fetch FRED series {series_id}: {e}")

        return self._build_context(indicators)

    async def _fetch_series(self, series_id: str) -> Optional[MacroIndicator]:
        """Fetch a single FRED series."""
        try:
            response = await self.client.get(
                f"{self.base_url}/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "limit": 2,
                    "sort_order": "desc",
                },
            )
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            if not observations:
                return None

            latest = observations[0]
            previous = observations[1] if len(observations) > 1 else None

            value = Decimal(latest["value"]) if latest["value"] != "." else Decimal("0")
            prev_value = None
            change = None

            if previous and previous["value"] != ".":
                prev_value = Decimal(previous["value"])
                if prev_value != 0:
                    change = float((value - prev_value) / prev_value * 100)

            return MacroIndicator(
                indicator_id=series_id,
                name=series_id,
                value=value,
                previous_value=prev_value,
                change_percent=change,
                observation_date=datetime.fromisoformat(latest["date"]),
                source=self._create_source_ref(
                    "fred",
                    url=f"https://fred.stlouisfed.org/series/{series_id}",
                ),
            )

        except httpx.HTTPError as e:
            logger.error(f"FRED API error for {series_id}: {e}")
            return None

    def _build_context(self, indicators: list[MacroIndicator]) -> MacroContext:
        """Build MacroContext from indicators."""
        context = MacroContext(indicators=indicators)

        # Map indicators to context fields
        for ind in indicators:
            if ind.indicator_id == "GDP":
                context.gdp_growth = ind.change_percent
            elif ind.indicator_id == "FEDFUNDS":
                context.interest_rate = float(ind.value)
            elif ind.indicator_id == "UNRATE":
                context.unemployment_rate = float(ind.value)
            elif ind.indicator_id == "CPIAUCSL":
                context.inflation_rate = ind.change_percent
            elif ind.indicator_id == "VIXCLS":
                context.vix_index = float(ind.value)

        # Determine market sentiment
        context.market_sentiment = self._assess_sentiment(context)

        return context

    def _assess_sentiment(self, context: MacroContext) -> str:
        """Assess overall market sentiment from indicators."""
        bullish_signals = 0
        bearish_signals = 0

        if context.gdp_growth and context.gdp_growth > 2.0:
            bullish_signals += 1
        elif context.gdp_growth and context.gdp_growth < 0:
            bearish_signals += 1

        if context.vix_index and context.vix_index < 20:
            bullish_signals += 1
        elif context.vix_index and context.vix_index > 30:
            bearish_signals += 1

        if context.unemployment_rate and context.unemployment_rate < 5:
            bullish_signals += 1
        elif context.unemployment_rate and context.unemployment_rate > 7:
            bearish_signals += 1

        if bullish_signals > bearish_signals:
            return "bullish"
        elif bearish_signals > bullish_signals:
            return "bearish"
        return "neutral"

    async def _get_mock_context(self) -> MacroContext:
        """Return mock macro context for demo/testing."""
        from .mock_data import MOCK_MACRO_CONTEXT

        return MOCK_MACRO_CONTEXT
