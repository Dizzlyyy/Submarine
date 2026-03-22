from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from probe_api.components.grid_manager import GridManager
from probe_api.components.intent_parser import IntentParser
from probe_api.components.probe_store import ProbeStore
from probe_api.models.schemas import MovementRecord, MoveResponse, Position

DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


class ProbeEngineManager:
    def __init__(
        self,
        grid_manager: GridManager,
        intent_parser: IntentParser,
        probe_store: ProbeStore,
    ) -> None:
        self._grid_manager = grid_manager
        self._intent_parser = intent_parser
        self._probe_store = probe_store

    def move(self, instruction: str) -> MoveResponse:
        result = self._intent_parser.parse(instruction)

        if result.is_invalid:
            raise HTTPException(status_code=422, detail="Input is not a movement instruction.")

        if result.is_ambiguous:
            return MoveResponse(message=result.clarification_message)

        direction = result.direction
        dx, dy = DIRECTION_DELTAS[direction]

        current = self._probe_store.get_position()
        candidate_x = current.x + dx
        candidate_y = current.y + dy
        candidate = Position(x=candidate_x, y=candidate_y)

        if not self._grid_manager.is_within_bounds(candidate_x, candidate_y):
            self._probe_store.append_movement(
                MovementRecord(
                    date=datetime.now(timezone.utc),
                    from_position=current,
                    direction=direction,
                    to_position=candidate,
                    status="out of bounds",
                )
            )
            raise HTTPException(
                status_code=422,
                detail=f"Cannot move {direction}: position ({candidate_x},{candidate_y}) is out of bounds",
            )

        if self._grid_manager.is_obstacle(candidate_x, candidate_y):
            self._probe_store.append_movement(
                MovementRecord(
                    date=datetime.now(timezone.utc),
                    from_position=current,
                    direction=direction,
                    to_position=candidate,
                    status="obstacle",
                )
            )
            raise HTTPException(
                status_code=422,
                detail=f"Cannot move {direction}: obstacle at ({candidate_x},{candidate_y})",
            )

        new_position = Position(x=candidate_x, y=candidate_y)
        self._probe_store.set_position(new_position)
        self._probe_store.append_movement(
            MovementRecord(
                date=datetime.now(timezone.utc),
                from_position=current,
                direction=direction,
                to_position=new_position,
                status="success",
            )
        )

        return MoveResponse(position=new_position, message=f"Moved {direction}")

    def get_position(self) -> Position:
        return self._probe_store.get_position()

    def get_movements(self) -> list[MovementRecord]:
        records = self._probe_store.get_movements()
        return sorted(records, key=lambda r: r.date)
