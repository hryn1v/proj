"""Integration tests for cross-service workflows."""
import pytest
from datetime import date, timedelta
from src.models.enums import (
    BookingStatus, CheckInStatus, ContractStatus, InvoiceStatus,
    InvoiceType, PaymentMethod, SpaceStatus, SpaceType, TenantStatus,
)
from src.services.penalty_strategy import FlatRatePenalty, ProgressivePenalty
from src.services.notification_service import (
    BookingQueueNotifier, SpaceEventPublisher, TenantNotifier,
)


class TestFullRentalLifecycle:
    """End-to-end test: register → book → contract → check-in → invoice → pay → check-out."""

    def test_complete_rental_lifecycle(
        self, tenant_service, space_service, contract_service,
        booking_service, check_in_service, invoice_service, payment_service,
    ):
        # 1. Register tenant
        tenant = tenant_service.register_tenant("Alice", "alice@test.com", "+380501234567")
        assert tenant.is_active()

        # 2. Create space
        space = space_service.create_space("Office 301", SpaceType.OFFICE, 75.0, 3, 1500.0)
        assert space.is_available()

        # 3. Book space
        booking = booking_service.create_booking(
            tenant.id, space.id,
            date.today() + timedelta(days=7),
            date.today() + timedelta(days=367),
        )
        assert booking.is_pending()

        # 4. Confirm booking
        booking = booking_service.confirm_booking(booking.id)
        assert booking.is_confirmed()

        # 5. Create contract
        contract = contract_service.create_contract(
            tenant.id, space.id,
            date.today(), date.today() + timedelta(days=365),
            1500.0, 3000.0,
        )
        assert contract.is_draft()

        # 6. Activate contract (occupies space)
        contract = contract_service.activate_contract(contract.id)
        assert contract.is_active()
        space = space_service.get_space(space.id)
        assert space.status == SpaceStatus.OCCUPIED

        # 7. Check-in tenant
        check_in = check_in_service.check_in(tenant.id, space.id, contract.id)
        assert check_in.is_active()

        # 8. Generate and pay invoice
        invoice = invoice_service.generate_regular_invoice(contract.id, date.today())
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.base_amount == 1500.0

        payment = payment_service.process_payment(invoice.id, 1500.0, PaymentMethod.CARD)
        invoice = invoice_service.get_invoice(invoice.id)
        assert invoice.is_paid()

        # 9. Check-out
        check_in = check_in_service.check_out(check_in.id)
        assert not check_in.is_active()

        # 10. Terminate contract (releases space)
        contract = contract_service.terminate_contract(contract.id)
        assert contract.status == ContractStatus.TERMINATED
        space = space_service.get_space(space.id)
        assert space.is_available()


class TestBookingToContractFlow:
    def test_booking_confirmed_then_contract(
        self, tenant_service, space_service, booking_service, contract_service,
    ):
        t = tenant_service.register_tenant("Bob", "bob@test.com", "+380502222222")
        s = space_service.create_space("Apt 101", SpaceType.APARTMENT, 60.0, 1, 2000.0)

        b = booking_service.create_booking(
            t.id, s.id, date.today() + timedelta(days=14), date.today() + timedelta(days=194)
        )
        booking_service.confirm_booking(b.id)

        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=180), 2000.0
        )
        contract_service.activate_contract(c.id)
        assert space_service.get_space(s.id).status == SpaceStatus.OCCUPIED


class TestPenaltyEscalationFlow:
    def test_overdue_triggers_penalty_and_violation(
        self, tenant_service, space_service, contract_service, invoice_service,
    ):
        t = tenant_service.register_tenant("Carl", "carl@test.com", "+380503333333")
        s = space_service.create_space("Park P1", SpaceType.PARKING, 15.0, 0, 200.0)
        c = contract_service.create_contract(
            t.id, s.id, date(2024, 1, 1), date(2025, 12, 31), 200.0
        )
        contract_service.activate_contract(c.id)

        # Generate invoice with past due date
        inv = invoice_service.generate_regular_invoice(c.id, date(2024, 1, 1))

        # Apply penalties 45 days later
        invoice_service.penalty_strategy = FlatRatePenalty(5.0)
        penalized = invoice_service.apply_penalties(date(2024, 3, 1))

        assert len(penalized) == 1
        assert penalized[0].penalty_amount > 0

        # Tenant should have a violation
        updated_t = tenant_service.get_tenant(t.id)
        assert updated_t.violation_count >= 1


class TestTenantBlockingFlow:
    def test_auto_block_after_multiple_violations(
        self, tenant_service, space_service, contract_service, invoice_service,
    ):
        t = tenant_service.register_tenant("Dan", "dan@test.com", "+380504444444")
        s = space_service.create_space("WH1", SpaceType.WAREHOUSE, 200.0, 0, 3000.0)
        c = contract_service.create_contract(
            t.id, s.id, date(2024, 1, 1), date(2025, 12, 31), 3000.0
        )
        contract_service.activate_contract(c.id)

        # Create 3 overdue invoices and apply penalties
        for month in range(1, 4):
            invoice_service.generate_regular_invoice(c.id, date(2024, month, 1))

        # Apply penalties much later
        invoice_service.apply_penalties(date(2024, 12, 1))

        tenant = tenant_service.get_tenant(t.id)
        assert tenant.is_blocked()
        assert tenant.violation_count >= 3


