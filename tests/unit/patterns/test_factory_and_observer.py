"""Unit tests for Factory Method Pattern (Invoice Factories) and Observer Pattern."""
import pytest
from datetime import date
from src.models.enums import InvoiceType, ContractStatus
from src.services.invoice_factory import (
    RegularInvoiceFactory, PenaltyInvoiceFactory,
    DepositInvoiceFactory, FinalSettlementFactory,
)
from src.services.notification_service import (
    SpaceEventPublisher, BookingQueueNotifier, TenantNotifier,
)
from src.storage.booking_repository import InMemoryBookingRepository
from tests.conftest import make_contract, make_booking, make_space


# ─── Invoice Factory Tests ─────────────────────────────────────────────

class TestRegularInvoiceFactory:
    def test_creates_regular_invoice(self):
        f = RegularInvoiceFactory()
        c = make_contract(status=ContractStatus.ACTIVE)
        inv = f.create_invoice(c, date(2025, 1, 1))
        assert inv.type == InvoiceType.REGULAR
        assert inv.base_amount == c.monthly_rate
        assert inv.id.startswith("INV-")

    def test_custom_amount(self):
        f = RegularInvoiceFactory()
        c = make_contract()
        inv = f.create_invoice(c, date(2025, 1, 1), amount=500.0)
        assert inv.base_amount == 500.0

    def test_due_date_30_days(self):
        f = RegularInvoiceFactory(payment_terms_days=30)
        c = make_contract()
        inv = f.create_invoice(c, date(2025, 1, 1))
        assert inv.due_date == date(2025, 1, 31)


class TestPenaltyInvoiceFactory:
    def test_creates_penalty_invoice(self):
        f = PenaltyInvoiceFactory()
        c = make_contract()
        inv = f.create_invoice(c, date(2025, 1, 1), amount=100.0)
        assert inv.type == InvoiceType.PENALTY
        assert inv.base_amount == 100.0
        assert inv.id.startswith("PEN-")

    def test_no_amount_raises(self):
        f = PenaltyInvoiceFactory()
        c = make_contract()
        with pytest.raises(ValueError):
            f.create_invoice(c, date(2025, 1, 1))

    def test_zero_amount_raises(self):
        f = PenaltyInvoiceFactory()
        c = make_contract()
        with pytest.raises(ValueError):
            f.create_invoice(c, date(2025, 1, 1), amount=0)

    def test_due_date_7_days(self):
        f = PenaltyInvoiceFactory(payment_terms_days=7)
        c = make_contract()
        inv = f.create_invoice(c, date(2025, 1, 1), amount=50.0)
        assert inv.due_date == date(2025, 1, 8)


class TestDepositInvoiceFactory:
    def test_creates_deposit_invoice(self):
        f = DepositInvoiceFactory()
        c = make_contract(deposit=2000.0)
        inv = f.create_invoice(c, date(2025, 1, 1))
        assert inv.type == InvoiceType.DEPOSIT
        assert inv.base_amount == 2000.0
        assert inv.id.startswith("DEP-")


class TestFinalSettlementFactory:
    def test_creates_settlement_invoice(self):
        f = FinalSettlementFactory()
        c = make_contract()
        inv = f.create_invoice(c, date(2025, 1, 1), amount=500.0)
        assert inv.type == InvoiceType.FINAL_SETTLEMENT
        assert inv.id.startswith("SET-")

    def test_no_amount_raises(self):
        f = FinalSettlementFactory()
        c = make_contract()
        with pytest.raises(ValueError):
            f.create_invoice(c, date(2025, 1, 1))


# ─── Observer Pattern Tests ────────────────────────────────────────────

class TestSpaceEventPublisher:
    def test_subscribe_and_publish(self):
        pub = SpaceEventPublisher()
        notifier = TenantNotifier()
        pub.subscribe("space_available", notifier)
        space = make_space()
        pub.publish("space_available", space, tenant_id="T1")
        assert len(notifier.notifications) == 1

    def test_unsubscribe(self):
        pub = SpaceEventPublisher()
        notifier = TenantNotifier()
        pub.subscribe("space_available", notifier)
        pub.unsubscribe("space_available", notifier)
        pub.publish("space_available", make_space(), tenant_id="T1")
        assert len(notifier.notifications) == 0

    def test_no_duplicate_subscribe(self):
        pub = SpaceEventPublisher()
        notifier = TenantNotifier()
        pub.subscribe("space_available", notifier)
        pub.subscribe("space_available", notifier)
        assert pub.get_subscriber_count("space_available") == 1

    def test_publish_no_subscribers(self):
        pub = SpaceEventPublisher()
        pub.publish("space_available", make_space())  # should not raise

    def test_multiple_subscribers(self):
        pub = SpaceEventPublisher()
        n1 = TenantNotifier()
        n2 = TenantNotifier()
        pub.subscribe("space_available", n1)
        pub.subscribe("space_available", n2)
        pub.publish("space_available", make_space(), tenant_id="T1")
        assert len(n1.notifications) == 1
        assert len(n2.notifications) == 1


class TestBookingQueueNotifier:
    def test_auto_confirms_top_booking(self):
        repo = InMemoryBookingRepository()
        b1 = make_booking(id="B1", space_id="S1", priority=1)
        b2 = make_booking(id="B2", space_id="S1", priority=10)
        repo.add(b1)
        repo.add(b2)
        notifier = BookingQueueNotifier(repo)
        space = make_space(id="S1")
        notifier.on_event("space_available", space)
        assert notifier.last_confirmed_booking_id == "B2"
        assert repo.get_by_id("B2").is_confirmed()

    def test_no_pending_bookings(self):
        repo = InMemoryBookingRepository()
        notifier = BookingQueueNotifier(repo)
        space = make_space(id="S1")
        notifier.on_event("space_available", space)
        assert notifier.last_confirmed_booking_id is None

    def test_ignores_non_available_events(self):
        repo = InMemoryBookingRepository()
        repo.add(make_booking(id="B1", space_id="S1"))
        notifier = BookingQueueNotifier(repo)
        space = make_space(id="S1")
        notifier.on_event("space_occupied", space)
        assert notifier.last_confirmed_booking_id is None


class TestTenantNotifier:
    def test_creates_notification(self):
        n = TenantNotifier()
        n.on_event("space_available", make_space(), tenant_id="T1")
        assert len(n.notifications) == 1
        assert n.notifications[0].tenant_id == "T1"

    def test_no_tenant_id_skips(self):
        n = TenantNotifier()
        n.on_event("space_available", make_space())
        assert len(n.notifications) == 0

    def test_get_notifications_for_tenant(self):
        n = TenantNotifier()
        n.on_event("space_available", make_space(), tenant_id="T1")
        n.on_event("space_available", make_space(), tenant_id="T2")
        assert len(n.get_notifications_for_tenant("T1")) == 1

    def test_unread_count(self):
        n = TenantNotifier()
        n.on_event("space_available", make_space(), tenant_id="T1")
        n.on_event("space_available", make_space(id="S2", name="S2"), tenant_id="T1")
        assert n.get_unread_count("T1") == 2
        n.notifications[0].mark_read()
        assert n.get_unread_count("T1") == 1
