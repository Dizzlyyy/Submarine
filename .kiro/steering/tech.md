# Tech Stack

- Language: Python 3.11+
- Web Framework: FastAPI
- Package Manager: pip / venv or Poetry
- Testing: pytest with full test coverage required (aim for 100% coverage)
- Coverage Tool: pytest-cov

## Testing Requirements

- All code must have corresponding tests
- Use `pytest` for unit and integration tests
- Coverage must be measured with `pytest-cov`
- No feature is considered complete without passing tests

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Start dev server (update once framework is chosen)
python app.py
```
