# Testing Strategy Guide

## Framework & Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `pytest` | Test runner | `pip install pytest` |
| `pytest-cov` | Coverage measurement | `pip install pytest-cov` |
| `coverage` | Coverage reports | `pip install coverage[toml]` |
| `ruff` | Linting | `pip install ruff` |

## Running Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing -v

# Generate XML reports for SonarQube
pytest --junitxml=reports/junit.xml \
       --cov=src \
       --cov-report=xml:reports/coverage.xml \
       --cov-report=html:reports/htmlcov \
       -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest tests/edge_cases/ -v              # Edge case tests only

# Run tests for a specific module
pytest tests/unit/services/test_tenant_service.py -v
```

## Test Organization

```
tests/
├── conftest.py                          # Shared fixtures
├── unit/
│   ├── models/                          # Model creation, validation, methods
│   ├── storage/                         # Repository CRUD and queries
│   ├── services/                        # Business logic with mocked deps
│   ├── patterns/                        # Strategy, Factory, Observer tests
│   └── utils/                           # Validators, helpers, exceptions
├── integration/                         # Cross-service workflow tests
└── edge_cases/                          # Boundary conditions, extreme values
```

## Coverage Target

- **Minimum**: 70% overall coverage (enforced in `pyproject.toml`)
- **Goal**: 85%+ coverage
- Coverage exclusions: `tests/*`, `*/__init__.py`

## Writing New Tests

### 1. Use Factory Functions (from `conftest.py`)

```python
from tests.conftest import make_tenant, make_space, make_contract

def test_example():
    tenant = make_tenant(name="Alice", email="alice@test.com")
    space = make_space(type=SpaceType.OFFICE, price_per_month=1500.0)
```

### 2. Use Fixtures for Services

```python
def test_register(self, tenant_service):
    t = tenant_service.register_tenant("Bob", "bob@test.com", "+380501234567")
    assert t.is_active()
```

### 3. Test Both Happy Path and Error Cases

```python
def test_success(self, tenant_service):
    t = tenant_service.register_tenant("Alice", "a@t.com", "+380501111111")
    assert t.name == "Alice"

def test_invalid_email_raises(self, tenant_service):
    with pytest.raises(ValidationError):
        tenant_service.register_tenant("Alice", "bad-email", "+380501111111")
```

### 4. Edge Cases Checklist

For each entity, test:
- [ ] Creation with valid data
- [ ] Creation with invalid data (each field)
- [ ] State transitions (valid and invalid)
- [ ] Boundary values (0, negative, very large)
- [ ] Duplicate detection
- [ ] Not-found scenarios
- [ ] Cross-entity validation (e.g., blocked tenant can't book)

## Report Formats

| Report | Location | Purpose |
|--------|----------|---------|
| `reports/junit.xml` | JUnit XML | SonarQube test results |
| `reports/coverage.xml` | Cobertura XML | SonarQube coverage data |
| `reports/htmlcov/` | HTML pages | Visual line-by-line coverage |

## CI/CD Integration

Reports are automatically generated and uploaded as artifacts in the GitHub Actions pipeline.
SonarCloud reads `junit.xml` and `coverage.xml` for Quality Gate evaluation.
