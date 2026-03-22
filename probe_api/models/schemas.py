from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Position(BaseModel):
    x: int
    y: int


class MovementRecord(BaseModel):
    date: datetime
    from_position: Position
    direction: Literal["up", "down", "left", "right"]
    to_position: Position
    status: str


class MoveRequest(BaseModel):
    instruction: str


class MoveResponse(BaseModel):
    position: Position | None = None
    message: str
