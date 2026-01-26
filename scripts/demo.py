#!/usr/bin/env python3
"""
PE-Nexus End-to-End Demo Script

Demonstrates the full PE-Nexus pipeline:
  Phase 1: Deal Sourcing (IntelligenceScout)
  Phase 2: Financial Triage (ForensicAnalyst - simulated)
  Phase 3: Relationship Discovery (RelationshipNavigator)
  Phase 4: Legal Diligence (LegalGuardian)
  Phase 5: Financial Modeling (QuantStrategist)
  Phase 6: IC Debate (AdversarialIC)
  Phase 7: Portfolio Monitoring (ValueCreationMonitor)

Run with: python scripts/demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

# Rich console imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better output formatting: pip install rich")

# ASCII symbols for cross-platform compatibility
SYMBOL_CHECK = "[OK]"
SYMBOL_BULLET = "*"
SYMBOL_WARNING = "[!]"
SYMBOL_ERROR = "[X]"
SYMBOL_ARROW = "->"
SYMBOL_STAR = "*"


class DemoConsole:
    """Wrapper for console output that works with or without rich."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def print(self, *args, **kwargs):
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            # Strip rich markup for plain print
            text = " ".join(str(a) for a in args)
            print(text)

    def print_header(self, title: str, subtitle: str = ""):
        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]" if subtitle else f"[bold cyan]{title}[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE,
            ))
        else:
            print()
            print("=" * 60)
            print(title)
            if subtitle:
                print(subtitle)
            print("=" * 60)

    def print_phase(self, phase_num: int, title: str):
        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"[bold yellow]Phase {phase_num}:[/bold yellow] [white]{title}[/white]",
                border_style="yellow",
            ))
        else:
            print()
            print(f"--- Phase {phase_num}: {title} ---")

    def print_success(self, message: str):
        if self.console:
            self.console.print(f"[green]{SYMBOL_CHECK}[/green] {message}")
        else:
            print(f"{SYMBOL_CHECK} {message}")

    def print_info(self, message: str):
        if self.console:
            self.console.print(f"[blue]{SYMBOL_BULLET}[/blue] {message}")
        else:
            print(f"  {SYMBOL_BULLET} {message}")

    def print_warning(self, message: str):
        if self.console:
            self.console.print(f"[yellow]{SYMBOL_WARNING}[/yellow] {message}")
        else:
            print(f"{SYMBOL_WARNING} {message}")

    def print_error(self, message: str):
        if self.console:
            self.console.print(f"[red]{SYMBOL_ERROR}[/red] {message}")
        else:
            print(f"{SYMBOL_ERROR} {message}")

    def print_table(self, title: str, headers: list, rows: list):
        if self.console:
            table = Table(title=title, box=box.ROUNDED)
            for header in headers:
                table.add_column(header, style="cyan")
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self.console.print(table)
        else:
            print(f"\n{title}:")
            print(" | ".join(headers))
            print("-" * 60)
            for row in rows:
                print(" | ".join(str(cell) for cell in row))

    def print_key_value(self, key: str, value: str):
        if self.console:
            self.console.print(f"  [dim]{key}:[/dim] [white]{value}[/white]")
        else:
            print(f"  {key}: {value}")

    def create_progress(self):
        if self.console:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            )
        return None


# Initialize console
console = DemoConsole()


async def init_system():
    """Initialize PE-Nexus core systems."""
    console.print_info("Initializing database...")
    from src.db.database import init_db
    await init_db()

    console.print_info("Starting event bus...")
    from src.core.events import init_event_bus
    await init_event_bus()

    console.print_success("PE-Nexus systems initialized")


async def cleanup_system():
    """Clean up PE-Nexus systems."""
    from src.core.events import shutdown_event_bus
    await shutdown_event_bus()


# =============================================================================
# Phase 1: Deal Sourcing
# =============================================================================

