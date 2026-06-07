"""CheckIn repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.check_in import CheckIn
from src.models.enums import CheckInStatus
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class ICheckInRepository(IRepository[CheckIn]):
    """Interface for check-in-specific repository operations."""

    @abstractmethod
    def find_by_tenant(self, tenant_id: str) -> list[CheckIn]:
        """Find all check-in records for a given tenant."""

    @abstractmethod
    def find_by_space(self, space_id: str) -> list[CheckIn]:
        """Find all check-in records for a given space."""

    @abstractmethod
    def find_active(self) -> list[CheckIn]:
        """Find all currently active check-ins."""

    @abstractmethod
    def find_by_contract(self, contract_id: str) -> CheckIn | None:
        """Find the check-in record for a specific contract."""


class InMemoryCheckInRepository(InMemoryBaseRepository[CheckIn], ICheckInRepository):
    """In-memory implementation of the check-in repository."""

    def __init__(self) -> None:
        """Initialize the check-in repository."""
        super().__init__(entity_name="CheckIn")

    def find_by_tenant(self, tenant_id: str) -> list[CheckIn]:
        """Find all check-in records for a given tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of check-in records.
        """
        return self.find_by(lambda ci: ci.tenant_id == tenant_id)

    def find_by_space(self, space_id: str) -> list[CheckIn]:
        """Find all check-in records for a given space.

        Args:
            space_id: ID of the space.

        Returns:
            List of check-in records.
        """
        return self.find_by(lambda ci: ci.space_id == space_id)

    def find_active(self) -> list[CheckIn]:
        """Find all currently active check-ins.

        Returns:
            List of active check-in records.
        """
        return self.find_by(lambda ci: ci.status == CheckInStatus.CHECKED_IN)

    def find_by_contract(self, contract_id: str) -> CheckIn | None:
        """Find the check-in record for a specific contract.

        Args:
            contract_id: ID of the contract.

        Returns:
            Check-in record or None.
        """
        results = self.find_by(lambda ci: ci.contract_id == contract_id)
        return results[0] if results else None
