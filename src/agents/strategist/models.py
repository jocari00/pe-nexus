"""Financial models for the QuantStrategist agent.

This module provides LBO modeling, IRR/MOIC calculations, and sensitivity analysis.
Uses Decimal for financial precision.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def to_decimal(value) -> Decimal:
    """Convert a value to Decimal with proper handling."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


@dataclass
class SourcesAndUses:
    """Sources and Uses of funds for the transaction."""
    # Sources
    equity: Decimal
    senior_debt: Decimal
    subordinated_debt: Decimal = Decimal("0")
    seller_note: Decimal = Decimal("0")

    # Uses
    purchase_price: Decimal = Decimal("0")
    transaction_fees: Decimal = Decimal("0")
    debt_financing_fees: Decimal = Decimal("0")

    def total_sources(self) -> Decimal:
        return self.equity + self.senior_debt + self.subordinated_debt + self.seller_note

    def total_uses(self) -> Decimal:
        return self.purchase_price + self.transaction_fees + self.debt_financing_fees

    def equity_percentage(self) -> Decimal:
        if self.total_sources() == 0:
            return Decimal("0")
        return (self.equity / self.total_sources() * 100).quantize(Decimal("0.1"))

    def debt_percentage(self) -> Decimal:
        if self.total_sources() == 0:
            return Decimal("0")
        total_debt = self.senior_debt + self.subordinated_debt + self.seller_note
        return (total_debt / self.total_sources() * 100).quantize(Decimal("0.1"))

    def to_dict(self) -> dict:
        return {
            "sources": {
                "equity": float(self.equity),
                "senior_debt": float(self.senior_debt),
                "subordinated_debt": float(self.subordinated_debt),
                "seller_note": float(self.seller_note),
                "total": float(self.total_sources()),
            },
            "uses": {
                "purchase_price": float(self.purchase_price),
                "transaction_fees": float(self.transaction_fees),
                "debt_financing_fees": float(self.debt_financing_fees),
                "total": float(self.total_uses()),
            },
            "equity_percentage": float(self.equity_percentage()),
            "debt_percentage": float(self.debt_percentage()),
        }


@dataclass
class DebtSchedule:
    """Debt amortization schedule."""
    year: int
    beginning_balance: Decimal
    mandatory_amortization: Decimal
    cash_sweep: Decimal
    ending_balance: Decimal
    interest_expense: Decimal

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "beginning_balance": float(self.beginning_balance),
            "mandatory_amortization": float(self.mandatory_amortization),
            "cash_sweep": float(self.cash_sweep),
            "ending_balance": float(self.ending_balance),
            "interest_expense": float(self.interest_expense),
        }


@dataclass
class ProjectionYear:
    """Financial projections for a single year."""
    year: int
    revenue: Decimal
    ebitda: Decimal
    ebitda_margin: Decimal
    depreciation: Decimal
    interest_expense: Decimal
    taxes: Decimal
    net_income: Decimal
    capex: Decimal
    change_in_nwc: Decimal
    free_cash_flow: Decimal
    debt_balance: Decimal
    cash_balance: Decimal

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "revenue": float(self.revenue),
            "ebitda": float(self.ebitda),
            "ebitda_margin": float(self.ebitda_margin),
            "depreciation": float(self.depreciation),
            "interest_expense": float(self.interest_expense),
            "taxes": float(self.taxes),
            "net_income": float(self.net_income),
            "capex": float(self.capex),
            "change_in_nwc": float(self.change_in_nwc),
            "free_cash_flow": float(self.free_cash_flow),
            "debt_balance": float(self.debt_balance),
            "cash_balance": float(self.cash_balance),
        }


