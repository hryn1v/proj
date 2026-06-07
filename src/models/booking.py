"""Booking domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from src.models.enums import BookingStatus


@dataclass
class Booking:
    """Represents a space reservation request by a tenant.

    Bookings support a priority queue system where higher priority
    values indicate greater urgency. When a space becomes available,
    the highest-priority pending booking is confirmed first.

    Attributes:
        id: Unique identifier for the booking.
        tenant_id: ID of the tenant requesting the booking.
        space_id: ID of the desired space.
        created_at: Timestamp when the booking was created.
        desired_start: Desired rental start date.
        desired_end: Desired rental end date.
        priority: Priority level (higher = more urgent, default 0).
        status: Current booking status.
    """

    id: str
    tenant_id: str
    space_id: str
    desired_start: date
    desired_end: date
    priority: int = 0
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    def confirm(self) -> None:
        """Confirm the booking reservation."""
        self.status = BookingStatus.CONFIRMED

    def cancel(self) -> None:
        """Cancel the booking reservation."""
        self.status = BookingStatus.CANCELLED

    def expire(self) -> None:
        """Mark the booking as expired."""
        self.status = BookingStatus.EXPIRED

    def is_pending(self) -> bool:
        """Check if the booking is still pending confirmation."""
        return self.status == BookingStatus.PENDING

    def is_confirmed(self) -> bool:
        """Check if the booking has been confirmed."""
        return self.status == BookingStatus.CONFIRMED