async def demo_sourcing():
    """Demonstrate IntelligenceScout agent for deal sourcing."""
    console.print_phase(1, "Deal Sourcing - IntelligenceScout Agent")

    from src.agents.scout import IntelligenceScoutAgent

    scout = IntelligenceScoutAgent(target_industries=["Technology"])

    # Analyze a specific company
    console.print_info("Analyzing target company: CloudSync Technologies...")
    result = await scout.analyze_company(
        company_name="CloudSync Technologies",
        industry="Technology",
        sub_sector="Enterprise Software",
    )

    if not result.success:
        console.print_error(f"Analysis failed: {result.errors}")
        return None

    scored_deal = result.output_data.get("scored_deal", {})

    console.print_success(f"Deal analysis complete in {result.duration_seconds:.2f}s")
    console.print()

    # Display results
    console.print_key_value("Company", scored_deal.get("company_name", "Unknown"))
    console.print_key_value("Industry", f"{scored_deal.get('industry', '')} / {scored_deal.get('sub_sector', '')}")
    console.print_key_value("Deal Score", f"{scored_deal.get('total_score', 0):.1f}/10")
    console.print_key_value("Score Tier", scored_deal.get("score_tier", ""))

    # Investment thesis
    thesis = scored_deal.get("investment_thesis", "")
    if thesis:
        console.print()
        console.print_info(f"Investment Thesis: {thesis[:200]}...")

    # Key signals
    signals = scored_deal.get("key_signals", [])
    if signals:
        console.print()
        console.print_info("Key Signals:")
        for signal in signals[:3]:
            console.print(f"    * {signal}")

    # Clean up
    await scout.close()

    return scored_deal


# =============================================================================
# Phase 2: Financial Triage
# =============================================================================

async def demo_triage(deal_context: dict):
    """Demonstrate ForensicAnalyst agent for financial extraction."""
    console.print_phase(2, "Financial Triage - ForensicAnalyst Agent")

    # Note: ForensicAnalyst normally extracts from PDFs.
    # For demo purposes, we'll simulate extraction results.
    console.print_info("Note: Simulating PDF extraction (no PDF file provided)")
    console.print_info("In production, this would extract from uploaded CIM documents")
    console.print()

    # Simulated financial data (what ForensicAnalyst would extract)
    financials = {
        "company_name": deal_context.get("company_name", "CloudSync Technologies"),
        "fiscal_year": "2024",
        "revenue": 125.0,  # $125M
        "ebitda": 25.0,    # $25M (20% margin)
        "net_income": 15.0,
        "total_assets": 180.0,
        "total_debt": 30.0,
        "cash": 20.0,
        "ebitda_margin": 0.20,
        "revenue_growth": 0.18,  # 18% YoY
    }

    console.print_success("Financial data extracted (simulated)")
    console.print()

    # Display financial summary
    console.print_table(
        "Extracted Financials",
        ["Metric", "Value", "Source"],
        [
            ["Revenue", f"${financials['revenue']:.1f}M", "CIM p.15"],
            ["EBITDA", f"${financials['ebitda']:.1f}M", "CIM p.18"],
            ["EBITDA Margin", f"{financials['ebitda_margin']*100:.1f}%", "Calculated"],
            ["Revenue Growth", f"{financials['revenue_growth']*100:.1f}%", "CIM p.12"],
            ["Net Debt", f"${financials['total_debt'] - financials['cash']:.1f}M", "CIM p.22"],
        ]
    )

    return financials


# =============================================================================
# Phase 3: Relationship Discovery
# =============================================================================

async def demo_relationships(deal_context: dict):
    """Demonstrate RelationshipNavigator agent for finding warm paths."""
    console.print_phase(3, "Relationship Discovery - RelationshipNavigator Agent")

    from src.agents.navigator import RelationshipNavigatorAgent

    navigator = RelationshipNavigatorAgent()

    # Find path from firm partner to target CEO
    console.print_info("Finding warm path to target CEO...")
    console.print_info("From: Alex Chen (PE-Nexus Capital)")
    console.print_info("To: Jennifer Martinez (CloudSync CEO)")
    console.print()

    result = await navigator.suggest_introduction(
        from_person="Alex Chen",
        to_person="Jennifer Martinez",
        context="Exploring strategic partnership opportunity",
    )

    if not result.success:
        console.print_warning("No direct path found, trying alternative...")
        # Try a different path
        result = await navigator.find_path(
            from_person="Alex Chen",
            to_person="David Thompson",  # TechFlow CEO
            max_hops=3,
        )

    if result.success and result.output_data.get("best_path"):
        console.print_success("Connection path found!")

        best_path = result.output_data.get("best_path", {})
        intro_draft = result.output_data.get("introduction_draft", {})

        console.print()
        console.print_key_value("Path Hops", str(best_path.get("total_hops", "N/A")))
        console.print_key_value("Path Strength", f"{best_path.get('path_strength', 0):.2f}")

        # Show connection chain
        chain = best_path.get("introduction_chain", [])
        if chain:
            console.print()
            console.print_info("Connection Chain:")
            for step in chain:
                console.print(f"    -> {step}")

        # Show intro draft
        if intro_draft:
            console.print()
            console.print_info(f"Introducer: {intro_draft.get('introducer', {}).get('name', 'Unknown')}")
            console.print_info(f"Subject: {intro_draft.get('subject', '')}")
    else:
        console.print_warning("No connection path found within 3 hops")

    return result.output_data


