"""Unit tests for all repository implementations."""
from datetime import date

import pytest

from src.models.check_in import CheckIn
from src.models.enums import (
    BookingStatus,
    ContractStatus,
    InvoiceStatus,
    SpaceStatus,
    SpaceType,
    TenantStatus,
)
from src.utils.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from tests.conftest import (
    make_booking,
    make_contract,
    make_invoice,
    make_payment,
    make_space,
    make_tenant,
)

# ─── Base Repository CRUD Tests (via TenantRepository) ─────────────────

class TestBaseRepositoryCRUD:
    def test_add_entity(self, tenant_repo):
        t = make_tenant()
        result = tenant_repo.add(t)
        assert result.id == t.id
        assert tenant_repo.count() == 1

    def test_add_duplicate_raises(self, tenant_repo):
        t = make_tenant()
        tenant_repo.add(t)
        with pytest.raises(EntityAlreadyExistsError):
            tenant_repo.add(t)

    def test_get_by_id_found(self, tenant_repo):
        t = make_tenant()
        tenant_repo.add(t)
        result = tenant_repo.get_by_id("TNT-test001")
        assert result is not None
        assert result.name == "John Doe"

    def test_get_by_id_not_found(self, tenant_repo):
        result = tenant_repo.get_by_id("nonexistent")
        assert result is None

    def test_get_all_empty(self, tenant_repo):
        assert tenant_repo.get_all() == []

    def test_get_all_multiple(self, tenant_repo):
        tenant_repo.add(make_tenant(id="T1", email="a@b.com"))
        tenant_repo.add(make_tenant(id="T2", email="c@d.com"))
        assert len(tenant_repo.get_all()) == 2

    def test_exists_true(self, tenant_repo):
        tenant_repo.add(make_tenant())
        assert tenant_repo.exists("TNT-test001") is True

    def test_exists_false(self, tenant_repo):
        assert tenant_repo.exists("nonexistent") is False

    def test_count(self, tenant_repo):
        assert tenant_repo.count() == 0
        tenant_repo.add(make_tenant())
        assert tenant_repo.count() == 1

    def test_update_existing(self, tenant_repo):
        t = make_tenant()
        tenant_repo.add(t)
        t.name = "Updated Name"
        result = tenant_repo.update(t)
        assert result.name == "Updated Name"

    def test_update_nonexistent_raises(self, tenant_repo):
        t = make_tenant()
        with pytest.raises(EntityNotFoundError):
            tenant_repo.update(t)

    def test_delete_existing(self, tenant_repo):
        tenant_repo.add(make_tenant())
        assert tenant_repo.delete("TNT-test001") is True
        assert tenant_repo.count() == 0

    def test_delete_nonexistent(self, tenant_repo):
        assert tenant_repo.delete("nonexistent") is False

    def test_clear(self, tenant_repo):
        tenant_repo.add(make_tenant(id="T1", email="a@b.com"))
        tenant_repo.add(make_tenant(id="T2", email="c@d.com"))
        tenant_repo.clear()
        assert tenant_repo.count() == 0

    def test_find_by_predicate(self, tenant_repo):
        tenant_repo.add(make_tenant(id="T1", name="Alice", email="a@b.com"))
        tenant_repo.add(make_tenant(id="T2", name="Bob", email="c@d.com"))
        results = tenant_repo.find_by(lambda t: t.name == "Alice")
        assert len(results) == 1
        assert results[0].name == "Alice"


# ─── Tenant Repository Specific Tests ──────────────────────────────────

class TestTenantRepository:
    def test_find_by_email(self, tenant_repo):
        tenant_repo.add(make_tenant(email="test@example.com"))
        result = tenant_repo.find_by_email("test@example.com")
        assert result is not None
        assert result.email == "test@example.com"

    def test_find_by_email_not_found(self, tenant_repo):
        assert tenant_repo.find_by_email("nope@nope.com") is None

    def test_find_by_status(self, tenant_repo):
        tenant_repo.add(make_tenant(id="T1", email="a@b.com", status=TenantStatus.ACTIVE))
        tenant_repo.add(make_tenant(id="T2", email="c@d.com", status=TenantStatus.BLOCKED))
        active = tenant_repo.find_by_status(TenantStatus.ACTIVE)
        assert len(active) == 1

    def test_find_active(self, tenant_repo):
        tenant_repo.add(make_tenant(id="T1", email="a@b.com"))
        tenant_repo.add(make_tenant(id="T2", email="c@d.com", status=TenantStatus.BLOCKED))
        active = tenant_repo.find_active()
        assert len(active) == 1


