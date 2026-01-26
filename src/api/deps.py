"""FastAPI dependency injection."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.events import EventBus, get_event_bus
from src.core.state_machine import DealStateMachine, get_state_machine
from src.core.traceability import TraceabilityEngine, get_traceability_engine
from src.db.database import get_session
from src.db.vector import VectorStore, get_vector_store


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session."""
    async for session in get_session():
        yield session


# Type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
StateMachineDep = Annotated[DealStateMachine, Depends(get_state_machine)]
TraceabilityDep = Annotated[TraceabilityEngine, Depends(get_traceability_engine)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]
