"""Unit tests for Booking, CheckIn, Invoice, Payment, and Notification models."""
from datetime import date, datetime

from src.models.check_in import CheckIn
from src.models.enums import (
    BookingStatus,
    CheckInStatus,
    InvoiceStatus,
    InvoiceType,
    PaymentMethod,
)
from src.models.notification import Notification
from tests.conftest import make_booking, make_invoice, make_payment

# ─── Booking Tests ─────────────────────────────────────────────────────

class TestBooking:
    def test_create_booking_defaults(self):
        booking = make_booking()
        assert booking.status == BookingStatus.PENDING
        assert booking.priority == 0

    def test_confirm_booking(self):
        booking = make_booking()
        booking.confirm()
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.is_confirmed() is True

    def test_cancel_booking(self):
        booking = make_booking()
        booking.cancel()
        assert booking.status == BookingStatus.CANCELLED

    def test_expire_booking(self):
        booking = make_booking()
        booking.expire()
        assert booking.status == BookingStatus.EXPIRED

    def test_is_pending(self):
        booking = make_booking()
        assert booking.is_pending() is True

    def test_is_not_pending_after_confirm(self):
        booking = make_booking()
        booking.confirm()
        assert booking.is_pending() is False

    def test_booking_with_priority(self):
        booking = make_booking(priority=10)
        assert booking.priority == 10


# ─── CheckIn Tests ─────────────────────────────────────────────────────

class TestCheckIn:
    def test_create_check_in_defaults(self):
        ci = CheckIn(id="CHK-1", tenant_id="T1", space_id="S1", contract_id="C1")
        assert ci.status == CheckInStatus.CHECKED_IN
        assert ci.check_out_date is None
        assert ci.is_active() is True

    def test_check_out(self):
        ci = CheckIn(id="CHK-1", tenant_id="T1", space_id="S1", contract_id="C1")
        ci.check_out()
        assert ci.status == CheckInStatus.CHECKED_OUT
        assert ci.check_out_date is not None
        assert ci.is_active() is False

    def test_duration_days_none_when_active(self):
        ci = CheckIn(id="CHK-1", tenant_id="T1", space_id="S1", contract_id="C1")
        assert ci.duration_days() is None

    def test_duration_days_after_checkout(self):
        ci = CheckIn(
            id="CHK-1", tenant_id="T1", space_id="S1", contract_id="C1",
            check_in_date=datetime(2025, 1, 1, 10, 0),
        )
        ci.check_out_date = datetime(2025, 1, 11, 10, 0)
        ci.status = CheckInStatus.CHECKED_OUT
        assert ci.duration_days() == 10


# ─── Invoice Tests ─────────────────────────────────────────────────────

class TestInvoice:
    def test_create_invoice_defaults(self):
        inv = make_invoice()
        assert inv.status == InvoiceStatus.PENDING
        assert inv.type == InvoiceType.REGULAR
        assert inv.penalty_amount == 0.0

    def test_total_amount_no_penalty(self):
        inv = make_invoice(base_amount=1000.0)
        assert inv.total_amount == 1000.0

    def test_total_amount_with_penalty(self):
        inv = make_invoice(base_amount=1000.0, penalty_amount=200.0)
        assert inv.total_amount == 1200.0

    def test_add_penalty(self):
        inv = make_invoice()
        inv.add_penalty(50.0)
        assert inv.penalty_amount == 50.0
        inv.add_penalty(30.0)
        assert inv.penalty_amount == 80.0

    def test_add_negative_penalty_ignored(self):
        inv = make_invoice()
        inv.add_penalty(-10.0)
        assert inv.penalty_amount == 0.0

    def test_mark_paid(self):
        inv = make_invoice()
        inv.mark_paid()
        assert inv.is_paid() is True
        assert inv.status == InvoiceStatus.PAID

    def test_mark_overdue(self):
        inv = make_invoice()
        inv.mark_overdue()
        assert inv.status == InvoiceStatus.OVERDUE

    def test_cancel_invoice(self):
        inv = make_invoice()
        inv.cancel()
        assert inv.status == InvoiceStatus.CANCELLED

    def test_is_overdue_when_past_due(self):
        inv = make_invoice(due_date=date(2024, 1, 1))
        assert inv.is_overdue(date(2024, 2, 1)) is True

    def test_is_not_overdue_when_before_due(self):
        inv = make_invoice(due_date=date(2026, 12, 31))
        assert inv.is_overdue(date(2025, 1, 1)) is False

    def test_is_not_overdue_when_paid(self):
        inv = make_invoice(due_date=date(2024, 1, 1))
        inv.mark_paid()
        assert inv.is_overdue(date(2025, 1, 1)) is False

    def test_days_overdue(self):
        inv = make_invoice(due_date=date(2025, 1, 1))
        assert inv.days_overdue(date(2025, 1, 11)) == 10

    def test_days_overdue_zero_when_not_overdue(self):
        inv = make_invoice(due_date=date(2026, 12, 31))
        assert inv.days_overdue(date(2025, 1, 1)) == 0


# ─── Payment Tests ─────────────────────────────────────────────────────

class TestPayment:
    def test_create_payment(self):
        pay = make_payment()
        assert pay.id == "PAY-test001"
        assert pay.amount == 1000.0
        assert pay.method == PaymentMethod.CARD

    def test_payment_date_is_set(self):
        pay = make_payment()
        assert pay.payment_date is not None

    def test_payment_with_bank_transfer(self):
        pay = make_payment(method=PaymentMethod.BANK_TRANSFER)
        assert pay.method == PaymentMethod.BANK_TRANSFER

    def test_payment_with_cash(self):
        pay = make_payment(method=PaymentMethod.CASH)
        assert pay.method == PaymentMethod.CASH


# ─── Notification Tests ───────────────────────────────────────────────

class TestNotification:
    def test_create_notification(self):
        n = Notification(id="NTF-1", tenant_id="T1", message="Hello")
        assert n.is_read is False
        assert n.message == "Hello"

    def test_mark_read(self):
        n = Notification(id="NTF-1", tenant_id="T1", message="Hello")
        n.mark_read()
        assert n.is_read is True
