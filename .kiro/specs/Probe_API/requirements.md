# Requirements Document

## Introduction

A Python microservice that exposes an API which can steer a probe up, down, left and right, inside a 20x20 grid. The probe starts at position (0,0). The grid has hardcoded obstacles at cells (2,3) and (9,11). The API does not allow the probe to move to a cell where an obstacle is present or outside the grid boundaries.

Movement instructions are provided as free-text natural language (e.g. "go north", "move left a step"). A dedicated Intent_Parser component uses a lightweight LLM to interpret the input and resolve it to one of the four canonical directions before passing it to the movement engine.

## Glossary

- **Grid**: A 20x20 square matrix. Each cell in the matrix can either be empty, contain the probe, or contain an obstacle.
- **Probe**: A virtual probe that knows its current position inside the Grid. The probe starts at position (0,0).
- **Obstacle**: A cell in the Grid that the Probe cannot occupy. Obstacles are hardcoded at positions (2,3) and (9,11).
- **Movement_Record**: A record of a single movement attempt, containing: date, from-position, direction, to-position, and status (success or reason for failure).
- **Natural_Language_Input**: A free-text string provided by the user expressing a movement intent (e.g. "go north", "take one step down").
- **Intent_Parser**: The component responsible for interpreting a Natural_Language_Input using a lightweight LLM (e.g. GPT-4o-mini or equivalent) and resolving it to one of the four canonical directions: "up", "down", "left", or "right".
- **Grid_Manager**: The component responsible for creating and initialising the Grid, placing Obstacles at their hardcoded positions, and providing the Grid state to other components.
- **Probe_Engine_Manager**: The component responsible for moving the Probe along the Grid, enforcing movement rules by consulting the Grid state provided by the Grid_Manager to ensure the Probe does not move into a cell with an Obstacle or out of bounds.
- **Probe_Store**: The persistence layer responsible for storing and retrieving the Probe's current position and Movement_Records.
- **API**: The HTTP interface exposed by the Probe_Engine_Manager.

---

## Requirements

### Requirement 0: Grid and Probe Initialization

**User Story:** As a developer, I want the grid and probe to be initialized with known defaults, so that the system behaves predictably without external configuration.

#### Acceptance Criteria

1. THE Grid_Manager SHALL initialize the Grid with a fixed size of 20 columns and 20 rows.
2. THE Grid_Manager SHALL place Obstacles at cells (2,3) and (9,11) at startup.
3. THE Grid_Manager SHALL set the Probe's starting position to (0,0) at startup.

---

### Requirement 1: Parse Natural Language Movement Intent

**User Story:** As a user, I want to express movement instructions in plain language, so that I do not need to know the exact API direction values.

#### Acceptance Criteria

1. WHEN a Natural_Language_Input is received, THE Intent_Parser SHALL invoke a lightweight LLM to interpret the input and resolve it to exactly one of the four directions: "up", "down", "left", or "right".
2. WHEN the Intent_Parser resolves a direction from the Natural_Language_Input, THE Intent_Parser SHALL pass the resolved direction to the Probe_Engine_Manager for processing.
3. IF the Natural_Language_Input is ambiguous and the Intent_Parser cannot confidently determine a direction, THEN THE API SHALL return a 200 OK response containing a clarification message asking the user to rephrase the instruction.
4. IF the Natural_Language_Input is clearly not a movement instruction, THEN THE API SHALL return a 422 Unprocessable Entity response with a descriptive error message.
5. THE Intent_Parser SHALL use a lightweight LLM optimised for speed and low cost (e.g. GPT-4o-mini or equivalent) to minimise latency and operational expense.

---

### Requirement 2: Move the Probe

**User Story:** As a user, I want to move the probe up, down, left or right, 1 step.

#### Acceptance Criteria

1. WHEN a resolved direction is received from the Intent_Parser, THE Probe_Engine_Manager SHALL update the Probe's position to the new location and persist it in the Probe_Store.
2. IF a resolved direction would place the Probe in a cell with an Obstacle or outside the Grid boundaries, THEN THE Probe_Engine_Manager SHALL consult the Grid state provided by the Grid_Manager and return a 422 Unprocessable Entity response with a descriptive error message.
3. THE Probe_Store SHALL persist a Movement_Record containing the date, from-position, direction, to-position, and status (success or reason for failure) for every movement attempt.

---

### Requirement 3: Retrieve Probe's Historical Movements

**User Story:** As a user, I want to retrieve a log of the Probe's movements.

#### Acceptance Criteria

1. WHEN a request to list the Probe's movements is received, THE Probe_Engine_Manager SHALL return a list of all Movement_Records stored in the Probe_Store, sorted by date ascending, where each record includes the date, from-position, direction, to-position, and status.

---

### Requirement 4: Get Current Probe Position

**User Story:** As a user, I want to retrieve the Probe's current position, so that I know where it is at any time.

#### Acceptance Criteria

1. WHEN a request to get the Probe's current position is received, THE Probe_Engine_Manager SHALL return the Probe's current coordinates from the Probe_Store.
