"""Unit tests for IntentParser.

All tests mock the OpenAI client — no real API calls are made.
"""
import json
from unittest.mock import MagicMock

import pytest

from probe_api.components.intent_parser import IntentParser


def make_client(content: str) -> MagicMock:
    """Return a mock OpenAI client whose chat.completions.create() returns *content*."""
    mock_message = MagicMock()
    mock_message.content = content

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# Valid directions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("direction", ["up", "down", "left", "right"])
def test_valid_direction_returned(direction):
    payload = json.dumps({"direction": direction, "ambiguous": False})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("move somewhere")
    assert result.direction == direction
    assert result.is_ambiguous is False
    assert result.is_invalid is False
    assert result.clarification_message is None


# ---------------------------------------------------------------------------
# Ambiguous response
# ---------------------------------------------------------------------------

def test_ambiguous_response():
    payload = json.dumps({"direction": None, "ambiguous": True})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("go somewhere vague")
    assert result.direction is None
    assert result.is_ambiguous is True
    assert result.is_invalid is False
    assert result.clarification_message is not None


# ---------------------------------------------------------------------------
# Invalid (non-movement) response
# ---------------------------------------------------------------------------

def test_invalid_response():
    payload = json.dumps({"direction": None, "ambiguous": False})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("what is the weather?")
    assert result.direction is None
    assert result.is_ambiguous is False
    assert result.is_invalid is True


# ---------------------------------------------------------------------------
# JSON parse error → treated as ambiguous
# ---------------------------------------------------------------------------

def test_json_parse_error_treated_as_ambiguous():
    parser = IntentParser(client=make_client("this is not json at all"))
    result = parser.parse("go north")
    assert result.is_ambiguous is True
    assert result.is_invalid is False
    assert result.direction is None


# ---------------------------------------------------------------------------
# Unexpected schema → treated as ambiguous
# ---------------------------------------------------------------------------

def test_unexpected_schema_missing_ambiguous_field():
    # Valid JSON but missing the 'ambiguous' key
    payload = json.dumps({"direction": "up"})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("go north")
    assert result.is_ambiguous is True
    assert result.is_invalid is False


def test_unexpected_schema_unknown_direction():
    # Valid JSON but direction is not one of the four canonical values
    payload = json.dumps({"direction": "diagonal", "ambiguous": False})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("go diagonally")
    assert result.is_ambiguous is True
    assert result.is_invalid is False


# ---------------------------------------------------------------------------
# Default client construction (no client argument)
# ---------------------------------------------------------------------------

def test_default_client_construction_uses_openai(monkeypatch):
    """Covers the `if client is None` branch in IntentParser.__init__."""
    import types

    fake_openai_client = MagicMock()
    fake_openai_module = types.SimpleNamespace(OpenAI=lambda: fake_openai_client)
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai_module)

    parser = IntentParser()  # no client passed → triggers the branch
    assert parser._client is fake_openai_client


# ---------------------------------------------------------------------------
# Network / API error → 503 HTTPException
# ---------------------------------------------------------------------------

def test_network_error_raises_503():
    from fastapi import HTTPException

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("connection refused")

    parser = IntentParser(client=mock_client)
    with pytest.raises(HTTPException) as exc_info:
        parser.parse("go north")

    assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# Property 2: Intent_Parser output is always one of the four canonical directions
# ---------------------------------------------------------------------------
# Feature: Probe_API, Property 2: Intent_Parser output is always one of the four canonical directions
# Validates: Requirements 1.1

from hypothesis import given, settings
import hypothesis.strategies as st


@given(st.sampled_from(["up", "down", "left", "right"]))
@settings(max_examples=100)
def test_property_2_valid_direction_always_canonical(direction):
    """Property 2: For any valid direction string returned by the LLM,
    parse() returns a ParseResult with that exact direction and both flags False."""
    payload = json.dumps({"direction": direction, "ambiguous": False})
    parser = IntentParser(client=make_client(payload))
    result = parser.parse("move somewhere")
    assert result.direction == direction
    assert result.is_ambiguous is False
    assert result.is_invalid is False
