"""Property-based tests for ProbeEngineManager (Property 5).

Uses a real GridManager and ProbeStore; mocks only IntentParser.parse.
"""
from __future__ import annotations

from unittest.mock import patch

from hypothesis import assume, given, settings
import hypothesis.strategies as st

from probe_api.components.grid_manager import GridManager
from probe_api.components.intent_parser import IntentParser, ParseResult
from probe_api.components.probe_engine_manager import ProbeEngineManager
from probe_api.components.probe_store import ProbeStore
from probe_api.models.schemas import Position

# Direction deltas: up=(0,+1), down=(0,-1), left=(-1,0), right=(+1,0)
DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}

# ---------------------------------------------------------------------------
# Property 5: Valid move round-trip — position is updated correctly
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 5: Valid move round-trip — position is updated correctly
# Validates: Requirements 2.1, 4.1


@given(
    x=st.integers(min_value=0, max_value=19),
    y=st.integers(min_value=0, max_value=19),
    direction=st.sampled_from(["up", "down", "left", "right"]),
)
@settings(max_examples=100)
def test_property_5_valid_move_round_trip(x: int, y: int, direction: str):
    """Property 5: For any probe position (x, y) and direction d such that the
    resulting cell is within bounds and not an obstacle, calling move() and then
    get_position() returns (x + Δx, y + Δy)."""
    dx, dy = DIRECTION_DELTAS[direction]
    new_x, new_y = x + dx, y + dy

    grid = GridManager()

    # Filter out cases where the starting cell itself is invalid
    assume(grid.is_cell_valid(x, y))
    # Filter out cases where the resulting cell is out of bounds or an obstacle
    assume(grid.is_cell_valid(new_x, new_y))

    store = ProbeStore()
    store.set_position(Position(x=x, y=y))

    parser = IntentParser.__new__(IntentParser)
    engine = ProbeEngineManager(
        grid_manager=grid,
        intent_parser=parser,
        probe_store=store,
    )

    valid_result = ParseResult(
        direction=direction,
        is_ambiguous=False,
        is_invalid=False,
        clarification_message=None,
    )

    with patch.object(parser, "parse", return_value=valid_result):
        engine.move("move " + direction)

    position = engine.get_position()
    assert position.x == new_x
    assert position.y == new_y


# ---------------------------------------------------------------------------
# Property 6: Blocked move returns 422 and position unchanged
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 6: Blocked move returns 422
# Validates: Requirements 2.2

# Composite strategy: pick a valid starting cell and a direction that leads to a
# blocked cell (out-of-bounds or obstacle), avoiding excessive assume() filtering.
_GRID = GridManager()
_ALL_VALID_STARTS = [
    (x, y)
    for x in range(20)
    for y in range(20)
    if _GRID.is_cell_valid(x, y)
]
_BLOCKED_TRIPLES = [
    (x, y, d)
    for (x, y) in _ALL_VALID_STARTS
    for d in ["up", "down", "left", "right"]
    if not _GRID.is_cell_valid(
        x + DIRECTION_DELTAS[d][0],
        y + DIRECTION_DELTAS[d][1],
    )
]


@given(triple=st.sampled_from(_BLOCKED_TRIPLES))
@settings(max_examples=100)
def test_property_6_blocked_move_returns_422_position_unchanged(triple: tuple[int, int, str]):
    """Property 6: For any probe position (x, y) and direction d such that the
    resulting cell is out-of-bounds or an obstacle, calling move() raises HTTP 422
    and get_position() remains unchanged."""
    from fastapi import HTTPException

    x, y, direction = triple
    grid = GridManager()
    store = ProbeStore()
    store.set_position(Position(x=x, y=y))

    parser = IntentParser.__new__(IntentParser)
    engine = ProbeEngineManager(
        grid_manager=grid,
        intent_parser=parser,
        probe_store=store,
    )

    blocked_result = ParseResult(
        direction=direction,
        is_ambiguous=False,
        is_invalid=False,
        clarification_message=None,
    )

    with patch.object(parser, "parse", return_value=blocked_result):
        try:
            engine.move("move " + direction)
            assert False, "Expected HTTPException 422 but no exception was raised"
        except HTTPException as exc:
            assert exc.status_code == 422

    # Position must be unchanged
    position = engine.get_position()
    assert position.x == x
    assert position.y == y


# ---------------------------------------------------------------------------
# Property 7: Every movement attempt produces a Movement_Record
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 7: Every movement attempt produces a Movement_Record
# Validates: Requirements 2.3


@given(
    directions=st.lists(
        st.sampled_from(["up", "down", "left", "right"]),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_property_7_every_move_produces_a_record(directions: list[str]):
    """Property 7: For any sequence of n move calls (valid or blocked), the
    movement history contains exactly n records."""
    from fastapi import HTTPException

    grid = GridManager()
    store = ProbeStore()
    parser = IntentParser.__new__(IntentParser)
    engine = ProbeEngineManager(
        grid_manager=grid,
        intent_parser=parser,
        probe_store=store,
    )

    for direction in directions:
        result = ParseResult(
            direction=direction,
            is_ambiguous=False,
            is_invalid=False,
            clarification_message=None,
        )
        with patch.object(parser, "parse", return_value=result):
            try:
                engine.move("move " + direction)
            except HTTPException:
                pass  # blocked moves still produce a record

    records = engine.get_movements()
    assert len(records) == len(directions)


# ---------------------------------------------------------------------------
# Property 8: Movement history is sorted by date ascending
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 8: Movement history is sorted by date ascending
# Validates: Requirements 3.1


@given(
    directions=st.lists(
        st.sampled_from(["up", "down", "left", "right"]),
        min_size=2,
        max_size=20,
    )
)
@settings(max_examples=50)
def test_property_8_movement_history_sorted_ascending(directions: list[str]):
    """Property 8: For any sequence of movement attempts, get_movements() returns
    records in non-decreasing order of the date field."""
    from fastapi import HTTPException

    grid = GridManager()
    store = ProbeStore()
    parser = IntentParser.__new__(IntentParser)
    engine = ProbeEngineManager(
        grid_manager=grid,
        intent_parser=parser,
        probe_store=store,
    )

    for direction in directions:
        result = ParseResult(
            direction=direction,
            is_ambiguous=False,
            is_invalid=False,
            clarification_message=None,
        )
        with patch.object(parser, "parse", return_value=result):
            try:
                engine.move("move " + direction)
            except HTTPException:
                pass  # blocked moves still produce a record

    records = engine.get_movements()
    for i in range(len(records) - 1):
        assert records[i].date <= records[i + 1].date
