from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException

SYSTEM_PROMPT = """You are a movement intent classifier. Given a user instruction, respond with a JSON object:
  { "direction": "up" | "down" | "left" | "right" | null, "ambiguous": true | false }

Rules:
- If the instruction clearly maps to one direction, set direction to that value and ambiguous to false.
- If the instruction is a movement instruction but the direction is unclear, set direction to null and ambiguous to true.
- If the instruction is not a movement instruction at all, set direction to null and ambiguous to false.
- Synonyms: north/up, south/down, west/left, east/right, forward/up, back/down.
- Respond ONLY with the JSON object, no other text."""

VALID_DIRECTIONS = {"up", "down", "left", "right"}


@dataclass
class ParseResult:
    direction: Literal["up", "down", "left", "right"] | None
    is_ambiguous: bool
    is_invalid: bool
    clarification_message: str | None


class IntentParser:
    def __init__(self, client=None):
        if client is None:
            import openai
            client = openai.OpenAI()
        self._client = client

    def parse(self, instruction: str) -> ParseResult:
        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                ],
            )
            raw = response.choices[0].message.content
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Intent parsing service unavailable. Please try again.",
            )

        try:
            data = json.loads(raw)
            direction = data.get("direction")
            ambiguous = data.get("ambiguous")

            if not isinstance(ambiguous, bool):
                raise ValueError("unexpected schema")

            if direction is not None and direction not in VALID_DIRECTIONS:
                raise ValueError("unexpected direction value")

        except (json.JSONDecodeError, ValueError, AttributeError):
            # Treat parse errors / unexpected schema as ambiguous
            return ParseResult(
                direction=None,
                is_ambiguous=True,
                is_invalid=False,
                clarification_message="I couldn't determine a direction. Could you rephrase?",
            )

        if direction in VALID_DIRECTIONS and not ambiguous:
            return ParseResult(
                direction=direction,
                is_ambiguous=False,
                is_invalid=False,
                clarification_message=None,
            )

        if direction is None and ambiguous:
            return ParseResult(
                direction=None,
                is_ambiguous=True,
                is_invalid=False,
                clarification_message="I couldn't determine a direction. Could you rephrase?",
            )

        # direction is None and ambiguous is False → not a movement instruction
        return ParseResult(
            direction=None,
            is_ambiguous=False,
            is_invalid=True,
            clarification_message=None,
        )
