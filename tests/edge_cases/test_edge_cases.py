"""Edge case tests for boundary conditions and extreme scenarios."""
import pytest
from datetime import date, timedelta
from src.models.enums import (
    BookingStatus, ContractStatus, InvoiceStatus,
    PaymentMethod, SpaceType, TenantStatus,
)
from src.utils.exceptions import (
    BusinessRuleViolationError, ContractNotActiveError, DuplicateBookingError,
    EntityNotFoundError, InvalidStateTransitionError, InvoiceAlreadyPaidError,
    SpaceNotAvailableError, TenantBlockedError, ValidationError,
)
from src.services.penalty_strategy import FlatRatePenalty, PercentagePenalty, ProgressivePenalty
from tests.conftest import make_invoice


class TestDateBoundaryConditions:
    """Edge cases around date boundaries."""

    def test_contract_start_equals_end_invalid(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        today = date.today()
        with pytest.raises(ValidationError):
            contract_service.create_contract(t.id, s.id, today, today, 1000.0)

    def test_booking_start_equals_end_invalid(self, booking_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        today = date.today()
        with pytest.raises(ValidationError):
            booking_service.create_booking(t.id, s.id, today, today)

    def test_contract_one_day_duration(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        today = date.today()
        c = contract_service.create_contract(t.id, s.id, today, today + timedelta(days=1), 1000.0)
        assert c.duration_months() == 0

    def test_invoice_due_today_not_overdue(self):
        today = date.today()
        inv = make_invoice(due_date=today)
        assert inv.is_overdue(today) is False

    def test_invoice_due_yesterday_is_overdue(self):
        yesterday = date.today() - timedelta(days=1)
        inv = make_invoice(due_date=yesterday)
        assert inv.is_overdue(date.today()) is True

    def test_invoice_zero_days_overdue_on_due_date(self):
        today = date.today()
        inv = make_invoice(due_date=today)
        assert inv.days_overdue(today) == 0

    def test_invoice_one_day_overdue(self):
        yesterday = date.today() - timedelta(days=1)
        inv = make_invoice(due_date=yesterday)
        assert inv.days_overdue(date.today()) == 1


class TestInvalidStateTransitions:
    """Edge cases for state machine violations."""

    def test_activate_terminated_contract(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        contract_service.terminate_contract(c.id)
        with pytest.raises(InvalidStateTransitionError):
            contract_service.activate_contract(c.id)

    def test_cancel_active_contract(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        with pytest.raises(InvalidStateTransitionError):
            contract_service.cancel_contract(c.id)

    def test_expire_draft_contract(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        with pytest.raises(ContractNotActiveError):
            contract_service.expire_contract(c.id)

    def test_cancel_paid_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        invoice_service.mark_invoice_paid(inv.id)
        with pytest.raises(InvoiceAlreadyPaidError):
            invoice_service.cancel_invoice(inv.id)


class TestExtremeValues:
    """Edge cases with extreme or unusual values."""

    def test_very_high_monthly_rate(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("Rich", "rich@test.com", "+380501111111")
        s = space_service.create_space("Penthouse", SpaceType.APARTMENT, 500.0, 50, 999999.99)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 999999.99
        )
        assert c.monthly_rate == 999999.99

    def test_very_small_positive_amount(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("Cheap", "cheap@test.com", "+380501111111")
        s = space_service.create_space("Closet", SpaceType.PARKING, 1.0, 0, 0.01)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 0.01
        )
        assert c.monthly_rate == 0.01

    def test_penalty_on_zero_base_amount(self):
        inv = make_invoice(base_amount=0.01)
        s = PercentagePenalty(0.01)
        result = s.calculate(inv, 10)
        assert result == pytest.approx(0.001, abs=0.0001)

    def test_progressive_penalty_boundary_day_7(self):
        s = ProgressivePenalty(0.01, 0.02, 0.05)
        inv = make_invoice(base_amount=1000.0)
        # Exactly 7 days: only tier1
        assert s.calculate(inv, 7) == 70.0

    def test_progressive_penalty_boundary_day_8(self):
        s = ProgressivePenalty(0.01, 0.02, 0.05)
        inv = make_invoice(base_amount=1000.0)
        # 8 days: 7 tier1 + 1 tier2 = 70 + 20 = 90
        assert s.calculate(inv, 8) == 90.0

    def test_progressive_penalty_boundary_day_30(self):
        s = ProgressivePenalty(0.01, 0.02, 0.05)
        inv = make_invoice(base_amount=1000.0)
        # 30 days: 7*10 + 23*20 = 70 + 460 = 530
        assert s.calculate(inv, 30) == 530.0

    def test_progressive_penalty_boundary_day_31(self):
        s = ProgressivePenalty(0.01, 0.02, 0.05)
        inv = make_invoice(base_amount=1000.0)
        # 31 days: 70 + 460 + 1*50 = 580
        assert s.calculate(inv, 31) == 580.0


class TestConcurrentBookings:
    """Edge cases for multiple bookings on the same space."""

    def test_different_tenants_same_space_booking(
        self, booking_service, tenant_service, space_service,
    ):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        t1 = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        t3 = tenant_service.register_tenant("C", "c@t.com", "+380503333333")

        booking_service.create_booking(
            t1.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=1
        )
        booking_service.create_booking(
            t2.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=5
        )
        booking_service.create_booking(
            t3.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37), priority=3
        )

        pending = booking_service.get_pending_bookings_for_space(s.id)
        assert len(pending) == 3
        assert pending[0].tenant_id == t2.id  # highest priority

    def test_cancelled_booking_allows_new_one(
        self, booking_service, tenant_service, space_service,
    ):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)

        b1 = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
        )
        booking_service.cancel_booking(b1.id)

        # Should be able to create new booking now
        b2 = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=14), date.today() + timedelta(days=44)
        )
        assert b2.is_pending()


class TestBlockedTenantRestrictions:
    """Verify blocked tenants cannot perform restricted actions."""

    def test_blocked_cannot_create_contract(
        self, contract_service, tenant_service, space_service,
    ):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            contract_service.create_contract(
                t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
            )

    def test_blocked_cannot_book(
        self, booking_service, tenant_service, space_service,
    ):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            booking_service.create_booking(
                t.id, s.id, date.today() + timedelta(days=7), date.today() + timedelta(days=37)
            )

    def test_blocked_cannot_check_in(
        self, check_in_service, tenant_service, space_service, contract_service,
    ):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            check_in_service.check_in(t.id, s.id, c.id)
