"""Agent management API routes."""

import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import DBSession, EventBusDep
from src.db.models import DealModel, DocumentModel, ExtractionModel, FinancialModel
from src.agents.forensic import ForensicAnalystAgent, create_forensic_analyst
from src.agents.navigator import RelationshipNavigatorAgent, create_navigator
from src.agents.scout import IntelligenceScoutAgent
from src.agents.guardian import LegalGuardianAgent, create_guardian
from src.agents.strategist import QuantStrategistAgent, create_strategist
from src.agents.ic import AdversarialICAgent, create_ic_agent
from src.agents.monitor import ValueCreationMonitorAgent, create_vcm
from src.services.peer_review import get_peer_review_service, ReviewType

router = APIRouter(prefix="/agents", tags=["agents"])

# Lock for thread-safe access to _running_tasks
_tasks_lock = asyncio.Lock()


class ExtractFinancialsRequest(BaseModel):
    """Request to extract financials from a document."""

    document_id: UUID
    deal_id: UUID


class ScoutAnalyzeRequest(BaseModel):
    """Request to analyze a company for deal potential."""

    company_name: str
    industry: str = ""
    sub_sector: str = ""
    deal_id: Optional[UUID] = None


class ScoutScanRequest(BaseModel):
    """Request to scan an industry for opportunities."""

    industry: Optional[str] = None
    limit: int = 10
    min_score: float = 3.5


class ScoutSignalsRequest(BaseModel):
    """Request to fetch market signals."""

    company_name: Optional[str] = None
    industry: Optional[str] = None


class NavigatorFindPathRequest(BaseModel):
    """Request to find connection paths between two people."""

    from_person: str
    to_person: str
    max_hops: int = 3


class NavigatorMapNetworkRequest(BaseModel):
    """Request to map network around a person."""

    person: str
    depth: int = 2


class NavigatorSuggestIntroRequest(BaseModel):
    """Request to suggest an introduction path and draft."""

    from_person: str
    to_person: str
    context: str = ""


class NavigatorListContactsRequest(BaseModel):
    """Request to list contacts."""

    filter: str = "all"  # all, firm, external
    company: Optional[str] = None


# =============================================================================
# LegalGuardian Request Models
# =============================================================================


class GuardianAnalyzeRequest(BaseModel):
    """Request to analyze a contract for legal risks."""

    contract_id: Optional[str] = None
    contract_text: Optional[str] = None
    contract_name: str = "Unknown Contract"
    contract_type: str = "unknown"
    counterparty: str = "Unknown"


class GuardianCheckClauseRequest(BaseModel):
    """Request to check for a specific clause type."""

    clause_type: str = "change_of_control"


# =============================================================================
# QuantStrategist Request Models
# =============================================================================


class StrategistLBORequest(BaseModel):
    """Request to build an LBO model."""

    ltm_revenue: float
    ltm_ebitda: float
    entry_multiple: float = 8.0
    exit_multiple: float = 8.0
    holding_period: int = 5
    leverage: float = 4.0
    revenue_growth: float = 0.05
    net_debt: float = 0.0
    interest_rate: float = 0.08
    tax_rate: float = 0.25


class StrategistSensitivityRequest(BaseModel):
    """Request to generate sensitivity tables."""

    ltm_revenue: float
    ltm_ebitda: float
    entry_multiple: float = 8.0
    exit_multiple: float = 8.0
    sensitivity_type: str = "entry_exit"  # entry_exit, growth_leverage, all
    metric: str = "irr"  # irr or moic


class StrategistAnalyzeRequest(BaseModel):
    """Request for full analysis with model, sensitivity, and commentary."""

    company_name: str
    ltm_revenue: float
    ltm_ebitda: float
    entry_multiple: float = 8.0
    exit_multiple: float = 8.0
    holding_period: int = 5
    leverage: float = 4.0
    revenue_growth: float = 0.05


class StrategistQuickCalcRequest(BaseModel):
    """Request for quick IRR/MOIC calculation."""

    entry_equity: float
    exit_equity: float
    holding_period: int = 5


# =============================================================================
# AdversarialIC Request Models
# =============================================================================


class ICDealContext(BaseModel):
    """Deal context for IC debate."""

    company_name: str
    industry: str = "Technology"
    revenue: float = 100.0
    ebitda: float = 20.0
    entry_multiple: float = 8.0
    exit_multiple: float = 8.0
    irr: str = "20%"
    moic: str = "2.5x"
    strengths: list[str] = []
    growth_rate: str = "5"


class ICMemoRequest(BaseModel):
    """Request to generate investment memo."""

    deal_context: ICDealContext


