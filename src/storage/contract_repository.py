"""Contract repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.contract import Contract
from src.models.enums import ContractStatus
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class IContractRepository(IRepository[Contract]):
    """Interface for contract-specific repository operations."""

    @abstractmethod
    def find_by_tenant(self, tenant_id: str) -> list[Contract]:
        """Find all contracts for a given tenant."""

    @abstractmethod
    def find_by_space(self, space_id: str) -> list[Contract]:
        """Find all contracts for a given space."""

    @abstractmethod
    def find_active(self) -> list[Contract]:
        """Find all active contracts."""

    @abstractmethod
    def find_by_status(self, status: ContractStatus) -> list[Contract]:
        """Find contracts by status."""

    @abstractmethod
    def find_active_for_space(self, space_id: str) -> Contract | None:
        """Find the active contract for a specific space."""


class InMemoryContractRepository(InMemoryBaseRepository[Contract], IContractRepository):
    """In-memory implementation of the contract repository."""

    def __init__(self) -> None:
        """Initialize the contract repository."""
        super().__init__(entity_name="Contract")

    def find_by_tenant(self, tenant_id: str) -> list[Contract]:
        """Find all contracts for a given tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of contracts for the tenant.
        """
        return self.find_by(lambda c: c.tenant_id == tenant_id)

    def find_by_space(self, space_id: str) -> list[Contract]:
        """Find all contracts for a given space.

        Args:
            space_id: ID of the space.

        Returns:
            List of contracts for the space.
        """
        return self.find_by(lambda c: c.space_id == space_id)

    def find_active(self) -> list[Contract]:
        """Find all active contracts.

        Returns:
            List of active contracts.
        """
        return self.find_by(lambda c: c.status == ContractStatus.ACTIVE)

    def find_by_status(self, status: ContractStatus) -> list[Contract]:
        """Find contracts by status.

        Args:
            status: Contract status to filter by.

        Returns:
            List of contracts with the specified status.
        """
        return self.find_by(lambda c: c.status == status)

    def find_active_for_space(self, space_id: str) -> Contract | None:
        """Find the active contract for a specific space.

        Args:
            space_id: ID of the space.

        Returns:
            Active contract for the space, or None.
        """
        results = self.find_by(
            lambda c: c.space_id == space_id and c.status == ContractStatus.ACTIVE
        )
        return results[0] if results else None
