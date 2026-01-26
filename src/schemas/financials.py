"""Financial schemas with Decimal precision and traceability."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class BoundingBox(BaseModel):
    """Bounding box coordinates for PDF extraction tracing."""

    x0: float = Field(description="Left coordinate")
    y0: float = Field(description="Top coordinate")
    x1: float = Field(description="Right coordinate")
    y1: float = Field(description="Bottom coordinate")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


class SourceReference(BaseModel):
    """Reference to source document for traceability."""

    document_id: UUID
    document_name: str
    page_number: int
    bounding_box: Optional[BoundingBox] = None
    text_snippet: str = Field(default="", max_length=500)
    url: Optional[str] = None


class TracedValue(BaseModel):
    """A numeric value with full source traceability."""

    value: Decimal = Field(decimal_places=2)
    currency: Currency = Currency.USD
    source: SourceReference
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    verified_by: Optional[str] = None
    verified_at: Optional[date] = None

    model_config = ConfigDict()

    @field_serializer("value")
    @staticmethod
    def serialize_decimal(v: Decimal) -> str:
        return str(v)


class EBITDAAdjustment(BaseModel):
    """EBITDA adjustment with justification and tracing."""

    adjustment_id: UUID
    description: str
    amount: Decimal
    category: str  # e.g., "one-time", "run-rate", "synergy"
    source: SourceReference
    approved_by: Optional[str] = None


class TracedFinancials(BaseModel):
    """Complete financials with source tracing for each value."""

    fiscal_year: int
    fiscal_period: str = "FY"  # FY, Q1, Q2, etc.

    # Income Statement
    revenue: Optional[TracedValue] = None
    gross_profit: Optional[TracedValue] = None
    ebitda: Optional[TracedValue] = None
    ebit: Optional[TracedValue] = None
    net_income: Optional[TracedValue] = None

    # Balance Sheet
    total_assets: Optional[TracedValue] = None
    total_liabilities: Optional[TracedValue] = None
    total_equity: Optional[TracedValue] = None
    cash: Optional[TracedValue] = None
    total_debt: Optional[TracedValue] = None

    # Cash Flow
    operating_cash_flow: Optional[TracedValue] = None
    capex: Optional[TracedValue] = None
    free_cash_flow: Optional[TracedValue] = None

    # Calculated Metrics (no source - derived)
    revenue_growth: Optional[Decimal] = None
    ebitda_margin: Optional[Decimal] = None
    net_debt: Optional[Decimal] = None


class LBOAssumptions(BaseModel):
    """LBO model input assumptions."""

    entry_multiple: Decimal = Field(description="EV/EBITDA entry multiple")
    exit_multiple: Decimal = Field(description="EV/EBITDA exit multiple")
    hold_period_years: int = Field(ge=1, le=10)

    # Capital Structure
    senior_debt_multiple: Decimal = Field(description="Senior debt / EBITDA")
    sub_debt_multiple: Decimal = Field(default=Decimal("0"))
    equity_contribution: Decimal = Field(description="Equity as % of sources")

    # Interest Rates
    senior_rate: Decimal = Field(description="Senior debt interest rate")
    sub_rate: Decimal = Field(default=Decimal("0"))

    # Operating Assumptions
    revenue_growth_rates: list[Decimal] = Field(default_factory=list)
    ebitda_margins: list[Decimal] = Field(default_factory=list)
    capex_percent_revenue: Decimal = Field(default=Decimal("0.03"))
    nwc_percent_revenue: Decimal = Field(default=Decimal("0.10"))


class LBOModelOutput(BaseModel):
    """LBO model output metrics."""

    # Returns
    irr: Decimal = Field(description="Internal Rate of Return")
    moic: Decimal = Field(description="Multiple on Invested Capital")
    equity_value_entry: Decimal
    equity_value_exit: Decimal

    # Sensitivity
    irr_sensitivity: dict[str, list[Decimal]] = Field(
        default_factory=dict,
        description="IRR sensitivity to entry/exit multiples",
    )

    # Sources & Uses
    total_sources: Decimal
    total_uses: Decimal
    sources_breakdown: dict[str, Decimal]
    uses_breakdown: dict[str, Decimal]

    # Debt Schedule Summary
    entry_leverage: Decimal
    exit_leverage: Decimal
    min_cash_balance: Decimal

    # Model metadata
    assumptions: LBOAssumptions
    generated_at: date
    generated_by: str = "QuantitativeStrategist"


class SensitivityTable(BaseModel):
    """2D sensitivity analysis table."""

    metric: str  # "IRR" or "MOIC"
    row_variable: str  # e.g., "entry_multiple"
    col_variable: str  # e.g., "exit_multiple"
    row_values: list[Decimal]
    col_values: list[Decimal]
    matrix: list[list[Decimal]]  # row_values x col_values
