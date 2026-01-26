"""Financial statement reconciliation and cross-validation."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.schemas.financials import TracedFinancials

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of a reconciliation check."""

    check_name: str
    passed: bool
    expected_value: Optional[Decimal]
    actual_value: Optional[Decimal]
    variance: Optional[Decimal]
    variance_percent: Optional[Decimal]
    message: str


@dataclass
class ReconciliationReport:
    """Full reconciliation report for a set of financials."""

    results: list[ReconciliationResult]
    passed_count: int
    failed_count: int
    skipped_count: int
    overall_pass: bool
    notes: list[str]


class FinancialReconciler:
    """
    Cross-statement validation for extracted financial data.

    Performs checks like:
    - Assets = Liabilities + Equity
    - Net Income ties between statements
    - Cash flow reconciliation
    - Margin calculations
    """

    def __init__(self, tolerance: Decimal = Decimal("0.01")):
        """
        Initialize reconciler.

        Args:
            tolerance: Acceptable variance as decimal (0.01 = 1%)
        """
        self.tolerance = tolerance

    def reconcile(self, financials: TracedFinancials) -> ReconciliationReport:
        """
        Run all reconciliation checks on a set of financials.

        Args:
            financials: The financials to validate

        Returns:
            ReconciliationReport with all results
        """
        results = []
        notes = []

        # Balance Sheet Identity
        results.append(self._check_balance_sheet_identity(financials))

        # EBITDA Margin
        results.append(self._check_ebitda_margin(financials))

        # Net Debt Calculation
        results.append(self._check_net_debt(financials))

        # Free Cash Flow
        results.append(self._check_free_cash_flow(financials))

        # Gross Profit Margin
        results.append(self._check_gross_margin(financials))

        # Calculate summary
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed and r.expected_value is not None)
        skipped = sum(1 for r in results if r.expected_value is None and not r.passed)

        overall_pass = failed == 0

        if not overall_pass:
            notes.append(f"WARNING: {failed} reconciliation check(s) failed")
            for r in results:
                if not r.passed and r.expected_value is not None:
                    notes.append(f"  - {r.check_name}: {r.message}")

        return ReconciliationReport(
            results=results,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            overall_pass=overall_pass,
            notes=notes,
        )

    def _check_balance_sheet_identity(
        self,
        financials: TracedFinancials,
    ) -> ReconciliationResult:
        """Check that Assets = Liabilities + Equity."""
        if not all([
            financials.total_assets,
            financials.total_liabilities,
            financials.total_equity,
        ]):
            return ReconciliationResult(
                check_name="Balance Sheet Identity",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Missing balance sheet values - cannot verify",
            )

        assets = financials.total_assets.value
        liabilities = financials.total_liabilities.value
        equity = financials.total_equity.value

        expected = liabilities + equity
        variance = abs(assets - expected)

        if assets != 0:
            variance_percent = variance / abs(assets)
        else:
            variance_percent = Decimal("0") if variance == 0 else Decimal("1")

        passed = variance_percent <= self.tolerance

        return ReconciliationResult(
            check_name="Balance Sheet Identity",
            passed=passed,
            expected_value=expected,
            actual_value=assets,
            variance=variance,
            variance_percent=variance_percent,
            message=(
                f"Assets ({assets:,.0f}) vs Liabilities + Equity ({expected:,.0f})"
                if not passed else "Balance sheet balances"
            ),
        )

    def _check_ebitda_margin(
        self,
        financials: TracedFinancials,
    ) -> ReconciliationResult:
        """Verify EBITDA margin calculation."""
        if not financials.revenue or not financials.ebitda:
            return ReconciliationResult(
                check_name="EBITDA Margin",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Missing revenue or EBITDA - cannot calculate margin",
            )

        revenue = financials.revenue.value
        ebitda = financials.ebitda.value

        if revenue == 0:
            return ReconciliationResult(
                check_name="EBITDA Margin",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Revenue is zero - cannot calculate margin",
            )

        calculated_margin = ebitda / revenue
        stored_margin = financials.ebitda_margin

        if stored_margin is None:
            # Just calculate and report, no verification needed
            financials.ebitda_margin = calculated_margin
            return ReconciliationResult(
                check_name="EBITDA Margin",
                passed=True,
                expected_value=calculated_margin,
                actual_value=calculated_margin,
                variance=Decimal("0"),
                variance_percent=Decimal("0"),
                message=f"EBITDA margin calculated: {calculated_margin:.1%}",
            )

        variance = abs(calculated_margin - stored_margin)
        passed = variance <= self.tolerance

        return ReconciliationResult(
            check_name="EBITDA Margin",
            passed=passed,
            expected_value=calculated_margin,
            actual_value=stored_margin,
            variance=variance,
            variance_percent=variance,
            message=(
                f"Stored margin ({stored_margin:.1%}) differs from calculated ({calculated_margin:.1%})"
                if not passed else f"EBITDA margin verified: {calculated_margin:.1%}"
            ),
        )

    def _check_net_debt(
        self,
        financials: TracedFinancials,
    ) -> ReconciliationResult:
        """Verify net debt = total debt - cash."""
        if not financials.total_debt or not financials.cash:
            return ReconciliationResult(
                check_name="Net Debt",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Missing debt or cash values",
            )

        total_debt = financials.total_debt.value
        cash = financials.cash.value
        calculated_net_debt = total_debt - cash

        if financials.net_debt is None:
            financials.net_debt = calculated_net_debt
            return ReconciliationResult(
                check_name="Net Debt",
                passed=True,
                expected_value=calculated_net_debt,
                actual_value=calculated_net_debt,
                variance=Decimal("0"),
                variance_percent=Decimal("0"),
                message=f"Net debt calculated: {calculated_net_debt:,.0f}",
            )

        variance = abs(calculated_net_debt - financials.net_debt)
        base = abs(calculated_net_debt) if calculated_net_debt != 0 else Decimal("1")
        variance_percent = variance / base
        passed = variance_percent <= self.tolerance

        return ReconciliationResult(
            check_name="Net Debt",
            passed=passed,
            expected_value=calculated_net_debt,
            actual_value=financials.net_debt,
            variance=variance,
            variance_percent=variance_percent,
            message=(
                f"Net debt mismatch: stored ({financials.net_debt:,.0f}) vs calculated ({calculated_net_debt:,.0f})"
                if not passed else "Net debt verified"
            ),
        )

    def _check_free_cash_flow(
        self,
        financials: TracedFinancials,
    ) -> ReconciliationResult:
        """Verify FCF = Operating Cash Flow - CapEx."""
        if not financials.operating_cash_flow or not financials.capex:
            return ReconciliationResult(
                check_name="Free Cash Flow",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Missing OCF or CapEx values",
            )

        ocf = financials.operating_cash_flow.value
        capex = abs(financials.capex.value)  # CapEx is often negative
        calculated_fcf = ocf - capex

        if not financials.free_cash_flow:
            return ReconciliationResult(
                check_name="Free Cash Flow",
                passed=True,
                expected_value=calculated_fcf,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message=f"FCF calculated: {calculated_fcf:,.0f} (no stored value to verify)",
            )

        stored_fcf = financials.free_cash_flow.value
        variance = abs(calculated_fcf - stored_fcf)
        base = abs(calculated_fcf) if calculated_fcf != 0 else Decimal("1")
        variance_percent = variance / base
        passed = variance_percent <= self.tolerance

        return ReconciliationResult(
            check_name="Free Cash Flow",
            passed=passed,
            expected_value=calculated_fcf,
            actual_value=stored_fcf,
            variance=variance,
            variance_percent=variance_percent,
            message=(
                f"FCF mismatch: stored ({stored_fcf:,.0f}) vs calculated ({calculated_fcf:,.0f})"
                if not passed else "FCF verified"
            ),
        )

    def _check_gross_margin(
        self,
        financials: TracedFinancials,
    ) -> ReconciliationResult:
        """Check gross profit margin is reasonable."""
        if not financials.revenue or not financials.gross_profit:
            return ReconciliationResult(
                check_name="Gross Margin",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Missing revenue or gross profit",
            )

        revenue = financials.revenue.value
        gross_profit = financials.gross_profit.value

        if revenue == 0:
            return ReconciliationResult(
                check_name="Gross Margin",
                passed=False,
                expected_value=None,
                actual_value=None,
                variance=None,
                variance_percent=None,
                message="Revenue is zero",
            )

        gross_margin = gross_profit / revenue

        # Sanity check: margin should typically be between -50% and 100%
        reasonable = Decimal("-0.5") <= gross_margin <= Decimal("1.0")

        return ReconciliationResult(
            check_name="Gross Margin",
            passed=reasonable,
            expected_value=None,
            actual_value=gross_margin,
            variance=None,
            variance_percent=None,
            message=(
                f"Gross margin ({gross_margin:.1%}) outside typical range"
                if not reasonable else f"Gross margin: {gross_margin:.1%}"
            ),
        )

    def compare_periods(
        self,
        current: TracedFinancials,
        prior: TracedFinancials,
    ) -> list[ReconciliationResult]:
        """
        Compare financials between two periods.

        Checks for unusual changes that might indicate errors.
        """
        results = []

        # Revenue growth check
        if current.revenue and prior.revenue:
            current_rev = current.revenue.value
            prior_rev = prior.revenue.value

            if prior_rev != 0:
                growth = (current_rev - prior_rev) / abs(prior_rev)

                # Flag if growth > 100% or decline > 50%
                reasonable = Decimal("-0.5") <= growth <= Decimal("1.0")

                results.append(ReconciliationResult(
                    check_name="Revenue Growth",
                    passed=reasonable,
                    expected_value=None,
                    actual_value=growth,
                    variance=None,
                    variance_percent=None,
                    message=(
                        f"Revenue growth ({growth:.1%}) is unusual - verify"
                        if not reasonable else f"Revenue growth: {growth:.1%}"
                    ),
                ))

        return results
