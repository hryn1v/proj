# Architecture Guide

## Overview

The Rental Management System uses a **3-layer in-memory architecture** with no external dependencies.

## Layer Diagram

```
┌─────────────────────────────────────────────────┐
│                   Services                       │
│  Business logic, orchestration, validation       │
│  Depends on: Repository interfaces (ABCs)        │
├─────────────────────────────────────────────────┤
│                  Repositories                    │
│  Data access abstraction via interfaces          │
│  Implementation: dict[str, Entity] collections   │
├─────────────────────────────────────────────────┤
│                    Models                        │
│  Domain entities (dataclasses), enums            │
│  No dependencies on other layers                 │
├─────────────────────────────────────────────────┤
│                    Utils                         │
│  ID generation, validators, date helpers         │
│  Custom exception hierarchy                      │
└─────────────────────────────────────────────────┘
```

## Dependency Rules

1. **Models** have NO dependencies on Services or Repositories
2. **Repositories** depend only on Models and Utils
3. **Services** depend on Repository interfaces (ABCs) and Models
4. **Services** never depend on concrete repository implementations
5. Dependencies are injected via constructor (Dependency Inversion)

## In-Memory Storage

All data is stored in `dict[str, T]` collections within repository classes:

```python
class InMemoryBaseRepository(IRepository[T]):
    def __init__(self):
        self._store: dict[str, T] = {}
```

- Each entity type has its own repository instance
- Data is lost when the application stops (by design)
- No persistence layer — this is intentional for the project scope

## Domain Entities

| Entity | File | Key Relationships |
|--------|------|-------------------|
| Tenant | `src/models/tenant.py` | Has many Contracts, Bookings, CheckIns |
| Space | `src/models/space.py` | Has many Contracts, Bookings, CheckIns |
| Contract | `src/models/contract.py` | Belongs to Tenant + Space, has many Invoices |
| Booking | `src/models/booking.py` | Belongs to Tenant + Space |
| CheckIn | `src/models/check_in.py` | Belongs to Tenant + Space + Contract |
| Invoice | `src/models/invoice.py` | Belongs to Contract + Tenant, has Payment |
| Payment | `src/models/payment.py` | Belongs to Invoice |

## GoF Patterns

### Strategy Pattern (`src/services/penalty_strategy.py`)
- **Purpose**: Interchangeable penalty calculation algorithms
- **Classes**: `FlatRatePenalty`, `PercentagePenalty`, `ProgressivePenalty`
- **Usage**: Injected into `InvoiceService` via `penalty_strategy` property

### Observer Pattern (`src/services/notification_service.py`)
- **Purpose**: Event-driven notifications when spaces become available
- **Publisher**: `SpaceEventPublisher` — manages subscriptions and dispatches events
- **Subscribers**: `BookingQueueNotifier` (auto-confirms bookings), `TenantNotifier` (logs notifications)
- **Usage**: `SpaceService` publishes `space_available` events on `release_space()`

### Factory Method Pattern (`src/services/invoice_factory.py`)
- **Purpose**: Encapsulated invoice creation for different invoice types
- **Factories**: `RegularInvoiceFactory`, `PenaltyInvoiceFactory`, `DepositInvoiceFactory`, `FinalSettlementFactory`
- **Usage**: `InvoiceService` uses factories internally to create invoices

## File Naming Conventions

- Models: `src/models/<entity>.py` (singular, snake_case)
- Repositories: `src/storage/<entity>_repository.py`
- Services: `src/services/<entity>_service.py`
- Tests: `tests/unit/<layer>/test_<module>.py`
