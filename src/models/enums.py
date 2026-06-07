"""Domain enumerations for the Rental Management System."""
from __future__ import annotations

from enum import Enum


class TenantStatus(Enum):
    """Status of a tenant in the system."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    INACTIVE = "inactive"


class SpaceType(Enum):
    """Type of rentable space."""

    OFFICE = "office"
    APARTMENT = "apartment"
    PARKING = "parking"
    WAREHOUSE = "warehouse"


class SpaceStatus(Enum):
    """Current availability status of a space."""

    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class ContractStatus(Enum):
    """Lifecycle status of a rental contract."""

    DRAFT = "draft"
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BookingStatus(Enum):
    """Status of a space booking/reservation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CheckInStatus(Enum):
    """Status of a tenant check-in record."""

    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"


class InvoiceStatus(Enum):
    """Payment status of an invoice."""

    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceType(Enum):
    """Type/purpose of an invoice."""

    REGULAR = "regular"
    PENALTY = "penalty"
    DEPOSIT = "deposit"
    FINAL_SETTLEMENT = "final_settlement"


class PaymentMethod(Enum):
    """Method used for payment."""

    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
