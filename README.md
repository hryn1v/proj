# 🏢 Rental Management System

[![CI Pipeline](https://github.com/hryn1v/proj/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/hryn1v/proj/actions/workflows/ci-pipeline.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=hryn1v_proj&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=hryn1v_proj)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=hryn1v_proj&metric=coverage)](https://sonarcloud.io/summary/new_code?id=hryn1v_proj)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=hryn1v_proj&metric=bugs)](https://sonarcloud.io/summary/new_code?id=hryn1v_proj)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=hryn1v_proj&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=hryn1v_proj)

> In-memory rental management system handling **check-ins, contracts, space bookings, and invoices** — built with clean architecture, GoF design patterns, SOLID principles, and comprehensive test coverage.

## 📋 Overview

This system manages commercial space rentals (offices, apartments, parking, warehouses) with full lifecycle support:

| Feature | Description |
|---------|-------------|
| 🧑 **Tenant Management** | Registration, validation, violation tracking, auto-blocking |
| 📄 **Contracts** | Draft → Active → Terminated/Expired lifecycle |
| 📅 **Bookings** | Priority queue with waitlist auto-confirmation |
| 🏠 **Check-In/Out** | Occupancy tracking with contract validation |
| 💰 **Invoicing** | Regular, penalty, deposit, settlement invoices |
| 💳 **Payments** | Multi-method payment processing |
| ⚠️ **Penalties** | Strategy-based overdue penalty calculation |
| 🔔 **Notifications** | Observer-based space availability alerts |

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│              Services                    │  ← Business logic
├─────────────────────────────────────────┤
│            Repositories                  │  ← Data access (interfaces)
├─────────────────────────────────────────┤
│              Models                      │  ← Domain entities
├─────────────────────────────────────────┤
│              Utils                       │  ← Helpers, validators
└─────────────────────────────────────────┘
```

### GoF Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Strategy** | `src/services/penalty_strategy.py` | Interchangeable penalty algorithms (Flat, Percentage, Progressive) |
| **Observer** | `src/services/notification_service.py` | Event-driven space availability notifications |
| **Factory Method** | `src/services/invoice_factory.py` | Specialized invoice creation (Regular, Penalty, Deposit, Settlement) |

### SOLID Principles

- **S**ingle Responsibility: Each service/repo handles one domain area
- **O**pen/Closed: Patterns enable extension without modification
- **L**iskov Substitution: Repository implementations are interchangeable
- **I**nterface Segregation: Separate `IReadRepository` / `IWriteRepository`
- **D**ependency Inversion: Services depend on ABC interfaces, not implementations

## 📂 Project Structure

```
rental-management-system/
├── src/
│   ├── models/              # Domain entities (dataclasses)
│   │   ├── enums.py         # 9 enum definitions
│   │   ├── tenant.py        # Tenant with violation tracking
│   │   ├── space.py         # Rentable space with status
│   │   ├── contract.py      # Rental contract lifecycle
│   │   ├── booking.py       # Priority queue bookings
│   │   ├── check_in.py      # Occupancy records
│   │   ├── invoice.py       # Invoices with penalties
│   │   ├── payment.py       # Payment records
│   │   └── notification.py  # Observer notifications
│   ├── storage/             # Repository layer
│   │   ├── interfaces.py    # Generic IRepository ABC
│   │   ├── base_repository.py # InMemoryBaseRepository
│   │   └── *_repository.py  # Entity-specific repos
│   ├── services/            # Business logic layer
│   │   ├── tenant_service.py
│   │   ├── space_service.py
│   │   ├── contract_service.py
│   │   ├── booking_service.py
│   │   ├── check_in_service.py
│   │   ├── invoice_service.py
│   │   ├── payment_service.py
│   │   ├── penalty_strategy.py    # Strategy Pattern
│   │   ├── invoice_factory.py     # Factory Method
│   │   └── notification_service.py # Observer Pattern
│   ├── cli/                 # Interactive REPL
│   │   ├── repl.py          # RentalCLI command dispatcher
│   │   └── __main__.py      # `python -m src.cli` entry point
│   └── utils/               # Helpers
│       ├── exceptions.py    # Custom exception hierarchy
│       ├── validators.py    # Input validation
│       ├── date_helpers.py  # Date arithmetic
│       └── id_generator.py  # UUID-based IDs
├── tests/                   # 380+ tests
│   ├── conftest.py          # Shared fixtures
│   ├── unit/                # Unit tests by layer (incl. cli/)
│   ├── integration/         # Cross-service workflows
│   └── edge_cases/          # Boundary conditions
├── docs/diagrams/           # UML diagrams (Mermaid)
├── .cursor/rules/           # AI context files
├── .github/workflows/       # CI/CD pipeline
├── rms.py                   # CLI launcher (python rms.py / -m rms)
├── demo.py                  # Scripted lifecycle demo
├── .cursorrules             # Global AI rules
├── Dockerfile               # Isolated test runner
├── pyproject.toml           # Project config
├── sonar-project.properties # SonarCloud config
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/hryn1v/proj.git
cd proj

# Install dependencies
pip install -r requirements.txt
```

### Running the CLI

The project ships with an interactive command-line shell (REPL) for managing
the full rental lifecycle in memory:

```bash
python rms.py
# equivalent:  python -m rms     or     python -m src.cli
```

```text
🏢  Rental Management System — interactive CLI.  Type 'help' for commands, 'quit' to exit.
rms> seed
✓ Seeded sample data:
  tenant  TNT-…  (Alice, active)
  space   SPC-…  (Office 301, now occupied)
  contract CTR-… (active)
rms> tenant add "Alice Johnson" alice@mail.com +380501112233
✓ Registered TNT-…  Alice Johnson <alice@mail.com>  active  violations=0
rms> contract create <tenant_id> <space_id> 2026-06-01 2027-06-01 1500 1500
rms> contract activate <contract_id>
rms> invoice gen <contract_id>
rms> invoice pay <invoice_id> 1500 card
rms> stats
rms> quit
```

Type `help` inside the shell for the full command list (tenants, spaces,
contracts, bookings, check-ins, invoices, payments and penalty strategies).
All data is in-memory and is discarded when the shell exits.

### Running a Scripted Demo

```bash
# Guided, step-by-step walkthrough of the whole rental lifecycle
python demo.py
```

### Running Tests

```bash
# Run all tests
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing -v

# Generate full reports (XML + HTML)
pytest --junitxml=reports/junit.xml \
       --cov=src \
       --cov-report=xml:reports/coverage.xml \
       --cov-report=html:reports/htmlcov \
       -v

# Open HTML coverage report
open reports/htmlcov/index.html
```

### Docker

```bash
# Build and run tests in Docker
docker build -t rental-system .
docker run -v $(pwd)/reports:/app/reports rental-system
```

### Linting

```bash
ruff check src/ tests/
```

## 📊 Quality Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Code Coverage | ≥ 70% | ✅ |
| Test Count | 200+ | ✅ |
| Bugs | 0 | ✅ |
| Vulnerabilities | 0 | ✅ |
| Code Smells | A/B | ✅ |

## 🧪 Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Unit: Models** | ~35 | Entity creation, validation, methods |
| **Unit: Storage** | ~50 | Repository CRUD and queries |
| **Unit: Services** | ~65 | Business logic with dependency injection |
| **Unit: Patterns** | ~45 | Strategy, Factory, Observer pattern tests |
| **Unit: Utils** | ~50 | Validators, helpers, exceptions |
| **Integration** | ~25 | Cross-service workflow tests |
| **Edge Cases** | ~25 | Boundary conditions, extreme values |

## 📄 License

This project is developed as an academic assignment.