# ─── Space Repository Specific Tests ───────────────────────────────────

class TestSpaceRepository:
    def test_find_by_type(self, space_repo):
        space_repo.add(make_space(id="S1", type=SpaceType.OFFICE))
        space_repo.add(make_space(id="S2", name="Apt", type=SpaceType.APARTMENT))
        offices = space_repo.find_by_type(SpaceType.OFFICE)
        assert len(offices) == 1

    def test_find_available(self, space_repo):
        space_repo.add(make_space(id="S1"))
        space_repo.add(make_space(id="S2", name="Occ", status=SpaceStatus.OCCUPIED))
        available = space_repo.find_available()
        assert len(available) == 1

    def test_find_by_status(self, space_repo):
        space_repo.add(make_space(id="S1", status=SpaceStatus.MAINTENANCE))
        result = space_repo.find_by_status(SpaceStatus.MAINTENANCE)
        assert len(result) == 1

    def test_find_by_floor(self, space_repo):
        space_repo.add(make_space(id="S1", floor=1))
        space_repo.add(make_space(id="S2", name="F2", floor=2))
        f1 = space_repo.find_by_floor(1)
        assert len(f1) == 1


# ─── Contract Repository Specific Tests ────────────────────────────────

class TestContractRepository:
    def test_find_by_tenant(self, contract_repo):
        contract_repo.add(make_contract(id="C1", tenant_id="T1"))
        contract_repo.add(make_contract(id="C2", tenant_id="T2", space_id="S2"))
        results = contract_repo.find_by_tenant("T1")
        assert len(results) == 1

    def test_find_by_space(self, contract_repo):
        contract_repo.add(make_contract(id="C1", space_id="S1"))
        results = contract_repo.find_by_space("S1")
        assert len(results) == 1

    def test_find_active(self, contract_repo):
        contract_repo.add(make_contract(id="C1", status=ContractStatus.ACTIVE))
        contract_repo.add(make_contract(id="C2", space_id="S2"))
        active = contract_repo.find_active()
        assert len(active) == 1

    def test_find_active_for_space(self, contract_repo):
        contract_repo.add(make_contract(id="C1", space_id="S1", status=ContractStatus.ACTIVE))
        result = contract_repo.find_active_for_space("S1")
        assert result is not None
        assert result.id == "C1"

    def test_find_active_for_space_none(self, contract_repo):
        contract_repo.add(make_contract(id="C1", space_id="S1"))
        result = contract_repo.find_active_for_space("S1")
        assert result is None

    def test_find_by_status(self, contract_repo):
        contract_repo.add(make_contract(id="C1", status=ContractStatus.TERMINATED))
        result = contract_repo.find_by_status(ContractStatus.TERMINATED)
        assert len(result) == 1


# ─── Booking Repository Specific Tests ─────────────────────────────────

