"""Unit tests for ProbeEngineManager.

Mocks IntentParser and GridManager; uses a real ProbeStore (reset between tests).
Requirements: 1.2, 2.1, 2.2, 2.3, 3.1, 4.1
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from probe_api.components.intent_parser import ParseResult
from probe_api.components.probe_engine_manager import ProbeEngineManager
from probe_api.components.probe_store import ProbeStore
from probe_api.models.schemas import MovementRecord, Position


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store() -> ProbeStore:
    s = ProbeStore()
    s.reset()
    return s


@pytest.fixture()
def mock_parser() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def mock_grid() -> MagicMock:
    gm = MagicMock()
    gm.is_within_bounds.return_value = True
    gm.is_obstacle.return_value = False
    gm.is_cell_valid.return_value = True
    return gm


@pytest.fixture()
def engine(mock_grid, mock_parser, store) -> ProbeEngineManager:
    return ProbeEngineManager(
        grid_manager=mock_grid,
        intent_parser=mock_parser,
        probe_store=store,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_result(
    direction=None,
    is_ambiguous=False,
    is_invalid=False,
    clarification_message=None,
) -> ParseResult:
    return ParseResult(
        direction=direction,
        is_ambiguous=is_ambiguous,
        is_invalid=is_invalid,
        clarification_message=clarification_message,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestValidMove:
    """Requirement 2.1, 4.1 — valid move updates position and records success."""

    def test_position_updated(self, engine, mock_parser, store):
        mock_parser.parse.return_value = _parse_result(direction="up")

        response = engine.move("go up")

        assert response.position == Position(x=0, y=1)
        assert response.message == "Moved up"
        assert store.get_position() == Position(x=0, y=1)

    def test_success_movement_record_appended(self, engine, mock_parser, store):
        mock_parser.parse.return_value = _parse_result(direction="right")

        engine.move("go right")

        records = store.get_movements()
        assert len(records) == 1
        rec = records[0]
        assert rec.direction == "right"
        assert rec.from_position == Position(x=0, y=0)
        assert rec.to_position == Position(x=1, y=0)
        assert rec.status == "success"


class TestBlockedMoveObstacle:
    """Requirement 2.2, 2.3 — obstacle blocks move, raises 422, position unchanged."""

    def test_raises_422(self, engine, mock_parser, mock_grid, store):
        mock_parser.parse.return_value = _parse_result(direction="up")
        mock_grid.is_within_bounds.return_value = True
        mock_grid.is_obstacle.return_value = True
        mock_grid.is_cell_valid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            engine.move("go up")

        assert exc_info.value.status_code == 422

    def test_position_unchanged(self, engine, mock_parser, mock_grid, store):
        mock_parser.parse.return_value = _parse_result(direction="up")
        mock_grid.is_within_bounds.return_value = True
        mock_grid.is_obstacle.return_value = True
        mock_grid.is_cell_valid.return_value = False

        with pytest.raises(HTTPException):
            engine.move("go up")

        assert store.get_position() == Position(x=0, y=0)

    def test_failed_movement_record_appended(self, engine, mock_parser, mock_grid, store):
        mock_parser.parse.return_value = _parse_result(direction="up")
        mock_grid.is_within_bounds.return_value = True
        mock_grid.is_obstacle.return_value = True
        mock_grid.is_cell_valid.return_value = False

        with pytest.raises(HTTPException):
            engine.move("go up")

        records = store.get_movements()
        assert len(records) == 1
        assert records[0].status == "obstacle"


class TestBlockedMoveOutOfBounds:
    """Requirement 2.2 — out-of-bounds move raises 422, position unchanged."""

    def test_raises_422(self, engine, mock_parser, mock_grid, store):
        mock_parser.parse.return_value = _parse_result(direction="down")
        mock_grid.is_within_bounds.return_value = False
        mock_grid.is_obstacle.return_value = False
        mock_grid.is_cell_valid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            engine.move("go down")

        assert exc_info.value.status_code == 422

    def test_position_unchanged(self, engine, mock_parser, mock_grid, store):
        mock_parser.parse.return_value = _parse_result(direction="down")
        mock_grid.is_within_bounds.return_value = False
        mock_grid.is_obstacle.return_value = False
        mock_grid.is_cell_valid.return_value = False

        with pytest.raises(HTTPException):
            engine.move("go down")

        assert store.get_position() == Position(x=0, y=0)


class TestAmbiguousInstruction:
    """Requirement 1.2, 1.3 — ambiguous instruction returns 200 MoveResponse with message."""

    def test_returns_move_response_with_message(self, engine, mock_parser):
        mock_parser.parse.return_value = _parse_result(
            is_ambiguous=True,
            clarification_message="I couldn't determine a direction. Could you rephrase?",
        )

        response = engine.move("somewhere over there")

        assert response.position is None
        assert response.message == "I couldn't determine a direction. Could you rephrase?"

    def test_no_movement_record_appended(self, engine, mock_parser, store):
        mock_parser.parse.return_value = _parse_result(
            is_ambiguous=True,
            clarification_message="I couldn't determine a direction. Could you rephrase?",
        )

        engine.move("somewhere over there")

        assert store.get_movements() == []


class TestInvalidInstruction:
    """Requirement 1.2 — non-movement instruction raises 422."""

    def test_raises_422(self, engine, mock_parser):
        mock_parser.parse.return_value = _parse_result(is_invalid=True)

        with pytest.raises(HTTPException) as exc_info:
            engine.move("what is the weather?")

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "Input is not a movement instruction."

    def test_no_movement_record_appended(self, engine, mock_parser, store):
        mock_parser.parse.return_value = _parse_result(is_invalid=True)

        with pytest.raises(HTTPException):
            engine.move("what is the weather?")

        assert store.get_movements() == []


class TestGetMovements:
    """Requirement 3.1 — get_movements returns records sorted by date ascending."""

    def test_sorted_by_date_ascending(self, engine, store):
        now = datetime.now(timezone.utc)
        records = [
            MovementRecord(
                date=now + timedelta(seconds=2),
                from_position=Position(x=0, y=0),
                direction="up",
                to_position=Position(x=0, y=1),
                status="success",
            ),
            MovementRecord(
                date=now,
                from_position=Position(x=0, y=1),
                direction="right",
                to_position=Position(x=1, y=1),
                status="success",
            ),
            MovementRecord(
                date=now + timedelta(seconds=1),
                from_position=Position(x=1, y=1),
                direction="down",
                to_position=Position(x=1, y=0),
                status="success",
            ),
        ]
        for r in records:
            store.append_movement(r)

        result = engine.get_movements()

        dates = [r.date for r in result]
        assert dates == sorted(dates)

    def test_returns_all_records(self, engine, store):
        now = datetime.now(timezone.utc)
        for i in range(3):
            store.append_movement(
                MovementRecord(
                    date=now + timedelta(seconds=i),
                    from_position=Position(x=0, y=0),
                    direction="up",
                    to_position=Position(x=0, y=1),
                    status="success",
                )
            )

        assert len(engine.get_movements()) == 3
