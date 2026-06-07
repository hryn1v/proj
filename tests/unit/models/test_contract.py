"""Unit tests for the Contract model."""
import pytest
from datetime import date
from src.models.contract import Contract
from src.models.enums import ContractStatus
from tests.conftest import make_contract


class TestContractCreation:
    def test_create_contract_with_defaults(self):
        contract = make_contract()
        assert contract.status == ContractStatus.DRAFT
        assert contract.monthly_rate == 1000.0
        assert contract.deposit == 2000.0

    def test_contract_created_at_is_set(self):
        contract = make_contract()
        assert contract.created_at is not None


class TestContractStatus:
    def test_is_draft(self):
        contract = make_contract()
        assert contract.is_draft() is True
        assert contract.is_active() is False

    def test_activate(self):
        contract = make_contract()
        contract.activate()
        assert contract.is_active() is True
        assert contract.is_draft() is False

    def test_terminate(self):
        contract = make_contract(status=ContractStatus.ACTIVE)
        contract.terminate()
        assert contract.status == ContractStatus.TERMINATED

    def test_expire(self):
        contract = make_contract(status=ContractStatus.ACTIVE)
        contract.expire()
        assert contract.status == ContractStatus.EXPIRED

    def test_cancel(self):
        contract = make_contract()
        contract.cancel()
        assert contract.status == ContractStatus.CANCELLED


class TestContractDuration:
    def test_duration_months_one_year(self):
        contract = make_contract(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        assert contract.duration_months() == 12

    def test_duration_months_six_months(self):
        contract = make_contract(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        assert contract.duration_months() == 6

    def test_duration_months_zero(self):
        contract = make_contract(
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
        )
        assert contract.duration_months() == 0


class TestContractExpiry:
    def test_is_expired_past_end_date(self):
        contract = make_contract(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
        )
        assert contract.is_expired(date(2025, 1, 1)) is True

    def test_is_not_expired_before_end_date(self):
        contract = make_contract(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        assert contract.is_expired(date(2025, 6, 1)) is False

    def test_is_not_expired_on_end_date(self):
        contract = make_contract(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        assert contract.is_expired(date(2025, 12, 31)) is False
