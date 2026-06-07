# Domain Model — Rental Management System

```mermaid
erDiagram
    TENANT {
        string id PK
        string name
        string email UK
        string phone
        TenantStatus status
        datetime registered_at
        int violation_count
    }

    SPACE {
        string id PK
        string name
        SpaceType type
        float area_sqm
        int floor
        float price_per_month
        SpaceStatus status
    }

    CONTRACT {
        string id PK
        string tenant_id FK
        string space_id FK
        date start_date
        date end_date
        float monthly_rate
        float deposit
        ContractStatus status
        datetime created_at
    }

    BOOKING {
        string id PK
        string tenant_id FK
        string space_id FK
        datetime created_at
        date desired_start
        date desired_end
        int priority
        BookingStatus status
    }

    CHECK_IN {
        string id PK
        string tenant_id FK
        string space_id FK
        string contract_id FK
        datetime check_in_date
        datetime check_out_date
        CheckInStatus status
    }

    INVOICE {
        string id PK
        string contract_id FK
        string tenant_id FK
        float base_amount
        float penalty_amount
        date issue_date
        date due_date
        InvoiceStatus status
        InvoiceType type
    }

    PAYMENT {
        string id PK
        string invoice_id FK
        float amount
        datetime payment_date
        PaymentMethod method
    }

    NOTIFICATION {
        string id PK
        string tenant_id FK
        string message
        datetime created_at
        bool is_read
    }

    TENANT ||--o{ CONTRACT : "signs"
    TENANT ||--o{ BOOKING : "requests"
    TENANT ||--o{ CHECK_IN : "performs"
    TENANT ||--o{ NOTIFICATION : "receives"
    SPACE ||--o{ CONTRACT : "subject of"
    SPACE ||--o{ BOOKING : "reserved for"
    SPACE ||--o{ CHECK_IN : "occupied by"
    CONTRACT ||--o{ INVOICE : "generates"
    CONTRACT ||--o| CHECK_IN : "has"
    INVOICE ||--o| PAYMENT : "paid by"
```

## Entity Relationships

| Relationship | Cardinality | Description |
|-------------|-------------|-------------|
| Tenant → Contract | 1:N | A tenant can have multiple contracts |
| Tenant → Booking | 1:N | A tenant can have multiple bookings |
| Tenant → CheckIn | 1:N | A tenant can have multiple check-in records |
| Space → Contract | 1:N | A space can have multiple contracts (sequential) |
| Space → Booking | 1:N | A space can have multiple bookings (waitlist) |
| Contract → Invoice | 1:N | A contract generates multiple invoices |
| Contract → CheckIn | 1:0..1 | A contract has at most one active check-in |
| Invoice → Payment | 1:0..1 | An invoice can have one payment |
| Tenant → Notification | 1:N | A tenant receives multiple notifications |
