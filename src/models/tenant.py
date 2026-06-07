"""Tenant domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.models.enums import TenantStatus


@dataclass
class Tenant:
    """Represents a tenant who rents spaces in the system.

    Attributes:
        id: Unique identifier for the tenant.
        name: Full name of the tenant.
        email: Contact email address.
        phone: Contact phone number.
        status: Current tenant status (active, blocked, inactive).
        registered_at: Timestamp when the tenant was registered.
        violation_count: Number of violations accumulated by the tenant.
    """

    id: str
    name: str
    email: str
    phone: str
    status: TenantStatus = TenantStatus.ACTIVE
    registered_at: datetime = field(default_factory=datetime.now)
    violation_count: int = 0

    def is_blocked(self) -> bool:
        """Check if the tenant is currently blocked."""
        return self.status == TenantStatus.BLOCKED

    def is_active(self) -> bool:
        """Check if the tenant is currently active."""
        return self.status == TenantStatus.ACTIVE

    def add_violation(self) -> None:
        """Increment the tenant's violation count by one."""
        self.violation_count += 1

    def block(self) -> None:
        """Block the tenant, preventing new contracts and bookings."""
        self.status = TenantStatus.BLOCKED

    def activate(self) -> None:
        """Reactivate a blocked or inactive tenant."""
        self.status = TenantStatus.ACTIVE
        self.violation_count = 0

    def deactivate(self) -> None:
        """Deactivate the tenant."""
        self.status = TenantStatus.INACTIVE
