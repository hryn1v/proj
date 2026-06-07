"""Unit tests for ContractService."""
from datetime import date, timedelta

import pytest

from src.models.enums import ContractStatus, SpaceType
from src.utils.exceptions import (
    ContractNotActiveError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    SpaceNotAvailableError,
    TenantBlockedError,
    ValidationError,
)


class TestCreateContract:
    def _setup(self, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        return t, s

    def test_create_valid_contract(self, contract_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0, 2000.0
        )
        assert c.status == ContractStatus.DRAFT
        assert c.id.startswith("CTR-")

    def test_create_with_blocked_tenant_raises(self, contract_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            contract_service.create_contract(
                t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
            )

    def test_create_invalid_dates_raises(self, contract_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        with pytest.raises(ValidationError):
            contract_service.create_contract(
                t.id, s.id, date.today(), date.today() - timedelta(days=1), 1000.0
            )

    def test_create_zero_rate_raises(self, contract_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        with pytest.raises(ValidationError):
            contract_service.create_contract(
                t.id, s.id, date.today(), date.today() + timedelta(days=30), 0
            )

    def test_create_with_active_contract_on_space_raises(self, contract_service, tenant_service, space_service):
        t, s = self._setup(tenant_service, space_service)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        contract_service.activate_contract(c.id)
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        with pytest.raises(SpaceNotAvailableError):
            contract_service.create_contract(
                t2.id, s.id, date.today(), date.today() + timedelta(days=30), 500.0
            )


class TestContractLifecycle:
    def _setup_active(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=365), 1000.0
        )
        return t, s, c

    def test_activate_draft(self, contract_service, tenant_service, space_service):
        _, s, c = self._setup_active(contract_service, tenant_service, space_service)
        activated = contract_service.activate_contract(c.id)
        assert activated.is_active()
        space = space_service.get_space(s.id)
        assert space.status.value == "occupied"

    def test_activate_non_draft_raises(self, contract_service, tenant_service, space_service):
        _, _, c = self._setup_active(contract_service, tenant_service, space_service)
        contract_service.activate_contract(c.id)
        with pytest.raises(InvalidStateTransitionError):
            contract_service.activate_contract(c.id)

    def test_terminate_active(self, contract_service, tenant_service, space_service):
        _, s, c = self._setup_active(contract_service, tenant_service, space_service)
        contract_service.activate_contract(c.id)
        terminated = contract_service.terminate_contract(c.id)
        assert terminated.status == ContractStatus.TERMINATED
        space = space_service.get_space(s.id)
        assert space.is_available()

    def test_terminate_non_active_raises(self, contract_service, tenant_service, space_service):
        _, _, c = self._setup_active(contract_service, tenant_service, space_service)
        with pytest.raises(ContractNotActiveError):
            contract_service.terminate_contract(c.id)

    def test_expire_active(self, contract_service, tenant_service, space_service):
        _, _, c = self._setup_active(contract_service, tenant_service, space_service)
        contract_service.activate_contract(c.id)
        expired = contract_service.expire_contract(c.id)
        assert expired.status == ContractStatus.EXPIRED

    def test_cancel_draft(self, contract_service, tenant_service, space_service):
        _, _, c = self._setup_active(contract_service, tenant_service, space_service)
        cancelled = contract_service.cancel_contract(c.id)
        assert cancelled.status == ContractStatus.CANCELLED

    def test_cancel_non_draft_raises(self, contract_service, tenant_service, space_service):
        _, _, c = self._setup_active(contract_service, tenant_service, space_service)
        contract_service.activate_contract(c.id)
        with pytest.raises(InvalidStateTransitionError):
            contract_service.cancel_contract(c.id)


class TestContractQueries:
    def test_get_contract(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
        )
        fetched = contract_service.get_contract(c.id)
        assert fetched.id == c.id

    def test_get_nonexistent_raises(self, contract_service):
        with pytest.raises(EntityNotFoundError):
            contract_service.get_contract("nope")

    def test_get_contracts_by_tenant(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
        )
        contracts = contract_service.get_contracts_by_tenant(t.id)
        assert len(contracts) == 1

    def test_get_active_contracts(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date.today(), date.today() + timedelta(days=30), 1000.0
        )
        contract_service.activate_contract(c.id)
        active = contract_service.get_active_contracts()
        assert len(active) == 1

    def test_check_and_expire_contracts(self, contract_service, tenant_service, space_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        c = contract_service.create_contract(
            t.id, s.id, date(2024, 1, 1), date(2024, 6, 1), 1000.0
        )
        contract_service.activate_contract(c.id)
        expired = contract_service.check_and_expire_contracts(date(2025, 1, 1))
        assert len(expired) == 1
        assert expired[0].status == ContractStatus.EXPIRED