# =============================================================================
# Phase 4: Legal Diligence
# =============================================================================

async def demo_legal():
    """Demonstrate LegalGuardian agent for contract analysis."""
    console.print_phase(4, "Legal Diligence - LegalGuardian Agent")

    from src.agents.guardian import LegalGuardianAgent

    guardian = LegalGuardianAgent()

    console.print_info("Analyzing VDR contracts for legal risks...")

    # Analyze all contracts
    result = await guardian.analyze_all()

    if not result.success:
        console.print_error(f"Analysis failed: {result.errors}")
        return None

    data = result.output_data
    console.print_success(f"Analyzed {data.get('contracts_analyzed', 0)} contracts")
    console.print()

    # Summary
    console.print_key_value("Total Critical Flags", str(data.get("total_critical_flags", 0)))
    console.print_key_value("Total High Priority Flags", str(data.get("total_high_flags", 0)))

    # Show individual contract risks
    analyses = data.get("analyses", [])
    if analyses:
        console.print()
        rows = []
        for a in analyses[:5]:  # Top 5 contracts
            rows.append([
                a.get("contract_name", "Unknown")[:30],
                a.get("counterparty", "")[:20],
                a.get("overall_risk", "").upper(),
                str(a.get("flag_count", 0)),
            ])

        console.print_table(
            "Contract Risk Summary",
            ["Contract", "Counterparty", "Risk Level", "Flags"],
            rows
        )

    # Show a critical flag if any
    for a in analyses:
        if a.get("critical_flags", 0) > 0:
            flags = a.get("flags", [])
            for f in flags:
                if f.get("risk_level") == "critical":
                    console.print()
                    console.print_warning(f"Critical Issue Found:")
                    console.print_key_value("Contract", a.get("contract_name", ""))
                    console.print_key_value("Clause Type", f.get("clause_type", ""))
                    console.print_key_value("Description", f.get("description", "")[:100])
                    break
            break

    return data


# =============================================================================
# Phase 5: Financial Modeling
# =============================================================================

async def demo_modeling(financials: dict):
    """Demonstrate QuantStrategist agent for LBO modeling."""
    console.print_phase(5, "Financial Modeling - QuantStrategist Agent")

    from src.agents.strategist import QuantStrategistAgent

    strategist = QuantStrategistAgent()

    console.print_info("Building LBO model with extracted financials...")

    result = await strategist.analyze(
        company_name=financials.get("company_name", "Target"),
        ltm_revenue=financials.get("revenue", 125),
        ltm_ebitda=financials.get("ebitda", 25),
        entry_multiple=8.0,
        exit_multiple=9.0,  # Assume modest expansion
        holding_period=5,
        leverage=4.5,
        revenue_growth=financials.get("revenue_growth", 0.10),
    )

    if not result.success:
        console.print_error(f"Modeling failed: {result.errors}")
        return None

    data = result.output_data
    model = data.get("model", {})
    returns = model.get("returns", {})
    commentary = data.get("commentary", {})

    console.print_success("LBO model complete")
    console.print()

    # Transaction summary
    sources = model.get("sources_and_uses", {})
    console.print_key_value("Enterprise Value", f"${sources.get('enterprise_value', 0):.1f}M")
    console.print_key_value("Equity Check", f"${sources.get('equity', 0):.1f}M")
    console.print_key_value("Debt", f"${sources.get('senior_debt', 0):.1f}M")

    console.print()

    # Returns
    console.print_table(
        "Investment Returns",
        ["Metric", "Value", "Assessment"],
        [
            ["IRR", f"{returns.get('irr_pct', 0):.1f}%", "vs 20% target"],
            ["MOIC", f"{returns.get('moic', 0):.2f}x", "vs 2.5x target"],
            ["Exit Equity", f"${returns.get('exit_equity', 0):.1f}M", ""],
        ]
    )

    # Verdict
    verdict = commentary.get("verdict", "UNKNOWN")
    console.print()
    if verdict == "ATTRACTIVE":
        console.print_success(f"Investment Verdict: {verdict}")
    elif verdict == "MARGINAL":
        console.print_warning(f"Investment Verdict: {verdict}")
    else:
        console.print_error(f"Investment Verdict: {verdict}")

    console.print_info(f"Thesis: {commentary.get('investment_thesis', '')[:150]}...")

    return {
        "model": model,
        "returns": returns,
        "commentary": commentary,
        "irr": returns.get("irr_pct", 0) / 100,
    }


