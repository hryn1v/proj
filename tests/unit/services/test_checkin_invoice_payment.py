"""Unit tests for CheckInService, InvoiceService, and PaymentService."""
import pytest
from datetime import date, timedelta
from src.models.enums import (
    ContractStatus, InvoiceStatus, InvoiceType, PaymentMethod, SpaceType,
)
from src.services.penalty_strategy import FlatRatePenalty, ProgressivePenalty
from src.utils.exceptions import (
    BusinessRuleViolationError, ContractNotActiveError, EntityNotFoundError,
    InvalidStateTransitionError, InvoiceAlreadyPaidError, ValidationError,
)


# ─── CheckInService Tests ──────────────────────────────────────────────

class TestCheckIn:
    def _setup_active_contract(self, tenant_service, space_service, contract_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        return t, s, c

    def test_check_in_success(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        ci = check_in_service.check_in(t.id, s.id, c.id)
        assert ci.tenant_id == t.id
        assert ci.is_active()

    def test_check_in_inactive_contract_raises(self, check_in_service, tenant_service, space_service, contract_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        with pytest.raises(ContractNotActiveError):
            check_in_service.check_in(t.id, s.id, c.id)

    def test_check_in_wrong_tenant_raises(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        with pytest.raises(BusinessRuleViolationError):
            check_in_service.check_in(t2.id, s.id, c.id)

    def test_check_in_wrong_space_raises(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        s2 = space_service.create_space("S2", SpaceType.PARKING, 15.0, 0, 200.0)
        with pytest.raises(BusinessRuleViolationError):
            check_in_service.check_in(t.id, s2.id, c.id)

    def test_check_in_duplicate_raises(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        check_in_service.check_in(t.id, s.id, c.id)
        with pytest.raises(BusinessRuleViolationError):
            check_in_service.check_in(t.id, s.id, c.id)

    def test_check_out(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        ci = check_in_service.check_in(t.id, s.id, c.id)
        checked_out = check_in_service.check_out(ci.id)
        assert not checked_out.is_active()
        assert checked_out.check_out_date is not None

    def test_check_out_already_out_raises(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        ci = check_in_service.check_in(t.id, s.id, c.id)
        check_in_service.check_out(ci.id)
        with pytest.raises(InvalidStateTransitionError):
            check_in_service.check_out(ci.id)

    def test_get_active_check_ins(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        check_in_service.check_in(t.id, s.id, c.id)
        active = check_in_service.get_active_check_ins()
        assert len(active) == 1

    def test_get_check_in_by_contract(self, check_in_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup_active_contract(tenant_service, space_service, contract_service)
        check_in_service.check_in(t.id, s.id, c.id)
        result = check_in_service.get_check_in_by_contract(c.id)
        assert result is not None


# ─── InvoiceService Tests ──────────────────────────────────────────────

class TestInvoiceService:
    def _setup(self, tenant_service, space_service, contract_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0, 2000.0
        )
        contract_service.activate_contract(c.id)
        return t, s, c

    def test_generate_regular_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        assert inv.type == InvoiceType.REGULAR
        assert inv.base_amount == 1000.0

    def test_generate_deposit_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_deposit_invoice(c.id, date.today())
        assert inv.type == InvoiceType.DEPOSIT
        assert inv.base_amount == 2000.0

    def test_generate_penalty_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_penalty_invoice(c.id, date.today(), 150.0)
        assert inv.type == InvoiceType.PENALTY
        assert inv.base_amount == 150.0

    def test_generate_settlement_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        t, s, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_settlement_invoice(c.id, date.today(), 500.0)
        assert inv.type == InvoiceType.FINAL_SETTLEMENT

    def test_generate_invoice_inactive_contract_raises(self, invoice_service, tenant_service, space_service, contract_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
        )
        with pytest.raises(ContractNotActiveError):
            invoice_service.generate_regular_invoice(c.id, date.today())

    def test_mark_paid(self, invoice_service, tenant_service, space_service, contract_service):
        _, _, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        paid = invoice_service.mark_invoice_paid(inv.id)
        assert paid.status == InvoiceStatus.PAID

    def test_mark_paid_twice_raises(self, invoice_service, tenant_service, space_service, contract_service):
        _, _, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        invoice_service.mark_invoice_paid(inv.id)
        with pytest.raises(InvoiceAlreadyPaidError):
            invoice_service.mark_invoice_paid(inv.id)

    def test_cancel_invoice(self, invoice_service, tenant_service, space_service, contract_service):
        _, _, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        cancelled = invoice_service.cancel_invoice(inv.id)
        assert cancelled.status == InvoiceStatus.CANCELLED

    def test_change_penalty_strategy(self, invoice_service):
        invoice_service.penalty_strategy = FlatRatePenalty(20.0)
        assert isinstance(invoice_service.penalty_strategy, FlatRatePenalty)

    def test_apply_penalties(self, invoice_service, tenant_service, space_service, contract_service):
        _, _, c = self._setup(tenant_service, space_service, contract_service)
        inv = invoice_service.generate_regular_invoice(c.id, date(2024, 1, 1))
        penalized = invoice_service.apply_penalties(date(2024, 2, 15))
        assert len(penalized) == 1
        assert penalized[0].penalty_amount > 0

    def test_get_overdue_invoices(self, invoice_service, tenant_service, space_service, contract_service):
        _, _, c = self._setup(tenant_service, space_service, contract_service)
        invoice_service.generate_regular_invoice(c.id, date(2024, 1, 1))
        overdue = invoice_service.get_overdue_invoices(date(2025, 6, 1))
        assert len(overdue) == 1

    def test_get_invoices_by_tenant(self, invoice_service, tenant_service, space_service, contract_service):
        t, _, c = self._setup(tenant_service, space_service, contract_service)
        invoice_service.generate_regular_invoice(c.id, date.today())
        invoices = invoice_service.get_invoices_by_tenant(t.id)
        assert len(invoices) == 1


# ─── PaymentService Tests ──────────────────────────────────────────────

class TestPaymentService:
    def _setup_with_invoice(self, tenant_service, space_service, contract_service, invoice_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        inv = invoice_service.generate_regular_invoice(c.id, date.today())
        return t, inv

    def test_process_payment(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        pay = payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CARD)
        assert pay.amount == 1000.0
        assert pay.id.startswith("PAY-")

    def test_payment_marks_invoice_paid(self, payment_service, invoice_service, tenant_service, space_service, contract_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CARD)
        updated = invoice_service.get_invoice(inv.id)
        assert updated.is_paid()

    def test_payment_already_paid_raises(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CARD)
        with pytest.raises(InvoiceAlreadyPaidError):
            payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CARD)

    def test_payment_zero_amount_raises(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        with pytest.raises(ValidationError):
            payment_service.process_payment(inv.id, 0, PaymentMethod.CARD)

    def test_payment_insufficient_amount_raises(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        with pytest.raises(ValidationError):
            payment_service.process_payment(inv.id, 500.0, PaymentMethod.CARD)

    def test_get_payment(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        pay = payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CASH)
        fetched = payment_service.get_payment(pay.id)
        assert fetched.id == pay.id

    def test_get_nonexistent_payment_raises(self, payment_service):
        with pytest.raises(EntityNotFoundError):
            payment_service.get_payment("nope")

    def test_get_payments_for_invoice(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        payment_service.process_payment(inv.id, 1000.0, PaymentMethod.BANK_TRANSFER)
        payments = payment_service.get_payments_for_invoice(inv.id)
        assert len(payments) == 1

    def test_get_total_paid(self, payment_service, tenant_service, space_service, contract_service, invoice_service):
        _, inv = self._setup_with_invoice(tenant_service, space_service, contract_service, invoice_service)
        payment_service.process_payment(inv.id, 1000.0, PaymentMethod.CARD)
        total = payment_service.get_total_paid_for_invoice(inv.id)
        assert total == 1000.0
