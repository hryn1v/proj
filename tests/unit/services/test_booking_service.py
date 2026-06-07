"""Unit tests for BookingService."""
import pytest
from datetime import date, timedelta
from src.models.enums import BookingStatus, SpaceType
from src.utils.exceptions import (
    DuplicateBookingError, EntityNotFoundError, InvalidStateTransitionError,
    TenantBlockedError, ValidationError,
)


class TestCreateBooking:
    def _setup(self, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        return t, s

    def test_create_valid_booking(self, booking_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        b = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        assert b.status == BookingStatus.PENDING
        assert b.id.startswith("BKG-")

    def test_create_with_priority(self, booking_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        b = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=5
        )
        assert b.priority == 5

    def test_create_blocked_tenant_raises(self, booking_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            booking_service.create_booking(
                t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
            )

    def test_create_invalid_dates_raises(self, booking_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        with pytest.raises(ValidationError):
            booking_service.create_booking(t.id, s.id, date.today(), date.today() - timedelta(days=1))

    def test_create_duplicate_raises(self, booking_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        with pytest.raises(DuplicateBookingError):
            booking_service.create_booking(
                t.id, s.id, date.today() + timedelta(days=14), date.today() + timedelta(days=44)
            )


class TestBookingLifecycle:
    def _create_booking(self, booking_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        b = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        return b

    def test_confirm_booking(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        confirmed = booking_service.confirm_booking(b.id)
        assert confirmed.is_confirmed()

    def test_confirm_non_pending_raises(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        booking_service.confirm_booking(b.id)
        with pytest.raises(InvalidStateTransitionError):
            booking_service.confirm_booking(b.id)

    def test_cancel_booking(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        cancelled = booking_service.cancel_booking(b.id)
        assert cancelled.status == BookingStatus.CANCELLED

    def test_cancel_already_cancelled_raises(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        booking_service.cancel_booking(b.id)
        with pytest.raises(InvalidStateTransitionError):
            booking_service.cancel_booking(b.id)

    def test_expire_booking(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        expired = booking_service.expire_booking(b.id)
        assert expired.status == BookingStatus.EXPIRED

    def test_expire_non_pending_raises(self, booking_service, tenant_service, space_service):
        b = self._create_booking(booking_service, tenant_service, space_service)
        booking_service.confirm_booking(b.id)
        with pytest.raises(InvalidStateTransitionError):
            booking_service.expire_booking(b.id)


class TestBookingQueries:
    def test_get_booking(self, booking_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        b = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        fetched = booking_service.get_booking(b.id)
        assert fetched.id == b.id

    def test_get_nonexistent_raises(self, booking_service):
        with pytest.raises(EntityNotFoundError):
            booking_service.get_booking("nope")

    def test_get_pending_by_priority(self, booking_service, tenant_service, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        t1 = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        booking_service.create_booking(
            t1.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=1
        )
        booking_service.create_booking(
            t2.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=10
        )
        pending = booking_service.get_pending_bookings_for_space(s.id)
        assert pending[0].priority == 10

    def test_get_next_in_queue(self, booking_service, tenant_service, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        nxt = booking_service.get_next_in_queue(s.id)
        assert nxt is not None

    def test_get_next_in_queue_empty(self, booking_service, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        assert booking_service.get_next_in_queue(s.id) is None

    def test_expire_old_bookings(self, booking_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        booking_service.create_booking(
            t.id, s.id, date(2024, 1, 1), date(2024, 2, 1)
        )
        expired = booking_service.expire_old_bookings(date(2025, 1, 1))
        assert len(expired) == 1

    def test_get_bookings_by_tenant(self, booking_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        bookings = booking_service.get_bookings_by_tenant(t.id)
        assert len(bookings) == 1
