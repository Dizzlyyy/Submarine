"""API tests for the Probe_API FastAPI endpoints.

Tests use TestClient with a mocked ProbeEngineManager injected via
app.dependency_overrides[get_engine].
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from probe_api.main import app
from probe_api.models.schemas import MovementRecord, MoveResponse, Position
from probe_api.routers.probe import get_engine


def make_client(mock_engine: MagicMock) -> TestClient:
    app.dependency_overrides[get_engine] = lambda: mock_engine
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /move
# ---------------------------------------------------------------------------

def test_move_valid_instruction_returns_200_with_position_and_message():
    mock_engine = MagicMock()
    mock_engine.move.return_value = MoveResponse(
        position=Position(x=0, y=1), message="Moved up"
    )
    client = make_client(mock_engine)

    response = client.post("/move", json={"instruction": "go north"})

    assert response.status_code == 200
    body = response.json()
    assert body["position"] == {"x": 0, "y": 1}
    assert body["message"] == "Moved up"


def test_move_ambiguous_instruction_returns_200_with_clarification():
    mock_engine = MagicMock()
    mock_engine.move.return_value = MoveResponse(
        message="I couldn't determine a direction. Could you rephrase?"
    )
    client = make_client(mock_engine)

    response = client.post("/move", json={"instruction": "go somewhere"})

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert body["message"]  # non-empty


def test_move_invalid_instruction_returns_422():
    mock_engine = MagicMock()
    mock_engine.move.side_effect = HTTPException(
        status_code=422, detail="Input is not a movement instruction."
    )
    client = make_client(mock_engine)

    response = client.post("/move", json={"instruction": "what is the weather?"})

    assert response.status_code == 422


def test_move_blocked_move_returns_422_with_descriptive_detail():
    mock_engine = MagicMock()
    mock_engine.move.side_effect = HTTPException(
        status_code=422, detail="Cannot move up: obstacle at (0,1)"
    )
    client = make_client(mock_engine)

    response = client.post("/move", json={"instruction": "go up"})

    assert response.status_code == 422
    assert "Cannot move" in response.json()["detail"]


def test_move_llm_unavailable_returns_503():
    mock_engine = MagicMock()
    mock_engine.move.side_effect = HTTPException(
        status_code=503,
        detail="Intent parsing service unavailable. Please try again.",
    )
    client = make_client(mock_engine)

    response = client.post("/move", json={"instruction": "go north"})

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_move_missing_instruction_field_returns_422():
    mock_engine = MagicMock()
    client = make_client(mock_engine)

    response = client.post("/move", json={})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /position
# ---------------------------------------------------------------------------

def test_get_position_returns_200_with_coordinates():
    mock_engine = MagicMock()
    mock_engine.get_position.return_value = Position(x=3, y=7)
    client = make_client(mock_engine)

    response = client.get("/position")

    assert response.status_code == 200
    assert response.json() == {"x": 3, "y": 7}


# ---------------------------------------------------------------------------
# GET /movements
# ---------------------------------------------------------------------------

def test_get_movements_returns_200_with_list_of_records():
    mock_engine = MagicMock()
    record = MovementRecord(
        date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        from_position=Position(x=0, y=0),
        direction="up",
        to_position=Position(x=0, y=1),
        status="success",
    )
    mock_engine.get_movements.return_value = [record]
    client = make_client(mock_engine)

    response = client.get("/movements")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["direction"] == "up"
    assert body[0]["status"] == "success"


# ---------------------------------------------------------------------------
# get_engine() RuntimeError guard
# ---------------------------------------------------------------------------

def test_get_engine_raises_runtime_error_when_not_initialized():
    """Covers the `if _engine is None: raise RuntimeError` branch in get_engine()."""
    import probe_api.routers.probe as probe_module

    original = probe_module._engine
    try:
        probe_module._engine = None
        with pytest.raises(RuntimeError, match="Engine not initialized"):
            probe_module.get_engine()
    finally:
        probe_module._engine = original


def test_get_engine_returns_engine_when_initialized():
    """Covers the `return _engine` happy path in get_engine()."""
    import probe_api.routers.probe as probe_module

    mock_engine = MagicMock()
    original = probe_module._engine
    try:
        probe_module._engine = mock_engine
        result = probe_module.get_engine()
        assert result is mock_engine
    finally:
        probe_module._engine = original