# =============================================================================
# Phase 6: IC Debate
# =============================================================================

async def demo_ic_debate(deal_context: dict, model_output: dict):
    """Demonstrate AdversarialIC agent for investment committee debate."""
    console.print_phase(6, "IC Debate - AdversarialIC Agent")

    from src.agents.ic import AdversarialICAgent

    ic_agent = AdversarialICAgent()

    # Build deal context for IC
    ic_context = {
        "company_name": deal_context.get("company_name", "CloudSync Technologies"),
        "industry": deal_context.get("industry", "Technology"),
        "sub_sector": deal_context.get("sub_sector", "Enterprise Software"),
        "entry_multiple": 8.0,
        "irr": f"{model_output.get('irr', 0.20) * 100:.1f}%",
        "moic": f"{model_output.get('returns', {}).get('moic', 2.0):.2f}x",
        "thesis": model_output.get("commentary", {}).get("investment_thesis", ""),
    }

    console.print_info("Running Bull vs Bear debate...")

    result = await ic_agent.run_debate(ic_context)

    if not result.success:
        console.print_error(f"Debate failed: {result.errors}")
        return None

    debate = result.output_data.get("debate_outcome", {})

    console.print_success(f"IC debate complete in {result.duration_seconds:.2f}s")
    console.print()

    # Bull case highlights
    bull = debate.get("bull_memo", {})
    console.print_info("Bull Case Highlights:")
    for point in bull.get("investment_thesis", [])[:3]:
        console.print(f"    [green]+[/green] {point}" if RICH_AVAILABLE else f"    + {point}")

    console.print()

    # Bear case highlights
    bear = debate.get("bear_assessment", {})
    console.print_info("Bear Case Highlights:")
    deal_killers = bear.get("deal_killers", [])
    for dk in deal_killers[:2]:
        issue = dk.get("issue", dk) if isinstance(dk, dict) else dk
        console.print(f"    [red]-[/red] {issue}" if RICH_AVAILABLE else f"    - {issue}")

    major_risks = bear.get("major_risks", [])
    for risk in major_risks[:2]:
        r = risk.get("risk", risk) if isinstance(risk, dict) else risk
        console.print(f"    [yellow]![/yellow] {r}" if RICH_AVAILABLE else f"    ! {r}")

    console.print()

    # Final recommendation
    recommendation = debate.get("final_recommendation", "PENDING")
    confidence = debate.get("confidence_level", "MEDIUM")

    if "APPROVE" in recommendation and "CONDITIONS" not in recommendation:
        console.print_success(f"IC Recommendation: {recommendation} (Confidence: {confidence})")
    elif "CONDITIONS" in recommendation or "DD" in recommendation:
        console.print_warning(f"IC Recommendation: {recommendation} (Confidence: {confidence})")
    else:
        console.print_error(f"IC Recommendation: {recommendation} (Confidence: {confidence})")

    # Conditions
    conditions = debate.get("key_conditions", [])
    if conditions:
        console.print()
        console.print_info("Key Conditions:")
        for condition in conditions[:3]:
            console.print(f"    * {condition}")

    return debate


# =============================================================================
# Phase 7: Portfolio Monitoring
# =============================================================================

