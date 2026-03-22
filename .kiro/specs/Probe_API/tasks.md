# Implementation Plan: Probe_API

## Overview

Incremental implementation of the Probe_API FastAPI microservice. Each task builds on the previous, ending with full integration and test coverage verification.

## Tasks

- [x] 1. Project scaffolding
  - [x] 1.1 Create the directory structure: `probe_api/`, `probe_api/routers/`, `probe_api/components/`, `probe_api/models/`, `probe_api/tests/`
    - Add `__init__.py` to each package directory
    - _Requirements: 0.1, 0.2, 0.3_
  - [x] 1.2 Create `requirements.txt` with all dependencies
    - Include: `fastapi`, `uvicorn`, `openai`, `pydantic`, `pytest`, `pytest-cov`, `hypothesis`, `httpx`
    - _Requirements: 1.5_
  - [x] 1.3 Create `probe_api/main.py` as the FastAPI app entry point
    - Instantiate the `FastAPI` app object
    - Register the probe router (stub import, to be wired in task 8)
    - _Requirements: 0.1_

- [x] 2. Data models
  - [x] 2.1 Implement Pydantic schemas in `probe_api/models/schemas.py`
    - Define `Position(BaseModel)` with `x: int`, `y: int`
    - Define `MovementRecord(BaseModel)` with `date: datetime`, `from_position: Position`, `direction: Literal["up","down","left","right"]`, `to_position: Position`, `status: str`
    - Define `MoveRequest(BaseModel)` with `instruction: str`
    - Define `MoveResponse(BaseModel)` with `position: Position | None`, `message: str`
    - _Requirements: 2.3, 3.1_

- [x] 3. Grid_Manager
  - [x] 3.1 Implement `probe_api/components/grid_manager.py`
    - Define `GridManager` with `GRID_SIZE = 20` and `OBSTACLES = frozenset({(2,3),(9,11)})`
    - Implement `is_within_bounds(x, y) -> bool`
    - Implement `is_obstacle(x, y) -> bool`
    - Implement `is_cell_valid(x, y) -> bool` (within bounds AND not obstacle)
    - _Requirements: 0.1, 0.2_
  - [x] 3.2 Write unit tests in `probe_api/tests/test_grid_manager.py`
    - Test obstacle cells `(2,3)` and `(9,11)` are blocked
    - Test all four boundary edges (x=0, x=19, y=0, y=19 are valid; x=-1, x=20, y=-1, y=20 are invalid)
    - Test `is_cell_valid` returns False for obstacles and out-of-bounds, True for empty in-bounds cells
    - _Requirements: 0.1, 0.2_
  - [x] 3.3 Write property test for Grid_Manager bounds (Property 1)
    - `# Feature: Probe_API, Property 1: Grid bounds are exactly 20×20`
    - Use `@given(st.integers(), st.integers())` to generate arbitrary `(x, y)`
    - Assert `is_within_bounds(x, y)` iff `0 <= x < 20 and 0 <= y < 20`
    - Use `@settings(max_examples=100)`
    - **Property 1: Grid bounds are exactly 20×20**
    - **Validates: Requirements 0.1**

- [x] 4. Probe_Store
  - [x] 4.1 Implement `probe_api/components/probe_store.py`
    - Define `ProbeStore` with in-memory `_position: Position` initialised to `(0, 0)` and `_movements: list[MovementRecord]`
    - Implement `get_position() -> Position`
    - Implement `set_position(position: Position) -> None`
    - Implement `append_movement(record: MovementRecord) -> None`
    - Implement `get_movements() -> list[MovementRecord]`
    - Implement `reset() -> None` (restores initial state; used in tests)
    - _Requirements: 0.3, 2.3, 3.1_
  - [x] 4.2 Write unit tests in `probe_api/tests/test_probe_store.py`
    - Test initial position is `(0, 0)`
    - Test `set_position` / `get_position` round-trip
    - Test `append_movement` / `get_movements` accumulates records in order
    - Test `reset` restores position to `(0, 0)` and clears movement list
    - _Requirements: 0.3, 2.3_

