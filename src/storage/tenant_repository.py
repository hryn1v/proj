"""Tenant repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.enums import TenantStatus
from src.models.tenant import Tenant
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class ITenantRepository(IRepository[Tenant]):
    """Interface for tenant-specific repository operations."""

    @abstractmethod
    def find_by_email(self, email: str) -> Tenant | None:
        """Find a tenant by email address.

        Args:
            email: Email address to search for.

        Returns:
            The tenant if found, None otherwise.
        """

    @abstractmethod
    def find_by_status(self, status: TenantStatus) -> list[Tenant]:
        """Find all tenants with a given status.

        Args:
            status: Tenant status to filter by.

        Returns:
            List of tenants with the specified status.
        """

    @abstractmethod
    def find_active(self) -> list[Tenant]:
        """Find all active tenants.

        Returns:
            List of active tenants.
        """


class InMemoryTenantRepository(InMemoryBaseRepository[Tenant], ITenantRepository):
    """In-memory implementation of the tenant repository."""

    def __init__(self) -> None:
        """Initialize the tenant repository."""
        super().__init__(entity_name="Tenant")

    def find_by_email(self, email: str) -> Tenant | None:
        """Find a tenant by email address.

        Args:
            email: Email address to search for.

        Returns:
            The tenant if found, None otherwise.
        """
        results = self.find_by(lambda t: t.email == email)
        return results[0] if results else None

    def find_by_status(self, status: TenantStatus) -> list[Tenant]:
        """Find all tenants with a given status.

        Args:
            status: Tenant status to filter by.

        Returns:
            List of tenants with the specified status.
        """
        return self.find_by(lambda t: t.status == status)

    def find_active(self) -> list[Tenant]:
        """Find all active tenants.

        Returns:
            List of active tenants.
        """
        return self.find_by_status(TenantStatus.ACTIVE)