@dataclass
class LBOAssumptions:
    """Input assumptions for LBO model."""
    # Target financials
    ltm_revenue: Decimal
    ltm_ebitda: Decimal
    net_debt: Decimal = Decimal("0")

    # Transaction
    entry_multiple: Decimal = Decimal("8.0")
    exit_multiple: Decimal = Decimal("8.0")
    holding_period: int = 5

    # Growth assumptions
    revenue_growth_rate: Decimal = Decimal("0.05")  # 5%
    ebitda_margin: Optional[Decimal] = None  # If None, calculated from LTM

    # Debt structure
    senior_debt_multiple: Decimal = Decimal("4.0")  # x EBITDA
    senior_interest_rate: Decimal = Decimal("0.08")  # 8%
    mandatory_amortization: Decimal = Decimal("0.05")  # 5% per year
    cash_sweep_percentage: Decimal = Decimal("0.50")  # 50% of excess cash

    # Operating assumptions
    depreciation_pct_revenue: Decimal = Decimal("0.02")  # 2%
    capex_pct_revenue: Decimal = Decimal("0.03")  # 3%
    nwc_pct_revenue: Decimal = Decimal("0.10")  # 10%
    tax_rate: Decimal = Decimal("0.25")  # 25%

    # Transaction costs
    transaction_fee_pct: Decimal = Decimal("0.02")  # 2%
    financing_fee_pct: Decimal = Decimal("0.02")  # 2%

    def to_dict(self) -> dict:
        return {
            "ltm_revenue": float(self.ltm_revenue),
            "ltm_ebitda": float(self.ltm_ebitda),
            "net_debt": float(self.net_debt),
            "entry_multiple": float(self.entry_multiple),
            "exit_multiple": float(self.exit_multiple),
            "holding_period": self.holding_period,
            "revenue_growth_rate": float(self.revenue_growth_rate),
            "ebitda_margin": float(self.ebitda_margin) if self.ebitda_margin else None,
            "senior_debt_multiple": float(self.senior_debt_multiple),
            "senior_interest_rate": float(self.senior_interest_rate),
            "mandatory_amortization": float(self.mandatory_amortization),
            "cash_sweep_percentage": float(self.cash_sweep_percentage),
            "depreciation_pct_revenue": float(self.depreciation_pct_revenue),
            "capex_pct_revenue": float(self.capex_pct_revenue),
            "nwc_pct_revenue": float(self.nwc_pct_revenue),
            "tax_rate": float(self.tax_rate),
            "transaction_fee_pct": float(self.transaction_fee_pct),
            "financing_fee_pct": float(self.financing_fee_pct),
        }


@dataclass
class LBOReturns:
    """LBO return metrics."""
    irr: Decimal
    moic: Decimal
    entry_equity: Decimal
    exit_equity: Decimal
    total_debt_paydown: Decimal
    ebitda_growth_contribution: Decimal
    multiple_expansion_contribution: Decimal
    deleveraging_contribution: Decimal

    def to_dict(self) -> dict:
        return {
            "irr": float(self.irr),
            "irr_formatted": f"{float(self.irr) * 100:.1f}%",
            "moic": float(self.moic),
            "moic_formatted": f"{float(self.moic):.2f}x",
            "entry_equity": float(self.entry_equity),
            "exit_equity": float(self.exit_equity),
            "total_debt_paydown": float(self.total_debt_paydown),
            "value_creation": {
                "ebitda_growth": float(self.ebitda_growth_contribution),
                "multiple_expansion": float(self.multiple_expansion_contribution),
                "deleveraging": float(self.deleveraging_contribution),
            },
        }


