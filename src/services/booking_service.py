"""Booking management service with priority queue."""
from __future__ import annotations

from datetime import date

from src.models.booking import Booking
from src.models.enums import BookingStatus
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.booking_repository import IBookingRepository
from src.utils.exceptions import (
    DuplicateBookingError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ValidationError,
)
from src.utils.id_generator import generate_prefixed_id
from src.utils.validators import validate_date_range


class BookingService:
    """Service for managing space bookings with priority queue support.

    Handles booking creation, confirmation, cancellation, and
    maintains a priority-based waitlist for occupied spaces.

    Attributes:
        _booking_repo: Repository for booking persistence.
        _tenant_service: Service for tenant validation.
        _space_service: Service for space validation.
    """

    def __init__(
        self,
        booking_repo: IBookingRepository,
        tenant_service: TenantService,
        space_service: SpaceService,
    ) -> None:
        """Initialize with required repositories and services.

        Args:
            booking_repo: Repository implementing IBookingRepository.
            tenant_service: Service for tenant operations.
            space_service: Service for space operations.
        """
        self._booking_repo = booking_repo
        self._tenant_service = tenant_service
        self._space_service = space_service

    def create_booking(
        self,
        tenant_id: str,
        space_id: str,
        desired_start: date,
        desired_end: date,
        priority: int = 0,
    ) -> Booking:
        """Create a new booking/reservation request.

        Args:
            tenant_id: ID of the tenant requesting the booking.
            space_id: ID of the desired space.
            desired_start: Desired rental start date.
            desired_end: Desired rental end date.
            priority: Booking priority (higher = more urgent).

        Returns:
            The newly created booking.

        Raises:
            EntityNotFoundError: If tenant or space not found.
            TenantBlockedError: If tenant is blocked.
            ValidationError: If dates are invalid.
            DuplicateBookingError: If tenant already has a pending booking for this space.
        """
        self._tenant_service.ensure_tenant_active(tenant_id)
        self._space_service.get_space(space_id)

        if not validate_date_range(desired_start, desired_end):
            raise ValidationError("date_range", "Start date must be before end date")

        # Check for duplicate pending bookings
        existing_bookings = self._booking_repo.find_by_tenant(tenant_id)
        for existing in existing_bookings:
            if existing.space_id == space_id and existing.is_pending():
                raise DuplicateBookingError(tenant_id, space_id)

        booking = Booking(
            id=generate_prefixed_id("BKG"),
            tenant_id=tenant_id,
            space_id=space_id,
            desired_start=desired_start,
            desired_end=desired_end,
            priority=priority,
        )
        return self._booking_repo.add(booking)

    def confirm_booking(self, booking_id: str) -> Booking:
        """Confirm a pending booking.

        Args:
            booking_id: ID of the booking to confirm.

        Returns:
            The confirmed booking.

        Raises:
            EntityNotFoundError: If booking not found.
            InvalidStateTransitionError: If booking is not pending.
        """
        booking = self.get_booking(booking_id)
        if not booking.is_pending():
            raise InvalidStateTransitionError(
                "Booking", booking.status.value, BookingStatus.CONFIRMED.value
            )

        booking.confirm()
        return self._booking_repo.update(booking)

    def cancel_booking(self, booking_id: str) -> Booking:
        """Cancel a booking.

        Args:
            booking_id: ID of the booking to cancel.

        Returns:
            The cancelled booking.

        Raises:
            EntityNotFoundError: If booking not found.
            InvalidStateTransitionError: If booking is already cancelled or expired.
        """
        booking = self.get_booking(booking_id)
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.EXPIRED):
            raise InvalidStateTransitionError(
                "Booking", booking.status.value, BookingStatus.CANCELLED.value
            )

        booking.cancel()
        return self._booking_repo.update(booking)

    def expire_booking(self, booking_id: str) -> Booking:
        """Mark a booking as expired.

        Args:
            booking_id: ID of the booking.

        Returns:
            The expired booking.

        Raises:
            EntityNotFoundError: If booking not found.
        """
        booking = self.get_booking(booking_id)
        if not booking.is_pending():
            raise InvalidStateTransitionError(
                "Booking", booking.status.value, BookingStatus.EXPIRED.value
            )

        booking.expire()
        return self._booking_repo.update(booking)

    def get_booking(self, booking_id: str) -> Booking:
        """Retrieve a booking by ID.

        Args:
            booking_id: Unique identifier of the booking.

        Returns:
            The booking.

        Raises:
            EntityNotFoundError: If the booking does not exist.
        """
        booking = self._booking_repo.get_by_id(booking_id)
        if booking is None:
            raise EntityNotFoundError("Booking", booking_id)
        return booking

    def get_pending_bookings_for_space(self, space_id: str) -> list[Booking]:
        """Get all pending bookings for a space, sorted by priority.

        Args:
            space_id: ID of the space.

        Returns:
            List of pending bookings sorted by priority (desc) then created_at (asc).
        """
        return self._booking_repo.find_pending_for_space(space_id)

    def get_bookings_by_tenant(self, tenant_id: str) -> list[Booking]:
        """Get all bookings for a tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of tenant's bookings.
        """
        return self._booking_repo.find_by_tenant(tenant_id)

    def get_next_in_queue(self, space_id: str) -> Booking | None:
        """Get the next booking in the priority queue for a space.

        Args:
            space_id: ID of the space.

        Returns:
            The highest-priority pending booking, or None if queue is empty.
        """
        pending = self._booking_repo.find_pending_for_space(space_id)
        return pending[0] if pending else None

    def expire_old_bookings(self, current_date: date) -> list[Booking]:
        """Expire all bookings whose desired start date has passed.

        Args:
            current_date: Current date to check against.

        Returns:
            List of newly expired bookings.
        """
        expired = []
        pending = self._booking_repo.find_by_status(BookingStatus.PENDING)
        for booking in pending:
            if booking.desired_start < current_date:
                booking.expire()
                self._booking_repo.update(booking)
                expired.append(booking)
        return expired
