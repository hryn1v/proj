"""Check-in/check-out management service."""
from __future__ import annotations

from src.models.check_in import CheckIn
from src.services.contract_service import ContractService
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.check_in_repository import ICheckInRepository
from src.utils.exceptions import (
    BusinessRuleViolationError,
    ContractNotActiveError,
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from src.utils.id_generator import generate_prefixed_id


class CheckInService:
    """Service for managing tenant check-in and check-out operations.

    Coordinates between tenant, space, and contract services to ensure
    all business rules are met before recording occupancy.

    Attributes:
        _check_in_repo: Repository for check-in record persistence.
        _tenant_service: Service for tenant validation.
        _space_service: Service for space operations.
        _contract_service: Service for contract validation.
    """

    def __init__(
        self,
        check_in_repo: ICheckInRepository,
        tenant_service: TenantService,
        space_service: SpaceService,
        contract_service: ContractService,
    ) -> None:
        """Initialize with required repositories and services.

        Args:
            check_in_repo: Repository implementing ICheckInRepository.
            tenant_service: Service for tenant operations.
            space_service: Service for space operations.
            contract_service: Service for contract operations.
        """
        self._check_in_repo = check_in_repo
        self._tenant_service = tenant_service
        self._space_service = space_service
        self._contract_service = contract_service

    def check_in(self, tenant_id: str, space_id: str, contract_id: str) -> CheckIn:
        """Record a tenant checking in to a space.

        Args:
            tenant_id: ID of the tenant checking in.
            space_id: ID of the space.
            contract_id: ID of the associated contract.

        Returns:
            The new check-in record.

        Raises:
            EntityNotFoundError: If tenant, space, or contract not found.
            TenantBlockedError: If tenant is blocked.
            ContractNotActiveError: If contract is not active.
            BusinessRuleViolationError: If tenant already checked in to this contract.
        """
        self._tenant_service.ensure_tenant_active(tenant_id)
        self._space_service.get_space(space_id)

        contract = self._contract_service.get_contract(contract_id)
        if not contract.is_active():
            raise ContractNotActiveError(contract_id)

        if contract.tenant_id != tenant_id:
            raise BusinessRuleViolationError(
                f"Contract '{contract_id}' does not belong to tenant '{tenant_id}'"
            )

        if contract.space_id != space_id:
            raise BusinessRuleViolationError(
                f"Contract '{contract_id}' is not for space '{space_id}'"
            )

        # Check for existing active check-in for this contract
        existing = self._check_in_repo.find_by_contract(contract_id)
        if existing and existing.is_active():
            raise BusinessRuleViolationError(
                f"Tenant '{tenant_id}' is already checked in under contract '{contract_id}'"
            )

        check_in = CheckIn(
            id=generate_prefixed_id("CHK"),
            tenant_id=tenant_id,
            space_id=space_id,
            contract_id=contract_id,
        )
        return self._check_in_repo.add(check_in)

    def check_out(self, check_in_id: str) -> CheckIn:
        """Record a tenant checking out of a space.

        Args:
            check_in_id: ID of the check-in record.

        Returns:
            The updated check-in record with check-out timestamp.

        Raises:
            EntityNotFoundError: If check-in not found.
            InvalidStateTransitionError: If already checked out.
        """
        check_in = self.get_check_in(check_in_id)
        if not check_in.is_active():
            raise InvalidStateTransitionError(
                "CheckIn", check_in.status.value, "checked_out"
            )

        check_in.check_out()
        return self._check_in_repo.update(check_in)

    def get_check_in(self, check_in_id: str) -> CheckIn:
        """Retrieve a check-in record by ID.

        Args:
            check_in_id: Unique identifier.

        Returns:
            The check-in record.

        Raises:
            EntityNotFoundError: If not found.
        """
        check_in = self._check_in_repo.get_by_id(check_in_id)
        if check_in is None:
            raise EntityNotFoundError("CheckIn", check_in_id)
        return check_in

    def get_active_check_ins(self) -> list[CheckIn]:
        """Get all active check-ins.

        Returns:
            List of active check-in records.
        """
        return self._check_in_repo.find_active()

    def get_check_ins_by_tenant(self, tenant_id: str) -> list[CheckIn]:
        """Get all check-in records for a tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of check-in records.
        """
        return self._check_in_repo.find_by_tenant(tenant_id)

    def get_check_in_by_contract(self, contract_id: str) -> CheckIn | None:
        """Get the check-in record for a contract.

        Args:
            contract_id: ID of the contract.

        Returns:
            Check-in record or None.
        """
        return self._check_in_repo.find_by_contract(contract_id)

    def get_check_ins_by_space(self, space_id: str) -> list[CheckIn]:
        """Get all check-in records for a space.

        Args:
            space_id: ID of the space.

        Returns:
            List of check-in records.
        """
        return self._check_in_repo.find_by_space(space_id)