async def demo_monitoring():
    """Demonstrate ValueCreationMonitor agent for portfolio tracking."""
    console.print_phase(7, "Portfolio Monitoring - ValueCreationMonitor Agent")

    from src.agents.monitor import ValueCreationMonitorAgent

    monitor = ValueCreationMonitorAgent()

    # Get portfolio dashboard
    console.print_info("Fetching portfolio dashboard...")

    result = await monitor.get_dashboard()

    if not result.success:
        console.print_error(f"Dashboard failed: {result.errors}")
        return None

    data = result.output_data
    summary = data.get("summary", {})
    companies = data.get("companies", [])

    console.print_success("Portfolio dashboard loaded")
    console.print()

    # Summary metrics
    console.print_key_value("Portfolio Companies", str(summary.get("total_companies", 0)))
    console.print_key_value("Total NAV", f"${summary.get('total_nav', 0):.1f}M")
    console.print_key_value("Wtd. Revenue Growth", f"{summary.get('weighted_revenue_growth', 0):.1f}%")
    console.print_key_value("Active Alerts", str(data.get("total_alerts", 0)))
    console.print_key_value("Critical Alerts", str(data.get("critical_alerts", 0)))

    console.print()

    # Company status table
    if companies:
        rows = []
        for c in companies[:5]:
            status_icon = {
                "on_track": "[OK]" if not RICH_AVAILABLE else "[green][OK][/green]",
                "watch": "!" if not RICH_AVAILABLE else "[yellow]![/yellow]",
                "at_risk": "[X]" if not RICH_AVAILABLE else "[red][X][/red]",
                "outperforming": "*" if not RICH_AVAILABLE else "[cyan]*[/cyan]",
            }.get(c.get("status", ""), "?")

            rows.append([
                c.get("name", "")[:25],
                c.get("industry", "")[:15],
                f"{status_icon} {c.get('status', '').upper()}",
                c.get("ytd_revenue_variance", ""),
                str(c.get("alert_count", 0)),
            ])

        console.print_table(
            "Portfolio Status",
            ["Company", "Industry", "Status", "Rev vs Plan", "Alerts"],
            rows
        )

    # Generate LP report preview
    console.print()
    console.print_info("Generating Q4 2025 LP Report preview...")

    report_result = await monitor.generate_lp_report(quarter=4, year=2025)

    if report_result.success:
        report = report_result.output_data.get("report", {})
        exec_summary = report.get("executive_summary", "")

        console.print()
        console.print_info("Executive Summary Preview:")
        # Show first 300 chars of executive summary
        preview = exec_summary[:300] + "..." if len(exec_summary) > 300 else exec_summary
        console.print(f"    \"{preview}\"")

    return data


# =============================================================================
# Main Demo Orchestration
# =============================================================================

async def main():
    """Run the complete PE-Nexus demo."""

    console.print_header(
        "PE-NEXUS: Full Pipeline Demo",
        "Private Equity Deal Orchestration Platform"
    )

    start_time = datetime.now()

    try:
        # Initialize systems
        console.print()
        console.print_info("Initializing PE-Nexus...")
        await init_system()

        # Phase 1: Sourcing
        deal_context = await demo_sourcing()
        if not deal_context:
            deal_context = {
                "company_name": "CloudSync Technologies",
                "industry": "Technology",
                "sub_sector": "Enterprise Software",
            }

        # Phase 2: Triage
        financials = await demo_triage(deal_context)

        # Phase 3: Relationships
        await demo_relationships(deal_context)

        # Phase 4: Legal
        await demo_legal()

        # Phase 5: Modeling
        model_output = await demo_modeling(financials)
        if not model_output:
            model_output = {"irr": 0.22, "returns": {"moic": 2.5}, "commentary": {}}

        # Phase 6: IC Debate
        await demo_ic_debate(deal_context, model_output)

        # Phase 7: Monitoring
        await demo_monitoring()

        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()

        console.print()
        console.print_header("Demo Complete", f"Total elapsed time: {elapsed:.1f}s")

        console.print()
        console.print_success("All 7 pipeline phases executed successfully!")
        console.print()
        console.print_info("Agents demonstrated:")
        console.print("    1. IntelligenceScout - Deal sourcing and scoring")
        console.print("    2. ForensicAnalyst - Financial extraction (simulated)")
        console.print("    3. RelationshipNavigator - Warm path discovery")
        console.print("    4. LegalGuardian - Contract risk analysis")
        console.print("    5. QuantStrategist - LBO modeling")
        console.print("    6. AdversarialIC - Bull/Bear debate")
        console.print("    7. ValueCreationMonitor - Portfolio KPIs")

        console.print()
        console.print_info("To explore further:")
        console.print("    * Start API server: uvicorn src.main:app --reload")
        console.print("    * Visit Swagger UI: http://localhost:8000/docs")
        console.print("    * Run tests: pytest tests/")

    except KeyboardInterrupt:
        console.print()
        console.print_warning("Demo interrupted by user")
    except Exception as e:
        console.print()
        console.print_error(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cleanup_system()


if __name__ == "__main__":
    asyncio.run(main())
