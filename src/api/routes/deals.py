"""Deal management API routes."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.deps import DBSession, EventBusDep, StateMachineDep
from src.db.models import DealModel, DocumentModel, FinancialModel
from src.schemas.deal import (
    DealCreate,
    DealStage,
    DealSummary,
    IndustryClassification,
    MasterDeal,
    TargetCompany,
)
from src.schemas.events import EventType

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/", response_model=dict)
async def create_deal(
    deal_data: DealCreate,
    db: DBSession,
    event_bus: EventBusDep,
):
    """Create a new deal."""
    deal_id = str(uuid4())

    # Create database model
    db_deal = DealModel(
        id=deal_id,
        deal_name=deal_data.deal_name,
        target_name=deal_data.target_name,
        target_description=deal_data.target_description,
        target_headquarters=deal_data.headquarters,
        industry_sector=deal_data.industry_sector,
        industry_sub_sector=deal_data.industry_sub_sector,
        source_type=deal_data.source_type,
        source_description=deal_data.source_description,
        stage=DealStage.SOURCING.value,
    )

    db.add(db_deal)
    await db.commit()
    await db.refresh(db_deal)

    # Publish event
    await event_bus.publish(
        event_type=EventType.DEAL_CREATED,
        deal_id=UUID(deal_id),
        payload={
            "deal_name": deal_data.deal_name,
            "target_name": deal_data.target_name,
        },
    )

    return {
        "deal_id": deal_id,
        "deal_name": deal_data.deal_name,
        "stage": DealStage.SOURCING.value,
        "message": "Deal created successfully",
    }


@router.get("/", response_model=list[DealSummary])
async def list_deals(
    db: DBSession,
    stage: Optional[DealStage] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all deals with optional filtering."""
    query = select(DealModel).order_by(DealModel.updated_at.desc())

    if stage:
        query = query.where(DealModel.stage == stage.value)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    deals = result.scalars().all()

    return [
        DealSummary(
            deal_id=UUID(deal.id),
            deal_name=deal.deal_name,
            target_name=deal.target_name,
            stage=DealStage(deal.stage),
            industry_sector=deal.industry_sector,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            deal_score=deal.deal_score,
        )
        for deal in deals
    ]


@router.get("/{deal_id}")
async def get_deal(
    deal_id: UUID,
    db: DBSession,
):
    """Get a specific deal with all details."""
    query = (
        select(DealModel)
        .options(
            selectinload(DealModel.documents),
            selectinload(DealModel.financials),
        )
        .where(DealModel.id == str(deal_id))
    )

    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Build MasterDeal response
    return {
        "deal_id": deal.id,
        "deal_name": deal.deal_name,
        "stage": deal.stage,
        "sub_stage": deal.sub_stage,
        "created_at": deal.created_at.isoformat(),
        "updated_at": deal.updated_at.isoformat(),
        "target": {
            "name": deal.target_name,
            "legal_name": deal.target_legal_name,
            "headquarters": deal.target_headquarters,
            "description": deal.target_description,
            "website": deal.target_website,
            "employee_count": deal.target_employee_count,
            "founded_year": deal.target_founded_year,
        },
        "industry": {
            "sector": deal.industry_sector,
            "sub_sector": deal.industry_sub_sector,
            "sic_code": deal.industry_sic_code,
            "naics_code": deal.industry_naics_code,
        },
        "geography": deal.geography,
        "enterprise_value": float(deal.enterprise_value) if deal.enterprise_value else None,
        "equity_value": float(deal.equity_value) if deal.equity_value else None,
        "entry_multiple": float(deal.entry_multiple) if deal.entry_multiple else None,
        "source_type": deal.source_type,
        "source_description": deal.source_description,
        "deal_score": deal.deal_score,
        "documents": [
            {
                "document_id": doc.id,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "processed": doc.processed,
            }
            for doc in deal.documents
        ],
        "financials": [
            {
                "fiscal_year": fin.fiscal_year,
                "fiscal_period": fin.fiscal_period,
                "revenue": float(fin.revenue) if fin.revenue else None,
                "ebitda": float(fin.ebitda) if fin.ebitda else None,
                "net_income": float(fin.net_income) if fin.net_income else None,
            }
            for fin in deal.financials
        ],
        "state_history": deal.state_history,
        "deal_team": deal.deal_team,
        "legal_flags": deal.legal_flags,
        "diligence_checklist": deal.diligence_checklist,
    }


@router.post("/{deal_id}/transition")
async def transition_deal(
    deal_id: UUID,
    to_stage: DealStage,
    transitioned_by: str,
    reason: str = "",
    db: DBSession = None,
    state_machine: StateMachineDep = None,
    event_bus: EventBusDep = None,
):
    """Transition a deal to a new stage."""
    # Get deal
    query = select(DealModel).where(DealModel.id == str(deal_id))
    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    current_stage = DealStage(deal.stage)

    # Check if transition is valid
    if not state_machine.can_transition(current_stage, to_stage):
        valid = state_machine.get_valid_transitions(current_stage)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition. Valid transitions from {current_stage.value}: "
                   f"{[s.value for s in valid]}",
        )

    # Create transition record
    transition = {
        "from_stage": current_stage.value,
        "to_stage": to_stage.value,
        "transitioned_at": datetime.now(timezone.utc).isoformat(),
        "transitioned_by": transitioned_by,
        "reason": reason,
    }

    # Update deal
    deal.stage = to_stage.value
    deal.updated_at = datetime.now(timezone.utc)

    history = deal.state_history or []
    history.append(transition)
    deal.state_history = history

    await db.commit()

    # Publish event
    event_type = state_machine.get_transition_event(to_stage)
    await event_bus.publish(
        event_type=event_type,
        deal_id=deal_id,
        payload={
            "from_stage": current_stage.value,
            "to_stage": to_stage.value,
            "transitioned_by": transitioned_by,
        },
    )

    return {
        "deal_id": str(deal_id),
        "previous_stage": current_stage.value,
        "new_stage": to_stage.value,
        "message": f"Deal transitioned to {to_stage.value}",
    }


@router.get("/{deal_id}/valid-transitions")
async def get_valid_transitions(
    deal_id: UUID,
    db: DBSession,
    state_machine: StateMachineDep,
):
    """Get valid next stages for a deal."""
    query = select(DealModel).where(DealModel.id == str(deal_id))
    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    current_stage = DealStage(deal.stage)
    valid = state_machine.get_valid_transitions(current_stage)

    return {
        "deal_id": str(deal_id),
        "current_stage": current_stage.value,
        "valid_transitions": [s.value for s in valid],
    }


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: UUID,
    db: DBSession,
):
    """Delete a deal (soft delete in production)."""
    query = select(DealModel).where(DealModel.id == str(deal_id))
    result = await db.execute(query)
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    await db.delete(deal)
    await db.commit()

    return {"message": f"Deal {deal_id} deleted"}