class TestObserverIntegration:
    def test_space_release_auto_confirms_booking(
        self, space_repo, booking_repo, tenant_service,
    ):
        pub = SpaceEventPublisher()
        notifier = BookingQueueNotifier(booking_repo)
        tenant_notifier = TenantNotifier()
        pub.subscribe("space_available", notifier)
        pub.subscribe("space_available", tenant_notifier)

        from src.services.space_service import SpaceService
        space_svc = SpaceService(space_repo, pub)

        # Create space and tenants
        s = space_svc.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        t1 = tenant_service.register_tenant("Eve", "eve@test.com", "+380505555555")
        t2 = tenant_service.register_tenant("Frank", "frank@test.com", "+380506666666")

        # Add bookings with priorities
        from src.models.booking import Booking
        from src.utils.id_generator import generate_prefixed_id
        b1 = Booking(
            id=generate_prefixed_id("BKG"), tenant_id=t1.id, space_id=s.id,
            desired_start=date.today() + timedelta(days=7),
            desired_end=date.today() + timedelta(days=37),
            priority=1,
        )
        b2 = Booking(
            id=generate_prefixed_id("BKG"), tenant_id=t2.id, space_id=s.id,
            desired_start=date.today() + timedelta(days=7),
            desired_end=date.today() + timedelta(days=37),
            priority=10,
        )
        booking_repo.add(b1)
        booking_repo.add(b2)

        # Occupy then release space
        space_svc.occupy_space(s.id)
        space_svc.release_space(s.id, tenant_id=t2.id)

        # Highest priority booking should be auto-confirmed
        assert booking_repo.get_by_id(b2.id).is_confirmed()
        assert booking_repo.get_by_id(b1.id).is_pending()

        # Tenant notifier should have a notification
        assert len(tenant_notifier.get_notifications_for_tenant(t2.id)) == 1


class TestContractExpirationFlow:
    def test_expired_contracts_release_spaces(
        self, tenant_service, space_service, contract_service,
    ):
        t = tenant_service.register_tenant("Gina", "gina@test.com", "+380507777777")
        s = space_service.create_space("O2", SpaceType.OFFICE, 40.0, 2, 800.0)
        c = contract_service.create_contract(
            t.id, s.id, date(2024, 1, 1), date(2024, 6, 1), 800.0
        )
        contract_service.activate_contract(c.id)
        assert space_service.get_space(s.id).status == SpaceStatus.OCCUPIED

        expired = contract_service.check_and_expire_contracts(date(2025, 1, 1))
        assert len(expired) == 1
        assert space_service.get_space(s.id).is_available()


class TestCheckInCheckOutFlow:
    def test_check_in_and_out_with_settlement(
        self, tenant_service, space_service, contract_service,
        check_in_service, invoice_service, payment_service,
    ):
        t = tenant_service.register_tenant("Hanna", "hanna@test.com", "+380508888888")
        s = space_service.create_space("Apt 202", SpaceType.APARTMENT, 90.0, 2, 2500.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 2500.0, 5000.0
        )
        contract_service.activate_contract(c.id)

        # Check in
        ci = check_in_service.check_in(t.id, s.id, c.id)
        assert ci.is_active()

        # Generate deposit invoice and pay
        dep_inv = invoice_service.generate_deposit_invoice(c.id, date.today())
        payment_service.process_payment(dep_inv.id, dep_inv.total_amount, PaymentMethod.BANK_TRANSFER)

        # Check out
        ci = check_in_service.check_out(ci.id)
        assert not ci.is_active()

        # Generate settlement
        settle_inv = invoice_service.generate_settlement_invoice(c.id, date.today(), 500.0)
        assert settle_inv.type == InvoiceType.FINAL_SETTLEMENT
        payment_service.process_payment(settle_inv.id, 500.0, PaymentMethod.CARD)

        # All invoices should be paid
        invoices = invoice_service.get_invoices_by_contract(c.id)
        assert all(inv.is_paid() for inv in invoices)


class TestMultipleTenantsSameSpace:
    def test_sequential_tenants(
        self, tenant_service, space_service, contract_service,
    ):
        s = space_service.create_space("O1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        t1 = tenant_service.register_tenant("T1", "t1@test.com", "+380501111111")
        t2 = tenant_service.register_tenant("T2", "t2@test.com", "+380502222222")

        # First tenant contracts and leaves
        c1 = contract_service.create_contract(
            t1.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
        )
        contract_service.activate_contract(c1.id)
        contract_service.terminate_contract(c1.id)

        # Space should be available for second tenant
        assert space_service.get_space(s.id).is_available()
        c2 = contract_service.create_contract(
            t2.id, s.id, date.today(), date.today() + timedelta(days=60), 1100.0
        )
        contract_service.activate_contract(c2.id)
        assert space_service.get_space(s.id).status == SpaceStatus.OCCUPIED