class LBOModel:
    """
    Leveraged Buyout financial model.

    Calculates:
    - Sources and Uses
    - Debt schedule
    - Financial projections
    - IRR and MOIC
    - Value creation bridge
    """

    def __init__(self, assumptions: LBOAssumptions):
        self.assumptions = assumptions
        self._validate_assumptions()

        # Calculate derived values
        if assumptions.ebitda_margin is None:
            self.assumptions.ebitda_margin = (
                assumptions.ltm_ebitda / assumptions.ltm_revenue
            ).quantize(Decimal("0.0001"))

        # Build the model
        self.sources_and_uses = self._calculate_sources_and_uses()
        self.projections = self._build_projections()
        self.returns = self._calculate_returns()

    def _validate_assumptions(self):
        """Validate input assumptions."""
        if self.assumptions.ltm_revenue <= 0:
            raise ValueError("LTM revenue must be positive")
        if self.assumptions.ltm_ebitda <= 0:
            raise ValueError("LTM EBITDA must be positive")
        if self.assumptions.entry_multiple <= 0:
            raise ValueError("Entry multiple must be positive")
        if self.assumptions.holding_period < 1 or self.assumptions.holding_period > 10:
            raise ValueError("Holding period must be between 1 and 10 years")

    def _calculate_sources_and_uses(self) -> SourcesAndUses:
        """Calculate sources and uses of funds."""
        a = self.assumptions

        # Enterprise value at entry
        ev = a.ltm_ebitda * a.entry_multiple

        # Purchase price (EV - net debt if negative, + net debt if positive)
        purchase_price = ev + a.net_debt

        # Transaction fees
        transaction_fees = purchase_price * a.transaction_fee_pct

        # Debt
        senior_debt = a.ltm_ebitda * a.senior_debt_multiple

        # Financing fees
        debt_financing_fees = senior_debt * a.financing_fee_pct

        # Total uses
        total_uses = purchase_price + transaction_fees + debt_financing_fees

        # Equity (plug)
        equity = total_uses - senior_debt

        return SourcesAndUses(
            equity=equity.quantize(Decimal("0.01")),
            senior_debt=senior_debt.quantize(Decimal("0.01")),
            purchase_price=purchase_price.quantize(Decimal("0.01")),
            transaction_fees=transaction_fees.quantize(Decimal("0.01")),
            debt_financing_fees=debt_financing_fees.quantize(Decimal("0.01")),
        )

    def _build_projections(self) -> list[ProjectionYear]:
        """Build year-by-year financial projections."""
        a = self.assumptions
        projections = []

        # Initialize
        revenue = a.ltm_revenue
        debt_balance = self.sources_and_uses.senior_debt
        cash_balance = Decimal("0")
        prev_nwc = revenue * a.nwc_pct_revenue

        for year in range(1, a.holding_period + 1):
            # Revenue growth
            revenue = revenue * (1 + a.revenue_growth_rate)

            # EBITDA
            ebitda = revenue * a.ebitda_margin

            # D&A
            depreciation = revenue * a.depreciation_pct_revenue

            # Interest
            interest = debt_balance * a.senior_interest_rate

            # EBT and taxes
            ebt = ebitda - depreciation - interest
            taxes = max(Decimal("0"), ebt * a.tax_rate)

            # Net income
            net_income = ebt - taxes

            # CapEx
            capex = revenue * a.capex_pct_revenue

            # Working capital
            nwc = revenue * a.nwc_pct_revenue
            change_in_nwc = nwc - prev_nwc
            prev_nwc = nwc

            # Free cash flow
            fcf = ebitda - interest - taxes - capex - change_in_nwc

            # Debt paydown
            mandatory_paydown = self.sources_and_uses.senior_debt * a.mandatory_amortization
            cash_available = fcf - mandatory_paydown
            cash_sweep = max(Decimal("0"), cash_available * a.cash_sweep_percentage)

            # Update debt balance
            debt_balance = max(Decimal("0"), debt_balance - mandatory_paydown - cash_sweep)

            # Cash balance (excess after sweep)
            cash_balance = cash_balance + cash_available - cash_sweep

            projections.append(ProjectionYear(
                year=year,
                revenue=revenue.quantize(Decimal("0.01")),
                ebitda=ebitda.quantize(Decimal("0.01")),
                ebitda_margin=(a.ebitda_margin * 100).quantize(Decimal("0.1")),
                depreciation=depreciation.quantize(Decimal("0.01")),
                interest_expense=interest.quantize(Decimal("0.01")),
                taxes=taxes.quantize(Decimal("0.01")),
                net_income=net_income.quantize(Decimal("0.01")),
                capex=capex.quantize(Decimal("0.01")),
                change_in_nwc=change_in_nwc.quantize(Decimal("0.01")),
                free_cash_flow=fcf.quantize(Decimal("0.01")),
                debt_balance=debt_balance.quantize(Decimal("0.01")),
                cash_balance=cash_balance.quantize(Decimal("0.01")),
            ))

        return projections

    def _calculate_returns(self) -> LBOReturns:
        """Calculate IRR, MOIC, and value creation."""
        a = self.assumptions

        # Entry equity
        entry_equity = self.sources_and_uses.equity

        # Exit values
        exit_year = self.projections[-1]
        exit_ebitda = exit_year.ebitda
        exit_ev = exit_ebitda * a.exit_multiple
        exit_debt = exit_year.debt_balance
        exit_cash = exit_year.cash_balance
        exit_equity = exit_ev - exit_debt + exit_cash

        # MOIC
        moic = exit_equity / entry_equity

        # IRR (using simple approximation)
        # IRR = (MOIC ^ (1/n)) - 1
        n = Decimal(str(a.holding_period))
        irr = (moic ** (Decimal("1") / n)) - 1

        # Value creation attribution
        entry_ev = a.ltm_ebitda * a.entry_multiple
        exit_ev_at_entry_multiple = exit_ebitda * a.entry_multiple

        # EBITDA growth contribution
        ebitda_growth_contribution = exit_ev_at_entry_multiple - entry_ev

        # Multiple expansion contribution
        multiple_expansion = (a.exit_multiple - a.entry_multiple) * exit_ebitda

        # Deleveraging contribution
        total_debt_paydown = self.sources_and_uses.senior_debt - exit_debt

        return LBOReturns(
            irr=irr.quantize(Decimal("0.0001")),
            moic=moic.quantize(Decimal("0.01")),
            entry_equity=entry_equity,
            exit_equity=exit_equity.quantize(Decimal("0.01")),
            total_debt_paydown=total_debt_paydown.quantize(Decimal("0.01")),
            ebitda_growth_contribution=ebitda_growth_contribution.quantize(Decimal("0.01")),
            multiple_expansion_contribution=multiple_expansion.quantize(Decimal("0.01")),
            deleveraging_contribution=total_debt_paydown.quantize(Decimal("0.01")),
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "assumptions": self.assumptions.to_dict(),
            "sources_and_uses": self.sources_and_uses.to_dict(),
            "projections": [p.to_dict() for p in self.projections],
            "returns": self.returns.to_dict(),
        }