- [x] 5. Intent_Parser
  - [x] 5.1 Implement `probe_api/components/intent_parser.py`
    - Define `ParseResult` dataclass with `direction: Literal["up","down","left","right"] | None`, `is_ambiguous: bool`, `is_invalid: bool`, `clarification_message: str | None`
    - Define `IntentParser` with an injectable OpenAI client (default: real client; tests pass a mock)
    - Implement `parse(instruction: str) -> ParseResult`
    - Build the structured system prompt as specified in the design
    - Call the LLM, parse the JSON response with `json.loads`
    - On JSON parse error or unexpected schema → return ambiguous result
    - On network/API error → raise a service-unavailable exception
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 5.2 Write unit tests in `probe_api/tests/test_intent_parser.py`
    - Mock the OpenAI client for all tests
    - Test each of the four valid directions is returned correctly
    - Test ambiguous LLM response (`direction: null, ambiguous: true`) → `is_ambiguous=True`
    - Test invalid LLM response (`direction: null, ambiguous: false`) → `is_invalid=True`
    - Test JSON parse error → treated as ambiguous
    - Test unexpected schema → treated as ambiguous
    - _Requirements: 1.1, 1.3, 1.4_
  - [x] 5.3 Write property test for Intent_Parser valid directions (Property 2)
    - `# Feature: Probe_API, Property 2: Intent_Parser output is always one of the four canonical directions`
    - Use `@given(st.sampled_from(["up","down","left","right"]))` to generate direction strings
    - Mock LLM to return `{"direction": <sampled>, "ambiguous": false}`
    - Assert `parse()` returns `ParseResult` with that direction and both flags `False`
    - **Property 2: Intent_Parser output is always one of the four canonical directions (or a signal)**
    - **Validates: Requirements 1.1**
  - [x] 5.4 Write property test for ambiguous input → 200 with message (Property 3)
    - `# Feature: Probe_API, Property 3: Ambiguous input returns 200 with clarification`
    - Use `@given(st.text(min_size=1))` for instruction strings
    - Mock `IntentParser.parse` to return `ParseResult(is_ambiguous=True, ...)`
    - Assert `POST /move` returns HTTP 200 and response body has non-empty `message`
    - **Property 3: Ambiguous input returns 200 with clarification**
    - **Validates: Requirements 1.3**
  - [x] 5.5 Write property test for invalid input → 422 (Property 4)
    - `# Feature: Probe_API, Property 4: Invalid (non-movement) input returns 422`
    - Use `@given(st.text(min_size=1))` for instruction strings
    - Mock `IntentParser.parse` to return `ParseResult(is_invalid=True, ...)`
    - Assert `POST /move` returns HTTP 422
    - **Property 4: Invalid (non-movement) input returns 422**
    - **Validates: Requirements 1.4**

- [x] 6. Checkpoint — core components ready
  - Ensure all tests written so far pass: `pytest probe_api/tests/test_grid_manager.py probe_api/tests/test_probe_store.py probe_api/tests/test_intent_parser.py`
  - Ask the user if any questions arise before proceeding.

