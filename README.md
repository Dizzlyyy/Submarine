# Probe API

A FastAPI microservice that steers a virtual probe around a 20×20 grid using natural language instructions. Movement intent is resolved by a lightweight LLM (Amazon Nova Micro via Bedrock), so you can say things like "go north" or "take a step to the left" instead of passing raw direction values.

## How it works

- The grid is 20×20. The probe starts at `(0,0)` (bottom-left).
- Obstacles are fixed at `(2,3)` and `(9,11)`.
- Movement instructions are free-text. The LLM resolves them to `up`, `down`, `left`, or `right`.
- Ambiguous instructions get a clarification response. Non-movement instructions get a 422.
- Every move attempt (success or failure) is recorded in the movement history.

## Requirements

- Python 3.11+
- AWS credentials configured (for Bedrock) — via env vars, `~/.aws/credentials`, or an IAM role
- Amazon Nova Micro enabled in your AWS account/region (`us-east-1` by default)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the server

```bash
uvicorn probe_api.main:app --reload
```

Override the Bedrock model or region if needed:

```bash
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0 AWS_REGION=us-east-1 uvicorn probe_api.main:app --reload
```

## API

### POST /move

Send a natural language movement instruction.

```bash
curl -X POST http://localhost:8000/move \
  -H "Content-Type: application/json" \
  -d '{"instruction": "go north"}'
```

Responses:

| Status | Condition |
|--------|-----------|
| 200 | Successful move — returns new position and message |
| 200 | Ambiguous instruction — returns clarification message |
| 422 | Not a movement instruction, or move is blocked |
| 503 | LLM unavailable |

### GET /position

Get the probe's current position.

```bash
curl http://localhost:8000/position
```

### GET /movements

Get the full movement history, sorted by date ascending.

```bash
curl http://localhost:8000/movements
```

## Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=probe_api --cov-report=term-missing
```

## Project structure

```
probe_api/
├── main.py                        # App entry point, component wiring
├── routers/probe.py               # FastAPI route handlers
├── components/
│   ├── bedrock_client.py          # Bedrock adapter (Nova Micro)
│   ├── grid_manager.py            # Grid rules and obstacle checks
│   ├── intent_parser.py           # LLM-based direction resolver
│   ├── probe_engine_manager.py    # Movement orchestration
│   └── probe_store.py             # In-memory position and history store
├── models/schemas.py              # Pydantic models
└── tests/                         # Unit and property-based tests
requirements.txt
```
