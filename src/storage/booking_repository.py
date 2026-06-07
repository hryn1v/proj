"""Booking repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.booking import Booking
from src.models.enums import BookingStatus
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class IBookingRepository(IRepository[Booking]):
    """Interface for booking-specific repository operations."""

    @abstractmethod
    def find_by_tenant(self, tenant_id: str) -> list[Booking]:
        """Find all bookings for a given tenant."""

    @abstractmethod
    def find_by_space(self, space_id: str) -> list[Booking]:
        """Find all bookings for a given space."""

    @abstractmethod
    def find_pending_for_space(self, space_id: str) -> list[Booking]:
        """Find pending bookings for a space, sorted by priority (desc) then created_at (asc)."""

    @abstractmethod
    def find_by_status(self, status: BookingStatus) -> list[Booking]:
        """Find bookings by status."""


class InMemoryBookingRepository(InMemoryBaseRepository[Booking], IBookingRepository):
    """In-memory implementation of the booking repository."""

    def __init__(self) -> None:
        """Initialize the booking repository."""
        super().__init__(entity_name="Booking")

    def find_by_tenant(self, tenant_id: str) -> list[Booking]:
        """Find all bookings for a given tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of bookings for the tenant.
        """
        return self.find_by(lambda b: b.tenant_id == tenant_id)

    def find_by_space(self, space_id: str) -> list[Booking]:
        """Find all bookings for a given space.

        Args:
            space_id: ID of the space.

        Returns:
            List of bookings for the space.
        """
        return self.find_by(lambda b: b.space_id == space_id)

    def find_pending_for_space(self, space_id: str) -> list[Booking]:
        """Find pending bookings for a space, sorted by priority desc then created_at asc.

        Args:
            space_id: ID of the space.

        Returns:
            Sorted list of pending bookings (highest priority first).
        """
        pending = self.find_by(
            lambda b: b.space_id == space_id and b.status == BookingStatus.PENDING
        )
        return sorted(pending, key=lambda b: (-b.priority, b.created_at))

    def find_by_status(self, status: BookingStatus) -> list[Booking]:
        """Find bookings by status.

        Args:
            status: Booking status to filter by.

        Returns:
            List of bookings with the specified status.
        """
        return self.find_by(lambda b: b.status == status)
