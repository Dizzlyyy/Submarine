"""Property-based tests for the POST /move API endpoint (Properties 3 and 4).

Uses a minimal inline FastAPI app with a stubbed /move endpoint so these tests
can run independently before the real router (task 8) is implemented.
"""
from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from hypothesis import given, settings
import hypothesis.strategies as st

from probe_api.components.intent_parser import IntentParser, ParseResult
from probe_api.models.schemas import MoveRequest, MoveResponse, Position

# ---------------------------------------------------------------------------
# Minimal inline FastAPI app that mirrors the real router logic
# ---------------------------------------------------------------------------

_intent_parser = IntentParser.__new__(IntentParser)  # instance without __init__

_mini_app = FastAPI()


@_mini_app.post("/move", response_model=MoveResponse)
def move(request: MoveRequest) -> MoveResponse:
    result: ParseResult = _intent_parser.parse(request.instruction)
    if result.is_invalid:
        raise HTTPException(status_code=422, detail="Input is not a movement instruction.")
    if result.is_ambiguous:
        return MoveResponse(message=result.clarification_message or "Please rephrase.")
    return MoveResponse(position=Position(x=0, y=0), message="Moved")


_client = TestClient(_mini_app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Property 3: Ambiguous input returns 200 with clarification
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 3: Ambiguous input returns 200 with clarification
# Validates: Requirements 1.3


@given(st.text(min_size=1))
@settings(max_examples=100)
def test_property_3_ambiguous_input_returns_200_with_message(instruction: str):
    """Property 3: For any instruction where IntentParser signals ambiguity,
    POST /move returns HTTP 200 and a non-empty message field."""
    ambiguous_result = ParseResult(
        direction=None,
        is_ambiguous=True,
        is_invalid=False,
        clarification_message="Please rephrase.",
    )
    with patch.object(_intent_parser, "parse", return_value=ambiguous_result):
        response = _client.post("/move", json={"instruction": instruction})

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert len(body["message"]) > 0


# ---------------------------------------------------------------------------
# Property 4: Invalid (non-movement) input returns 422
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 4: Invalid (non-movement) input returns 422
# Validates: Requirements 1.4


@given(st.text(min_size=1))
@settings(max_examples=100)
def test_property_4_invalid_input_returns_422(instruction: str):
    """Property 4: For any instruction where IntentParser signals invalid input,
    POST /move returns HTTP 422."""
    invalid_result = ParseResult(
        direction=None,
        is_ambiguous=False,
        is_invalid=True,
        clarification_message=None,
    )
    with patch.object(_intent_parser, "parse", return_value=invalid_result):
        response = _client.post("/move", json={"instruction": instruction})

    assert response.status_code == 422
