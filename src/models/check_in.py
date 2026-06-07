"""Check-in domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.models.enums import CheckInStatus


@dataclass
class CheckIn:
    """Represents a tenant's physical check-in to a rented space.

    Attributes:
        id: Unique identifier for the check-in record.
        tenant_id: ID of the tenant checking in.
        space_id: ID of the space being occupied.
        contract_id: ID of the associated rental contract.
        check_in_date: Timestamp when the tenant checked in.
        check_out_date: Timestamp when the tenant checked out (None if still in).
        status: Current check-in status.
    """

    id: str
    tenant_id: str
    space_id: str
    contract_id: str
    check_in_date: datetime = field(default_factory=datetime.now)
    check_out_date: datetime | None = None
    status: CheckInStatus = CheckInStatus.CHECKED_IN

    def check_out(self) -> None:
        """Record the tenant checking out of the space."""
        self.check_out_date = datetime.now()
        self.status = CheckInStatus.CHECKED_OUT

    def is_active(self) -> bool:
        """Check if the tenant is currently checked in."""
        return self.status == CheckInStatus.CHECKED_IN

    def duration_days(self) -> int | None:
        """Calculate the duration of stay in days.

        Returns:
            Number of days stayed, or None if still checked in.
        """
        if self.check_out_date is None:
            return None
        delta = self.check_out_date - self.check_in_date
        return delta.days
