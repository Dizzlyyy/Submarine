from datetime import datetime, timezone

import pytest

from probe_api.components.probe_store import ProbeStore
from probe_api.models.schemas import MovementRecord, Position


@pytest.fixture
def store():
    s = ProbeStore()
    yield s
    s.reset()


def test_initial_position(store):
    pos = store.get_position()
    assert pos.x == 0
    assert pos.y == 0


def test_set_get_position_round_trip(store):
    new_pos = Position(x=5, y=10)
    store.set_position(new_pos)
    assert store.get_position() == new_pos


def test_append_movement_accumulates_in_order(store):
    def make_record(fx, fy, tx, ty):
        return MovementRecord(
            date=datetime.now(tz=timezone.utc),
            from_position=Position(x=fx, y=fy),
            direction="up",
            to_position=Position(x=tx, y=ty),
            status="success",
        )

    r1 = make_record(0, 0, 0, 1)
    r2 = make_record(0, 1, 0, 2)
    r3 = make_record(0, 2, 0, 3)

    store.append_movement(r1)
    store.append_movement(r2)
    store.append_movement(r3)

    movements = store.get_movements()
    assert len(movements) == 3
    assert movements[0] == r1
    assert movements[1] == r2
    assert movements[2] == r3


def test_reset_restores_initial_state(store):
    store.set_position(Position(x=7, y=3))
    store.append_movement(
        MovementRecord(
            date=datetime.now(tz=timezone.utc),
            from_position=Position(x=0, y=0),
            direction="right",
            to_position=Position(x=7, y=3),
            status="success",
        )
    )

    store.reset()

    pos = store.get_position()
    assert pos.x == 0
    assert pos.y == 0
    assert store.get_movements() == []
