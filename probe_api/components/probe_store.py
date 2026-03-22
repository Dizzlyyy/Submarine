from probe_api.models.schemas import MovementRecord, Position


class ProbeStore:
    def __init__(self) -> None:
        self._position: Position = Position(x=0, y=0)
        self._movements: list[MovementRecord] = []

    def get_position(self) -> Position:
        return self._position

    def set_position(self, position: Position) -> None:
        self._position = position

    def append_movement(self, record: MovementRecord) -> None:
        self._movements.append(record)

    def get_movements(self) -> list[MovementRecord]:
        return list(self._movements)

    def reset(self) -> None:
        self._position = Position(x=0, y=0)
        self._movements = []
