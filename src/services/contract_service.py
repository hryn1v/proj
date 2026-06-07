"""Contract management service."""
from __future__ import annotations

from datetime import date

from src.models.contract import Contract
from src.models.enums import ContractStatus
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.contract_repository import IContractRepository
from src.utils.exceptions import (
    ContractNotActiveError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    SpaceNotAvailableError,
    ValidationError,
)
from src.utils.id_generator import generate_prefixed_id
from src.utils.validators import validate_date_range, validate_positive_amount


class ContractService:
    """Service for managing rental contract lifecycle.

    Handles contract creation, activation, termination, expiration,
    and coordinates with tenant and space services for validation.

    Attributes:
        _contract_repo: Repository for contract persistence.
        _tenant_service: Service for tenant validation.
        _space_service: Service for space validation.
    """

    def __init__(
        self,
        contract_repo: IContractRepository,
        tenant_service: TenantService,
        space_service: SpaceService,
    ) -> None:
        """Initialize with required repositories and services.

        Args:
            contract_repo: Repository implementing IContractRepository.
            tenant_service: Service for tenant operations.
            space_service: Service for space operations.
        """
        self._contract_repo = contract_repo
        self._tenant_service = tenant_service
        self._space_service = space_service

    def create_contract(
        self,
        tenant_id: str,
        space_id: str,
        start_date: date,
        end_date: date,
        monthly_rate: float,
        deposit: float = 0.0,
    ) -> Contract:
        """Create a new rental contract in draft status.

        Args:
            tenant_id: ID of the tenant.
            space_id: ID of the space.
            start_date: Contract start date.
            end_date: Contract end date.
            monthly_rate: Monthly rental rate.
            deposit: Security deposit amount.

        Returns:
            The newly created draft contract.

        Raises:
            EntityNotFoundError: If tenant or space not found.
            TenantBlockedError: If tenant is blocked.
            ValidationError: If input is invalid.
        """
        self._tenant_service.ensure_tenant_active(tenant_id)
        self._space_service.get_space(space_id)

        if not validate_date_range(start_date, end_date):
            raise ValidationError("date_range", "Start date must be before end date")
        if not validate_positive_amount(monthly_rate):
            raise ValidationError("monthly_rate", "Monthly rate must be positive")

        # Check for existing active contract on the space
        existing = self._contract_repo.find_active_for_space(space_id)
        if existing:
            raise SpaceNotAvailableError(space_id)

        contract = Contract(
            id=generate_prefixed_id("CTR"),
            tenant_id=tenant_id,
            space_id=space_id,
            start_date=start_date,
            end_date=end_date,
            monthly_rate=monthly_rate,
            deposit=deposit,
        )
        return self._contract_repo.add(contract)

    def activate_contract(self, contract_id: str) -> Contract:
        """Activate a draft contract and occupy the space.

        Args:
            contract_id: ID of the contract to activate.

        Returns:
            The activated contract.

        Raises:
            EntityNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract is not in draft status.
        """
        contract = self.get_contract(contract_id)
        if not contract.is_draft():
            raise InvalidStateTransitionError(
                "Contract", contract.status.value, ContractStatus.ACTIVE.value
            )

        contract.activate()
        self._space_service.occupy_space(contract.space_id)
        return self._contract_repo.update(contract)

    def terminate_contract(self, contract_id: str) -> Contract:
        """Terminate an active contract early and release the space.

        Args:
            contract_id: ID of the contract to terminate.

        Returns:
            The terminated contract.

        Raises:
            EntityNotFoundError: If contract not found.
            ContractNotActiveError: If contract is not active.
        """
        contract = self.get_contract(contract_id)
        if not contract.is_active():
            raise ContractNotActiveError(contract_id)

        contract.terminate()
        self._space_service.release_space(contract.space_id)
        return self._contract_repo.update(contract)

    def expire_contract(self, contract_id: str) -> Contract:
        """Mark a contract as expired and release the space.

        Args:
            contract_id: ID of the contract to expire.

        Returns:
            The expired contract.

        Raises:
            EntityNotFoundError: If contract not found.
            ContractNotActiveError: If contract is not active.
        """
        contract = self.get_contract(contract_id)
        if not contract.is_active():
            raise ContractNotActiveError(contract_id)

        contract.expire()
        self._space_service.release_space(contract.space_id)
        return self._contract_repo.update(contract)

    def cancel_contract(self, contract_id: str) -> Contract:
        """Cancel a draft contract.

        Args:
            contract_id: ID of the contract to cancel.

        Returns:
            The cancelled contract.

        Raises:
            EntityNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract is not in draft status.
        """
        contract = self.get_contract(contract_id)
        if not contract.is_draft():
            raise InvalidStateTransitionError(
                "Contract", contract.status.value, ContractStatus.CANCELLED.value
            )

        contract.cancel()
        return self._contract_repo.update(contract)

    def get_contract(self, contract_id: str) -> Contract:
        """Retrieve a contract by ID.

        Args:
            contract_id: Unique identifier of the contract.

        Returns:
            The contract.

        Raises:
            EntityNotFoundError: If the contract does not exist.
        """
        contract = self._contract_repo.get_by_id(contract_id)
        if contract is None:
            raise EntityNotFoundError("Contract", contract_id)
        return contract

    def get_contracts_by_tenant(self, tenant_id: str) -> list[Contract]:
        """Get all contracts for a tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of contracts.
        """
        return self._contract_repo.find_by_tenant(tenant_id)

    def get_active_contracts(self) -> list[Contract]:
        """Get all active contracts.

        Returns:
            List of active contracts.
        """
        return self._contract_repo.find_active()

    def get_contracts_by_space(self, space_id: str) -> list[Contract]:
        """Get all contracts for a space.

        Args:
            space_id: ID of the space.

        Returns:
            List of contracts.
        """
        return self._contract_repo.find_by_space(space_id)

    def check_and_expire_contracts(self, current_date: date) -> list[Contract]:
        """Check all active contracts and expire those past their end date.

        Args:
            current_date: Current date to check against.

        Returns:
            List of newly expired contracts.
        """
        expired = []
        for contract in self._contract_repo.find_active():
            if contract.is_expired(current_date):
                contract.expire()
                self._space_service.release_space(contract.space_id)
                self._contract_repo.update(contract)
                expired.append(contract)
        return expired
