from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from probe_api.components.probe_engine_manager import ProbeEngineManager
from probe_api.models.schemas import MoveRequest, MoveResponse, MovementRecord, Position

router = APIRouter()

# Module-level engine instance (overridable in tests via app.dependency_overrides)
_engine: ProbeEngineManager | None = None


def get_engine() -> ProbeEngineManager:
    if _engine is None:
        raise RuntimeError("Engine not initialized")
    return _engine


def set_engine(engine: ProbeEngineManager) -> None:
    global _engine
    _engine = engine


@router.post("/move", response_model=MoveResponse)
def move(request: MoveRequest, engine: ProbeEngineManager = Depends(get_engine)) -> MoveResponse:
    return engine.move(request.instruction)


@router.get("/position", response_model=Position)
def get_position(engine: ProbeEngineManager = Depends(get_engine)) -> Position:
    return engine.get_position()


@router.get("/movements", response_model=list[MovementRecord])
def get_movements(engine: ProbeEngineManager = Depends(get_engine)) -> list[MovementRecord]:
    return engine.get_movements()