- [x] 7. Probe_Engine_Manager
  - [x] 7.1 Implement `probe_api/components/probe_engine_manager.py`
    - Define `ProbeEngineManager.__init__(self, grid_manager, intent_parser, probe_store)`
    - Implement `move(instruction: str) -> MoveResponse`
      - Call `intent_parser.parse(instruction)`
      - If `is_invalid` → raise HTTP 422 "Input is not a movement instruction."
      - If `is_ambiguous` → return `MoveResponse(message=clarification_message)`
      - Compute candidate position using direction delta map
      - Call `grid_manager.is_cell_valid(candidate)` → if blocked → append failed `MovementRecord`, raise HTTP 422 with descriptive message
      - Update position in `probe_store`, append successful `MovementRecord`
      - Return `MoveResponse(position=new_position, message="Moved {direction}")`
    - Implement `get_position() -> Position` (delegates to `probe_store`)
    - Implement `get_movements() -> list[MovementRecord]` (delegates to `probe_store`, sorted by date ascending)
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 3.1, 4.1_
  - [x] 7.2 Write unit tests in `probe_api/tests/test_probe_engine_manager.py`
    - Mock `IntentParser` and `GridManager` for all tests
    - Test valid move updates position and appends a success `MovementRecord`
    - Test blocked move (obstacle) raises 422 and position is unchanged, appends a failed `MovementRecord`
    - Test blocked move (out of bounds) raises 422 and position is unchanged
    - Test ambiguous instruction returns 200 `MoveResponse` with clarification message
    - Test invalid instruction raises 422
    - Test `get_movements` returns records sorted by date ascending
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 3.1, 4.1_
  - [x] 7.3 Write property test for valid move round-trip (Property 5)
    - `# Feature: Probe_API, Property 5: Valid move round-trip — position is updated correctly`
    - Use `@given(...)` to generate valid `(x, y, direction)` triples where the resulting cell is in-bounds and not an obstacle
    - Set probe position, call `move()`, assert `get_position()` equals `(x+Δx, y+Δy)`
    - **Property 5: Valid move round-trip — position is updated correctly**
    - **Validates: Requirements 2.1, 4.1**
  - [x] 7.4 Write property test for blocked move → 422 and position unchanged (Property 6)
    - `# Feature: Probe_API, Property 6: Blocked move returns 422`
    - Use `@given(...)` to generate `(x, y, direction)` triples where the resulting cell is out-of-bounds or an obstacle
    - Assert `POST /move` returns HTTP 422 and `get_position()` is unchanged
    - **Property 6: Blocked move returns 422**
    - **Validates: Requirements 2.2**
  - [x] 7.5 Write property test for movement record count (Property 7)
    - `# Feature: Probe_API, Property 7: Every movement attempt produces a Movement_Record`
    - Use `@given(st.lists(st.text(min_size=1), min_size=1, max_size=20))` for sequences of instructions
    - Mock parser to return valid directions; call `move()` for each; assert `len(get_movements()) == n`
    - **Property 7: Every movement attempt produces a Movement_Record**
    - **Validates: Requirements 2.3**
  - [x] 7.6 Write property test for movement history sort order (Property 8)
    - `# Feature: Probe_API, Property 8: Movement history is sorted by date ascending`
    - Use `@given(st.lists(st.text(min_size=1), min_size=2, max_size=20))` for sequences of instructions
    - After all moves, assert each consecutive pair of records satisfies `records[i].date <= records[i+1].date`
    - **Property 8: Movement history is sorted by date ascending**
    - **Validates: Requirements 3.1**

- [x] 8. FastAPI router and endpoints
  - [x] 8.1 Implement `probe_api/routers/probe.py`
    - Create an `APIRouter` with prefix `/`
    - Implement `POST /move` handler: call `engine.move(request.instruction)`, return `MoveResponse`; propagate `HTTPException` for 422 cases
    - Implement `GET /position` handler: call `engine.get_position()`, return `Position`
    - Implement `GET /movements` handler: call `engine.get_movements()`, return `list[MovementRecord]`
    - Handle the service-unavailable exception from `IntentParser` and return HTTP 503
    - _Requirements: 1.3, 1.4, 2.1, 2.2, 3.1, 4.1_
  - [x] 8.2 Write API tests in `probe_api/tests/test_api.py` using `httpx.AsyncClient` / `TestClient`
    - Mock `ProbeEngineManager` for all tests
    - Test `POST /move` with valid instruction → 200 with position and message
    - Test `POST /move` with ambiguous instruction → 200 with clarification message
    - Test `POST /move` with invalid instruction → 422
    - Test `POST /move` with blocked move → 422 with descriptive detail
    - Test `POST /move` with LLM unavailable → 503
    - Test `GET /position` → 200 with `{"x": ..., "y": ...}`
    - Test `GET /movements` → 200 with list of movement records
    - Test `POST /move` missing `instruction` field → 422 (FastAPI validation)
    - _Requirements: 1.3, 1.4, 2.1, 2.2, 3.1, 4.1_

- [x] 9. Integration wiring and dependency injection
  - [x] 9.1 Wire all components together in `probe_api/main.py`
    - Instantiate `GridManager`, `ProbeStore`, `IntentParser` (with real OpenAI client), and `ProbeEngineManager`
    - Use FastAPI dependency injection (`Depends`) or app-level state to provide `ProbeEngineManager` to the router
    - Register the probe router on the app
    - _Requirements: 0.1, 0.2, 0.3_

- [x] 10. Final checkpoint — full test coverage
  - Run `pytest --cov=probe_api --cov-report=term-missing` and verify line coverage reaches 100%
  - Fix any uncovered lines identified by the coverage report
  - Ensure all property tests pass with `@settings(max_examples=100)`
  - Ask the user if any questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use Hypothesis; each is tagged with the design property number it validates
- The OpenAI client is always injected, never imported directly in tests — use mocks
- `ProbeStore.reset()` is used in test fixtures to restore clean state between tests
- Direction delta map: `up=(0,+1)`, `down=(0,-1)`, `left=(-1,0)`, `right=(+1,0)`
- Grid coordinate `(0,0)` is bottom-left; `x` increases rightward, `y` increases upward