class TestBookingRepository:
    def test_find_by_tenant(self, booking_repo):
        booking_repo.add(make_booking(id="B1", tenant_id="T1"))
        results = booking_repo.find_by_tenant("T1")
        assert len(results) == 1

    def test_find_by_space(self, booking_repo):
        booking_repo.add(make_booking(id="B1", space_id="S1"))
        results = booking_repo.find_by_space("S1")
        assert len(results) == 1

    def test_find_pending_for_space_sorted(self, booking_repo):
        booking_repo.add(make_booking(id="B1", space_id="S1", priority=1))
        booking_repo.add(make_booking(id="B2", space_id="S1", priority=5))
        booking_repo.add(make_booking(id="B3", space_id="S1", priority=3))
        pending = booking_repo.find_pending_for_space("S1")
        assert len(pending) == 3
        assert pending[0].id == "B2"  # highest priority
        assert pending[1].id == "B3"
        assert pending[2].id == "B1"

    def test_find_pending_excludes_non_pending(self, booking_repo):
        b = make_booking(id="B1", space_id="S1")
        b.confirm()
        booking_repo.add(b)
        booking_repo.add(make_booking(id="B2", space_id="S1"))
        pending = booking_repo.find_pending_for_space("S1")
        assert len(pending) == 1

    def test_find_by_status(self, booking_repo):
        booking_repo.add(make_booking(id="B1"))
        b2 = make_booking(id="B2", space_id="S2")
        b2.confirm()
        booking_repo.add(b2)
        pending = booking_repo.find_by_status(BookingStatus.PENDING)
        assert len(pending) == 1


# ─── CheckIn Repository Specific Tests ─────────────────────────────────

class TestCheckInRepository:
    def test_find_by_tenant(self, check_in_repo):
        ci = CheckIn(id="CI1", tenant_id="T1", space_id="S1", contract_id="C1")
        check_in_repo.add(ci)
        results = check_in_repo.find_by_tenant("T1")
        assert len(results) == 1

    def test_find_by_space(self, check_in_repo):
        ci = CheckIn(id="CI1", tenant_id="T1", space_id="S1", contract_id="C1")
        check_in_repo.add(ci)
        results = check_in_repo.find_by_space("S1")
        assert len(results) == 1

    def test_find_active(self, check_in_repo):
        ci1 = CheckIn(id="CI1", tenant_id="T1", space_id="S1", contract_id="C1")
        ci2 = CheckIn(id="CI2", tenant_id="T2", space_id="S2", contract_id="C2")
        ci2.check_out()
        check_in_repo.add(ci1)
        check_in_repo.add(ci2)
        active = check_in_repo.find_active()
        assert len(active) == 1

    def test_find_by_contract(self, check_in_repo):
        ci = CheckIn(id="CI1", tenant_id="T1", space_id="S1", contract_id="C1")
        check_in_repo.add(ci)
        result = check_in_repo.find_by_contract("C1")
        assert result is not None

    def test_find_by_contract_none(self, check_in_repo):
        result = check_in_repo.find_by_contract("nope")
        assert result is None


# ─── Invoice Repository Specific Tests ─────────────────────────────────

class TestInvoiceRepository:
    def test_find_by_contract(self, invoice_repo):
        invoice_repo.add(make_invoice(id="I1", contract_id="C1"))
        results = invoice_repo.find_by_contract("C1")
        assert len(results) == 1

    def test_find_by_tenant(self, invoice_repo):
        invoice_repo.add(make_invoice(id="I1", tenant_id="T1"))
        results = invoice_repo.find_by_tenant("T1")
        assert len(results) == 1

    def test_find_overdue(self, invoice_repo):
        invoice_repo.add(make_invoice(id="I1", due_date=date(2024, 1, 1)))
        invoice_repo.add(make_invoice(id="I2", due_date=date(2030, 1, 1)))
        overdue = invoice_repo.find_overdue(date(2025, 6, 1))
        assert len(overdue) == 1

    def test_find_by_status(self, invoice_repo):
        inv = make_invoice(id="I1")
        inv.mark_paid()
        invoice_repo.add(inv)
        invoice_repo.add(make_invoice(id="I2"))
        paid = invoice_repo.find_by_status(InvoiceStatus.PAID)
        assert len(paid) == 1


# ─── Payment Repository Specific Tests ─────────────────────────────────

class TestPaymentRepository:
    def test_find_by_invoice(self, payment_repo):
        payment_repo.add(make_payment(id="P1", invoice_id="I1"))
        payment_repo.add(make_payment(id="P2", invoice_id="I2"))
        results = payment_repo.find_by_invoice("I1")
        assert len(results) == 1

    def test_find_by_invoice_empty(self, payment_repo):
        results = payment_repo.find_by_invoice("nope")
        assert len(results) == 0