class ICBearRequest(BaseModel):
    """Request to generate bear case."""

    deal_context: ICDealContext
    bull_memo: Optional[dict] = None


class ICDebateRequest(BaseModel):
    """Request to run full IC debate."""

    deal_context: ICDealContext


# =============================================================================
# ValueCreationMonitor Request Models
# =============================================================================


class VCMAnalyzeRequest(BaseModel):
    """Request to analyze a portfolio company."""

    company_id: str
    period: str = "quarterly"  # quarterly, annual, ytd


class VCMAlertsRequest(BaseModel):
    """Request to get portfolio alerts."""

    severity: Optional[str] = None  # critical, high, medium, low
    company_id: Optional[str] = None


class VCMReportRequest(BaseModel):
    """Request to generate LP report."""

    quarter: int = 4
    year: int = 2025
    fund_name: str = "PE-Nexus Fund I"


class VCMListCompaniesRequest(BaseModel):
    """Request to list portfolio companies."""

    status: Optional[str] = None  # on_track, watch, at_risk, outperforming
    industry: Optional[str] = None


class AgentTaskResponse(BaseModel):
    """Response for agent task submission."""

    task_id: str
    agent_name: str
    status: str
    message: str


# Store for tracking running tasks
_running_tasks: dict[str, dict] = {}


@router.post("/forensic/extract", response_model=AgentTaskResponse)
async def extract_financials(
    request: ExtractFinancialsRequest,
    background_tasks: BackgroundTasks,
    db: DBSession,
    event_bus: EventBusDep,
):
    """
    Extract financial data from a document using the Forensic Analyst agent.

    This runs the extraction asynchronously and returns a task ID.
    """
    # Verify document exists
    doc_query = select(DocumentModel).where(DocumentModel.id == str(request.document_id))
    doc_result = await db.execute(doc_query)
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify deal exists
    deal_query = select(DealModel).where(DealModel.id == str(request.deal_id))
    deal_result = await db.execute(deal_query)
    deal = deal_result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Create task
    agent = create_forensic_analyst()
    task_id = f"forensic_{request.document_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Track task (thread-safe)
    async with _tasks_lock:
        _running_tasks[task_id] = {
            "status": "running",
            "agent_name": agent.name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "document_id": str(request.document_id),
            "deal_id": str(request.deal_id),
        }

    # Run in background
    background_tasks.add_task(
        _run_forensic_extraction,
        task_id=task_id,
        agent=agent,
        document=document,
        deal_id=request.deal_id,
    )

    return AgentTaskResponse(
        task_id=task_id,
        agent_name=agent.name,
        status="running",
        message="Extraction started. Use /agents/tasks/{task_id} to check status.",
    )