class SensitivityTable:
    """
    Generate sensitivity tables for LBO returns.

    Creates a matrix showing IRR/MOIC across different assumption combinations.
    """

    def __init__(self, base_assumptions: LBOAssumptions):
        self.base_assumptions = base_assumptions

    def generate_entry_exit_sensitivity(
        self,
        entry_multiples: list[Decimal] = None,
        exit_multiples: list[Decimal] = None,
        metric: str = "irr",
    ) -> dict:
        """Generate entry/exit multiple sensitivity table."""
        if entry_multiples is None:
            base = self.base_assumptions.entry_multiple
            entry_multiples = [
                base - Decimal("1.5"),
                base - Decimal("1.0"),
                base - Decimal("0.5"),
                base,
                base + Decimal("0.5"),
            ]

        if exit_multiples is None:
            base = self.base_assumptions.exit_multiple
            exit_multiples = [
                base - Decimal("1.0"),
                base - Decimal("0.5"),
                base,
                base + Decimal("0.5"),
                base + Decimal("1.0"),
            ]

        results = []
        for entry in entry_multiples:
            row = {"entry_multiple": float(entry), "values": []}
            for exit_mult in exit_multiples:
                assumptions = LBOAssumptions(
                    ltm_revenue=self.base_assumptions.ltm_revenue,
                    ltm_ebitda=self.base_assumptions.ltm_ebitda,
                    net_debt=self.base_assumptions.net_debt,
                    entry_multiple=entry,
                    exit_multiple=exit_mult,
                    holding_period=self.base_assumptions.holding_period,
                    revenue_growth_rate=self.base_assumptions.revenue_growth_rate,
                    ebitda_margin=self.base_assumptions.ebitda_margin,
                    senior_debt_multiple=self.base_assumptions.senior_debt_multiple,
                    senior_interest_rate=self.base_assumptions.senior_interest_rate,
                )
                try:
                    model = LBOModel(assumptions)
                    if metric == "irr":
                        value = float(model.returns.irr * 100)
                    else:
                        value = float(model.returns.moic)
                    row["values"].append({
                        "exit_multiple": float(exit_mult),
                        metric: value,
                    })
                except Exception:
                    row["values"].append({
                        "exit_multiple": float(exit_mult),
                        metric: None,
                    })
            results.append(row)

        return {
            "type": "entry_exit_sensitivity",
            "metric": metric,
            "exit_multiples": [float(m) for m in exit_multiples],
            "rows": results,
        }

    def generate_growth_leverage_sensitivity(
        self,
        growth_rates: list[Decimal] = None,
        leverage_multiples: list[Decimal] = None,
        metric: str = "irr",
    ) -> dict:
        """Generate revenue growth / leverage sensitivity table."""
        if growth_rates is None:
            growth_rates = [
                Decimal("0.00"),
                Decimal("0.03"),
                Decimal("0.05"),
                Decimal("0.07"),
                Decimal("0.10"),
            ]

        if leverage_multiples is None:
            leverage_multiples = [
                Decimal("3.0"),
                Decimal("3.5"),
                Decimal("4.0"),
                Decimal("4.5"),
                Decimal("5.0"),
            ]

        results = []
        for growth in growth_rates:
            row = {"revenue_growth": float(growth * 100), "values": []}
            for leverage in leverage_multiples:
                assumptions = LBOAssumptions(
                    ltm_revenue=self.base_assumptions.ltm_revenue,
                    ltm_ebitda=self.base_assumptions.ltm_ebitda,
                    net_debt=self.base_assumptions.net_debt,
                    entry_multiple=self.base_assumptions.entry_multiple,
                    exit_multiple=self.base_assumptions.exit_multiple,
                    holding_period=self.base_assumptions.holding_period,
                    revenue_growth_rate=growth,
                    ebitda_margin=self.base_assumptions.ebitda_margin,
                    senior_debt_multiple=leverage,
                    senior_interest_rate=self.base_assumptions.senior_interest_rate,
                )
                try:
                    model = LBOModel(assumptions)
                    if metric == "irr":
                        value = float(model.returns.irr * 100)
                    else:
                        value = float(model.returns.moic)
                    row["values"].append({
                        "leverage": float(leverage),
                        metric: value,
                    })
                except Exception:
                    row["values"].append({
                        "leverage": float(leverage),
                        metric: None,
                    })
            results.append(row)

        return {
            "type": "growth_leverage_sensitivity",
            "metric": metric,
            "leverage_multiples": [float(m) for m in leverage_multiples],
            "rows": results,
        }