async def _run_forensic_extraction(
    task_id: str,
    agent: ForensicAnalystAgent,
    document: DocumentModel,
    deal_id: UUID,
):
    """Background task for forensic extraction."""
    try:
        # Run the agent
        result = await agent.run(
            input_data={
                "file_path": document.file_path,
                "document_id": document.id,
                "document_type": document.document_type,
            },
            deal_id=deal_id,
            document_id=UUID(document.id),
        )

        # Update task status (thread-safe)
        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "completed" if result.success else "failed"
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            _running_tasks[task_id]["result"] = result.to_dict()

    except Exception as e:
        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "failed"
            _running_tasks[task_id]["error"] = str(e)
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of an agent task."""
    async with _tasks_lock:
        if task_id not in _running_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        return _running_tasks[task_id].copy()


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
):
    """List recent agent tasks."""
    async with _tasks_lock:
        tasks = list(_running_tasks.values())

    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    # Sort by started_at descending
    tasks.sort(key=lambda t: t.get("started_at", ""), reverse=True)

    return tasks[:limit]


@router.post("/forensic/extract-sync")
async def extract_financials_sync(
    request: ExtractFinancialsRequest,
    db: DBSession,
):
    """
    Extract financial data synchronously (blocking).

    Use this for testing or when immediate results are needed.
    """
    # Verify document exists
    doc_query = select(DocumentModel).where(DocumentModel.id == str(request.document_id))
    doc_result = await db.execute(doc_query)
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify deal exists
    deal_query = select(DealModel).where(DealModel.id == str(request.deal_id))
    deal_result = await db.execute(deal_query)
    deal = deal_result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Run agent synchronously
    agent = create_forensic_analyst()

    try:
        result = await agent.run(
            input_data={
                "file_path": document.file_path,
                "document_id": document.id,
                "document_type": document.document_type,
            },
            deal_id=request.deal_id,
            document_id=UUID(document.id),
        )

        # If successful and has financials, save to database
        if result.success and result.output_data.get("financials"):
            financials_data = result.output_data["financials"]
            await _save_financials_to_db(
                db=db,
                deal_id=str(request.deal_id),
                financials_data=financials_data,
            )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


async def _save_financials_to_db(
    db: DBSession,
    deal_id: str,
    financials_data: dict,
):
    """Save extracted financials to database."""
    fiscal_year = financials_data.get("fiscal_year", datetime.now().year)
    fiscal_period = financials_data.get("fiscal_period", "FY")

    # Check if record exists
    query = select(FinancialModel).where(
        FinancialModel.deal_id == deal_id,
        FinancialModel.fiscal_year == fiscal_year,
        FinancialModel.fiscal_period == fiscal_period,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    def get_value(key: str) -> Optional[float]:
        val = financials_data.get(key)
        if isinstance(val, dict):
            return val.get("value")
        return val

    def get_source(key: str) -> Optional[dict]:
        val = financials_data.get(key)
        if isinstance(val, dict):
            return val.get("source")
        return None

    if existing:
        # Update existing
        existing.revenue = get_value("revenue")
        existing.revenue_source = get_source("revenue")
        existing.ebitda = get_value("ebitda")
        existing.ebitda_source = get_source("ebitda")
        existing.net_income = get_value("net_income")
        existing.net_income_source = get_source("net_income")
        # ... add other fields as needed
    else:
        # Create new
        financial = FinancialModel(
            deal_id=deal_id,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            revenue=get_value("revenue"),
            revenue_source=get_source("revenue"),
            ebitda=get_value("ebitda"),
            ebitda_source=get_source("ebitda"),
            net_income=get_value("net_income"),
            net_income_source=get_source("net_income"),
        )
        db.add(financial)

    await db.commit()


# =============================================================================
# IntelligenceScout Agent Routes
# =============================================================================


@router.post("/scout/analyze", response_model=AgentTaskResponse)
async def scout_analyze_company(
    request: ScoutAnalyzeRequest,
    background_tasks: BackgroundTasks,
    event_bus: EventBusDep,
):
    """
    Analyze a specific company for deal potential.

    The Scout agent will:
    - Gather news signals about the company
    - Analyze job posting patterns
    - Consider macroeconomic context
    - Compute a composite deal score with rationale
    """
    agent = IntelligenceScoutAgent()
    task_id = f"scout_analyze_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    async with _tasks_lock:
        _running_tasks[task_id] = {
            "status": "running",
            "agent_name": agent.name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "company_name": request.company_name,
            "deal_id": str(request.deal_id) if request.deal_id else None,
        }

    background_tasks.add_task(
        _run_scout_analysis,
        task_id=task_id,
        agent=agent,
        company_name=request.company_name,
        industry=request.industry,
        sub_sector=request.sub_sector,
        deal_id=request.deal_id,
    )

    return AgentTaskResponse(
        task_id=task_id,
        agent_name=agent.name,
        status="running",
        message=f"Analyzing {request.company_name}. Use /agents/tasks/{task_id} to check status.",
    )


async def _run_scout_analysis(
    task_id: str,
    agent: IntelligenceScoutAgent,
    company_name: str,
    industry: str,
    sub_sector: str,
    deal_id: Optional[UUID],
):
    """Background task for scout analysis."""
    try:
        result = await agent.analyze_company(
            company_name=company_name,
            industry=industry,
            sub_sector=sub_sector,
            deal_id=deal_id,
        )

        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "completed" if result.success else "failed"
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            _running_tasks[task_id]["result"] = result.to_dict()

    except Exception as e:
        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "failed"
            _running_tasks[task_id]["error"] = str(e)
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        await agent.close()


@router.post("/scout/analyze-sync")
async def scout_analyze_company_sync(request: ScoutAnalyzeRequest):
    """
    Analyze a company synchronously (blocking).

    Returns the full scored deal analysis immediately.
    """
    agent = IntelligenceScoutAgent()

    try:
        result = await agent.analyze_company(
            company_name=request.company_name,
            industry=request.industry,
            sub_sector=request.sub_sector,
            deal_id=request.deal_id,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        await agent.close()


@router.post("/scout/scan", response_model=AgentTaskResponse)
async def scout_scan_industry(
    request: ScoutScanRequest,
    background_tasks: BackgroundTasks,
):
    """
    Scan an industry for potential acquisition opportunities.

    Returns a ranked list of companies with deal scores.
    """
    agent = IntelligenceScoutAgent(min_score_threshold=request.min_score)
    task_id = f"scout_scan_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    async with _tasks_lock:
        _running_tasks[task_id] = {
            "status": "running",
            "agent_name": agent.name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "industry": request.industry or "all",
            "limit": request.limit,
        }

    background_tasks.add_task(
        _run_scout_scan,
        task_id=task_id,
        agent=agent,
        industry=request.industry,
        limit=request.limit,
    )

    return AgentTaskResponse(
        task_id=task_id,
        agent_name=agent.name,
        status="running",
        message=f"Scanning {request.industry or 'all industries'}. Use /agents/tasks/{task_id} to check status.",
    )


async def _run_scout_scan(
    task_id: str,
    agent: IntelligenceScoutAgent,
    industry: Optional[str],
    limit: int,
):
    """Background task for industry scan."""
    try:
        result = await agent.scan_industry(industry=industry, limit=limit)

        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "completed" if result.success else "failed"
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            _running_tasks[task_id]["result"] = result.to_dict()

    except Exception as e:
        async with _tasks_lock:
            _running_tasks[task_id]["status"] = "failed"
            _running_tasks[task_id]["error"] = str(e)
            _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        await agent.close()


@router.post("/scout/scan-sync")
async def scout_scan_industry_sync(request: ScoutScanRequest):
    """
    Scan an industry synchronously (blocking).

    Returns ranked opportunities immediately.
    """
    agent = IntelligenceScoutAgent(min_score_threshold=request.min_score)

    try:
        result = await agent.scan_industry(industry=request.industry, limit=request.limit)

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    finally:
        await agent.close()


@router.get("/scout/signals")
async def scout_get_signals(
    company_name: Optional[str] = None,
    industry: Optional[str] = None,
):
    """
    Get recent market signals without scoring.

    Useful for monitoring and research purposes.
    """
    agent = IntelligenceScoutAgent()

    try:
        result = await agent.get_market_signals(
            company_name=company_name,
            industry=industry,
        )

        return {
            "success": result.success,
            "signals": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch signals: {str(e)}")
    finally:
        await agent.close()


# =============================================================================
# RelationshipNavigator Agent Routes
# =============================================================================


@router.post("/navigator/find-path", response_model=AgentTaskResponse)
async def navigator_find_path(
    request: NavigatorFindPathRequest,
    background_tasks: BackgroundTasks,
):
    """
    Find connection paths between two people.

    The Navigator agent will:
    - Search the relationship graph for paths up to max_hops
    - Calculate path strength based on relationship types
    - Return ranked paths with introduction chains
    """
    agent = create_navigator()
    task_id = f"navigator_path_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    _running_tasks[task_id] = {
        "status": "running",
        "agent_name": agent.name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "from_person": request.from_person,
        "to_person": request.to_person,
    }

    background_tasks.add_task(
        _run_navigator_find_path,
        task_id=task_id,
        agent=agent,
        from_person=request.from_person,
        to_person=request.to_person,
        max_hops=request.max_hops,
    )

    return AgentTaskResponse(
        task_id=task_id,
        agent_name=agent.name,
        status="running",
        message=f"Finding paths from {request.from_person} to {request.to_person}. Use /agents/tasks/{task_id} to check status.",
    )


async def _run_navigator_find_path(
    task_id: str,
    agent: RelationshipNavigatorAgent,
    from_person: str,
    to_person: str,
    max_hops: int,
):
    """Background task for path finding."""
    try:
        result = await agent.find_path(
            from_person=from_person,
            to_person=to_person,
            max_hops=max_hops,
        )

        _running_tasks[task_id]["status"] = "completed" if result.success else "failed"
        _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _running_tasks[task_id]["result"] = result.to_dict()

    except Exception as e:
        _running_tasks[task_id]["status"] = "failed"
        _running_tasks[task_id]["error"] = str(e)
        _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.post("/navigator/find-path-sync")
async def navigator_find_path_sync(request: NavigatorFindPathRequest):
    """
    Find connection paths synchronously (blocking).

    Returns paths immediately for quick lookups.
    """
    agent = create_navigator()

    try:
        result = await agent.find_path(
            from_person=request.from_person,
            to_person=request.to_person,
            max_hops=request.max_hops,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Path finding failed: {str(e)}")


@router.post("/navigator/map-network-sync")
async def navigator_map_network_sync(request: NavigatorMapNetworkRequest):
    """
    Map the network around a person synchronously.

    Returns network graph for visualization.
    """
    agent = create_navigator()

    try:
        result = await agent.map_network(
            person=request.person,
            depth=request.depth,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network mapping failed: {str(e)}")


@router.post("/navigator/suggest-intro", response_model=AgentTaskResponse)
async def navigator_suggest_intro(
    request: NavigatorSuggestIntroRequest,
    background_tasks: BackgroundTasks,
):
    """
    Find best path and generate introduction draft.

    The Navigator agent will:
    - Find the strongest connection path
    - Generate a personalized introduction request email
    - Provide talking points for the introducer
    """
    agent = create_navigator()
    task_id = f"navigator_intro_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    _running_tasks[task_id] = {
        "status": "running",
        "agent_name": agent.name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "from_person": request.from_person,
        "to_person": request.to_person,
    }

    background_tasks.add_task(
        _run_navigator_suggest_intro,
        task_id=task_id,
        agent=agent,
        from_person=request.from_person,
        to_person=request.to_person,
        context=request.context,
    )

    return AgentTaskResponse(
        task_id=task_id,
        agent_name=agent.name,
        status="running",
        message=f"Generating introduction suggestion. Use /agents/tasks/{task_id} to check status.",
    )


async def _run_navigator_suggest_intro(
    task_id: str,
    agent: RelationshipNavigatorAgent,
    from_person: str,
    to_person: str,
    context: str,
):
    """Background task for introduction suggestion."""
    try:
        result = await agent.suggest_introduction(
            from_person=from_person,
            to_person=to_person,
            context=context,
        )

        _running_tasks[task_id]["status"] = "completed" if result.success else "failed"
        _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _running_tasks[task_id]["result"] = result.to_dict()

    except Exception as e:
        _running_tasks[task_id]["status"] = "failed"
        _running_tasks[task_id]["error"] = str(e)
        _running_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.post("/navigator/suggest-intro-sync")
async def navigator_suggest_intro_sync(request: NavigatorSuggestIntroRequest):
    """
    Generate introduction suggestion synchronously.

    Returns path and draft email immediately.
    """
    agent = create_navigator()

    try:
        result = await agent.suggest_introduction(
            from_person=request.from_person,
            to_person=request.to_person,
            context=request.context,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Introduction suggestion failed: {str(e)}")


@router.get("/navigator/contacts")
async def navigator_list_contacts(
    filter: str = "all",
    company: Optional[str] = None,
):
    """
    List available contacts in the network.

    filter options: all, firm, external
    """
    agent = create_navigator()

    try:
        result = await agent.list_contacts(
            filter_type=filter,
            company=company,
        )

        return {
            "success": result.success,
            "contacts": result.output_data.get("contacts", []),
            "total_count": result.output_data.get("total_count", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list contacts: {str(e)}")


# =============================================================================
# LegalGuardian Agent Routes
# =============================================================================


@router.post("/guardian/analyze-sync")
async def guardian_analyze_contract_sync(request: GuardianAnalyzeRequest):
    """
    Analyze a contract for legal risks synchronously.

    The Guardian agent will:
    - Detect Change of Control clauses
    - Identify assignment restrictions
    - Find termination rights and consent requirements
    - Score risks by severity
    """
    agent = create_guardian()

    try:
        result = await agent.analyze_contract(
            contract_id=request.contract_id,
            contract_text=request.contract_text,
            contract_name=request.contract_name,
            contract_type=request.contract_type,
            counterparty=request.counterparty,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/guardian/analyze-all-sync")
async def guardian_analyze_all_sync(contract_type: Optional[str] = None):
    """
    Analyze all contracts, optionally filtered by type.

    contract_type options: customer_agreement, employment, vendor, lease, ip_license, loan
    """
    agent = create_guardian()

    try:
        result = await agent.analyze_all(contract_type=contract_type)

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/guardian/check-clause-sync")
async def guardian_check_clause_sync(request: GuardianCheckClauseRequest):
    """
    Check for a specific clause type across all contracts.

    clause_type options: change_of_control, assignment_restriction, termination_rights,
    non_compete, non_solicitation, personal_guarantee, acceleration_clause, etc.
    """
    agent = create_guardian()

    try:
        result = await agent.check_clause(clause_type=request.clause_type)

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clause check failed: {str(e)}")


@router.get("/guardian/contracts")
async def guardian_list_contracts():
    """List all available contracts for analysis."""
    agent = create_guardian()

    try:
        result = await agent.list_contracts()

        return {
            "success": result.success,
            "contracts": result.output_data.get("contracts", []),
            "total_count": result.output_data.get("total_contracts", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list contracts: {str(e)}")


# =============================================================================
# QuantStrategist Agent Routes
# =============================================================================


@router.post("/strategist/lbo-sync")
async def strategist_build_lbo_sync(request: StrategistLBORequest):
    """
    Build an LBO model with specified assumptions.

    Returns full model with sources/uses, projections, and returns.
    """
    agent = create_strategist()

    try:
        result = await agent.build_lbo(
            ltm_revenue=request.ltm_revenue,
            ltm_ebitda=request.ltm_ebitda,
            entry_multiple=request.entry_multiple,
            exit_multiple=request.exit_multiple,
            holding_period=request.holding_period,
            leverage=request.leverage,
            revenue_growth=request.revenue_growth,
            net_debt=request.net_debt,
            interest_rate=request.interest_rate,
            tax_rate=request.tax_rate,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LBO model failed: {str(e)}")


@router.post("/strategist/sensitivity-sync")
async def strategist_sensitivity_sync(request: StrategistSensitivityRequest):
    """
    Generate sensitivity tables for LBO returns.

    sensitivity_type options: entry_exit, growth_leverage, all
    metric options: irr, moic
    """
    agent = create_strategist()

    try:
        result = await agent.generate_sensitivity(
            ltm_revenue=request.ltm_revenue,
            ltm_ebitda=request.ltm_ebitda,
            entry_multiple=request.entry_multiple,
            exit_multiple=request.exit_multiple,
            sensitivity_type=request.sensitivity_type,
            metric=request.metric,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sensitivity analysis failed: {str(e)}")


@router.post("/strategist/analyze-sync")
async def strategist_analyze_sync(request: StrategistAnalyzeRequest):
    """
    Full analysis with model, sensitivity tables, and commentary.

    Returns complete LBO analysis with investment recommendation.
    """
    agent = create_strategist()

    try:
        result = await agent.analyze(
            company_name=request.company_name,
            ltm_revenue=request.ltm_revenue,
            ltm_ebitda=request.ltm_ebitda,
            entry_multiple=request.entry_multiple,
            exit_multiple=request.exit_multiple,
            holding_period=request.holding_period,
            leverage=request.leverage,
            revenue_growth=request.revenue_growth,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/strategist/quick-calc-sync")
async def strategist_quick_calc_sync(request: StrategistQuickCalcRequest):
    """
    Quick IRR/MOIC calculation from entry and exit equity.

    Simple returns calculation without full model.
    """
    agent = create_strategist()

    try:
        result = await agent.quick_calc(
            entry_equity=request.entry_equity,
            exit_equity=request.exit_equity,
            holding_period=request.holding_period,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


# =============================================================================
# AdversarialIC Agent Routes
# =============================================================================


@router.post("/ic/memo-sync")
async def ic_generate_memo_sync(request: ICMemoRequest):
    """
    Generate investment memo (bull case).

    The Bull agent will create a compelling investment memorandum.
    """
    agent = create_ic_agent()

    try:
        result = await agent.generate_memo(deal_context=request.deal_context.model_dump())

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memo generation failed: {str(e)}")


@router.post("/ic/bear-sync")
async def ic_generate_bear_sync(request: ICBearRequest):
    """
    Generate risk assessment (bear case).

    The Bear agent will identify risks and counter-arguments.
    """
    agent = create_ic_agent()

    try:
        result = await agent.generate_bear_case(
            deal_context=request.deal_context.model_dump(),
            bull_memo=request.bull_memo,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bear case generation failed: {str(e)}")


@router.post("/ic/debate-sync")
async def ic_run_debate_sync(request: ICDebateRequest):
    """
    Run full IC debate with bull/bear synthesis.

    Orchestrates bull and bear agents, then synthesizes into final recommendation.
    """
    agent = create_ic_agent()

    try:
        result = await agent.run_debate(deal_context=request.deal_context.model_dump())

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IC debate failed: {str(e)}")


# =============================================================================
# ValueCreationMonitor Agent Routes
# =============================================================================


@router.get("/monitor/dashboard")
async def vcm_get_dashboard():
    """
    Get portfolio-level dashboard summary.

    Returns:
    - Portfolio summary statistics
    - Company-level status overview
    - Aggregate alerts count
    - Revenue/EBITDA trends
    """
    agent = create_vcm()

    try:
        result = await agent.get_dashboard()

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")


@router.post("/monitor/analyze-sync")
async def vcm_analyze_company_sync(request: VCMAnalyzeRequest):
    """
    Analyze KPIs for a specific portfolio company.

    Returns comprehensive KPI analysis including:
    - Financial variances (actual vs budget)
    - Operational KPI performance
    - Trend detection
    - Generated alerts
    - LLM-enhanced commentary (if available)
    """
    agent = create_vcm()

    try:
        result = await agent.analyze_company(
            company_id=request.company_id,
            period=request.period,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/monitor/alerts-sync")
async def vcm_get_alerts_sync(request: VCMAlertsRequest):
    """
    Get alerts across portfolio companies.

    Optionally filter by:
    - severity: critical, high, medium, low
    - company_id: specific company

    Returns alerts sorted by severity (critical first).
    """
    agent = create_vcm()

    try:
        result = await agent.get_alerts(
            severity=request.severity,
            company_id=request.company_id,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alerts query failed: {str(e)}")


@router.get("/monitor/alerts")
async def vcm_get_all_alerts(
    severity: Optional[str] = None,
    company_id: Optional[str] = None,
):
    """
    Get alerts across portfolio (GET endpoint).

    Query params:
    - severity: Filter by severity level
    - company_id: Filter by company
    """
    agent = create_vcm()

    try:
        result = await agent.get_alerts(
            severity=severity,
            company_id=company_id,
        )

        return {
            "success": result.success,
            "alerts": result.output_data.get("alerts", []),
            "total_count": result.output_data.get("total_alerts", 0),
            "critical_count": result.output_data.get("critical_count", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alerts query failed: {str(e)}")


@router.post("/monitor/report-sync")
async def vcm_generate_report_sync(request: VCMReportRequest):
    """
    Generate quarterly LP report.

    Creates a comprehensive report including:
    - Executive summary
    - Portfolio metrics
    - Individual company updates
    - Value creation narrative
    - Outlook and milestones

    Note: LP reports always require human review before distribution.
    """
    agent = create_vcm()

    try:
        result = await agent.generate_lp_report(
            quarter=request.quarter,
            year=request.year,
            fund_name=request.fund_name,
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "duration_seconds": result.duration_seconds,
            "requires_review": result.requires_review,
            "output": result.output_data,
            "errors": result.errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/monitor/company/{company_id}")
async def vcm_get_company_detail(company_id: str):
    """
    Get detailed information for a specific portfolio company.

    Returns:
    - Company profile
    - Monthly financials (actuals and budget)
    - Operational KPIs
    - Value creation initiatives
    """
    agent = create_vcm()

    try:
        result = await agent.get_company_detail(company_id=company_id)

        if not result.success:
            raise HTTPException(
                status_code=404,
                detail=result.errors[0] if result.errors else "Company not found"
            )

        return {
            "success": result.success,
            "company": result.output_data.get("company", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")


@router.get("/monitor/companies")
async def vcm_list_companies(
    status: Optional[str] = None,
    industry: Optional[str] = None,
):
    """
    List all portfolio companies.

    Query params:
    - status: Filter by status (on_track, watch, at_risk, outperforming)
    - industry: Filter by industry (Technology, Healthcare, etc.)
    """
    agent = create_vcm()

    try:
        result = await agent.list_companies(
            status=status,
            industry=industry,
        )

        return {
            "success": result.success,
            "companies": result.output_data.get("companies", []),
            "total_count": result.output_data.get("total_count", 0),
            "filters_applied": result.output_data.get("filters_applied", {}),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


@router.post("/monitor/companies")
async def vcm_list_companies_post(request: VCMListCompaniesRequest):
    """
    List portfolio companies (POST endpoint with filters in body).
    """
    agent = create_vcm()

    try:
        result = await agent.list_companies(
            status=request.status,
            industry=request.industry,
        )

        return {
            "success": result.success,
            "companies": result.output_data.get("companies", []),
            "total_count": result.output_data.get("total_count", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


# =============================================================================
# Peer Review Routes
# =============================================================================


@router.post("/review/{task_id}")
async def request_peer_review(
    task_id: str,
    review_type: str = "validation",
):
    """
    Request a peer review of an agent task output.

    review_type options: validation, verification, approval
    """
    async with _tasks_lock:
        if task_id not in _running_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        task = _running_tasks[task_id].copy()

    if task.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed (status: {task.get('status')})"
        )

    if "result" not in task:
        raise HTTPException(status_code=400, detail="Task has no result to review")

    # Get peer review service
    peer_review = get_peer_review_service()

    # Create AgentOutput from stored result
    from src.agents.base import AgentOutput
    result_data = task["result"]

    output = AgentOutput(
        agent_name=result_data["agent_name"],
        task_id=result_data["task_id"],
        success=result_data["success"],
        output_data=result_data["output_data"],
        extractions=result_data.get("extractions", []),
        errors=result_data.get("errors", []),
        duration_seconds=result_data.get("duration_seconds"),
        requires_review=result_data.get("requires_review", False),
    )

    # Perform quick validation (no reviewer agent)
    try:
        review_type_enum = ReviewType(review_type)
    except ValueError:
        review_type_enum = ReviewType.VALIDATION

    review_result = await peer_review.quick_validate(output)

    return {
        "review_id": str(review_result.review_id),
        "task_id": task_id,
        "decision": review_result.decision.value,
        "approved": review_result.approved,
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "description": i.description,
            }
            for i in review_result.issues
        ],
        "notes": review_result.notes,
        "confidence": review_result.confidence,
    }


@router.get("/available")
async def list_available_agents():
    """List all available agents and their capabilities."""
    return {
        "agents": [
            {
                "name": "ForensicAnalyst",
                "description": "Extracts and validates financial data from CIMs and documents",
                "capabilities": [
                    "PDF text extraction with bounding boxes",
                    "Financial statement parsing",
                    "Cross-statement reconciliation",
                    "EBITDA adjustment identification",
                ],
                "endpoints": [
                    "/agents/forensic/extract",
                    "/agents/forensic/extract-sync",
                ],
            },
            {
                "name": "IntelligenceScout",
                "description": "Identifies potential acquisition targets from market signals",
                "status": "Active",
                "capabilities": [
                    "News monitoring and sentiment analysis",
                    "Job posting analysis for growth signals",
                    "Macro-economic data integration",
                    "Composite deal scoring",
                    "LLM-enhanced investment thesis generation",
                ],
                "endpoints": [
                    "/agents/scout/analyze",
                    "/agents/scout/analyze-sync",
                    "/agents/scout/scan",
                    "/agents/scout/scan-sync",
                    "/agents/scout/signals",
                ],
            },
            {
                "name": "RelationshipNavigator",
                "description": "Maps network connections to find warm introduction paths",
                "status": "Active",
                "capabilities": [
                    "Network graph traversal (up to 3 hops)",
                    "Connection strength scoring",
                    "Introduction draft generation",
                    "Network visualization data",
                ],
                "endpoints": [
                    "/agents/navigator/find-path",
                    "/agents/navigator/find-path-sync",
                    "/agents/navigator/map-network-sync",
                    "/agents/navigator/suggest-intro",
                    "/agents/navigator/suggest-intro-sync",
                    "/agents/navigator/contacts",
                ],
            },
            {
                "name": "LegalGuardian",
                "description": "Analyzes contracts and VDR documents for legal risks",
                "status": "Active",
                "capabilities": [
                    "Change of Control clause detection",
                    "Assignment restriction analysis",
                    "Non-compete and termination rights identification",
                    "Personal guarantee and acceleration clause detection",
                    "Risk scoring with deal impact assessment",
                ],
                "endpoints": [
                    "/agents/guardian/analyze-sync",
                    "/agents/guardian/analyze-all-sync",
                    "/agents/guardian/check-clause-sync",
                    "/agents/guardian/contracts",
                ],
            },
            {
                "name": "QuantStrategist",
                "description": "Builds financial models and sensitivity analyses",
                "status": "Active",
                "capabilities": [
                    "LBO model generation with sources/uses",
                    "IRR/MOIC calculations",
                    "Multi-year financial projections",
                    "Entry/exit multiple sensitivity tables",
                    "Growth/leverage sensitivity analysis",
                    "Value creation attribution",
                ],
                "endpoints": [
                    "/agents/strategist/lbo-sync",
                    "/agents/strategist/sensitivity-sync",
                    "/agents/strategist/analyze-sync",
                    "/agents/strategist/quick-calc-sync",
                ],
            },
            {
                "name": "AdversarialIC",
                "description": "Bull/Bear debate for investment committee",
                "status": "Active",
                "capabilities": [
                    "Investment memo generation (bull case)",
                    "Risk assessment generation (bear case)",
                    "Counter-argument development",
                    "Bull/Bear debate orchestration",
                    "Synthesis and final recommendation",
                ],
                "endpoints": [
                    "/agents/ic/memo-sync",
                    "/agents/ic/bear-sync",
                    "/agents/ic/debate-sync",
                ],
            },
            {
                "name": "ValueCreationMonitor",
                "description": "Monitors portfolio company performance and generates LP reports",
                "status": "Active",
                "capabilities": [
                    "Portfolio dashboard with status overview",
                    "KPI tracking and variance analysis",
                    "Alert generation (critical/high/medium/low)",
                    "Trend detection (revenue, margin, cash)",
                    "Value creation initiative tracking",
                    "Quarterly LP report generation",
                    "LLM-enhanced commentary",
                ],
                "endpoints": [
                    "/agents/monitor/dashboard",
                    "/agents/monitor/analyze-sync",
                    "/agents/monitor/alerts",
                    "/agents/monitor/alerts-sync",
                    "/agents/monitor/report-sync",
                    "/agents/monitor/company/{company_id}",
                    "/agents/monitor/companies",
                ],
            },
        ]
    }
