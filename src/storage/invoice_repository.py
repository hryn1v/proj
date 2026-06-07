"""Invoice repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod
from datetime import date

from src.models.enums import InvoiceStatus
from src.models.invoice import Invoice
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class IInvoiceRepository(IRepository[Invoice]):
    """Interface for invoice-specific repository operations."""

    @abstractmethod
    def find_by_contract(self, contract_id: str) -> list[Invoice]:
        """Find all invoices for a given contract."""

    @abstractmethod
    def find_by_tenant(self, tenant_id: str) -> list[Invoice]:
        """Find all invoices for a given tenant."""

    @abstractmethod
    def find_overdue(self, current_date: date) -> list[Invoice]:
        """Find all overdue invoices as of the given date."""

    @abstractmethod
    def find_by_status(self, status: InvoiceStatus) -> list[Invoice]:
        """Find invoices by status."""


class InMemoryInvoiceRepository(InMemoryBaseRepository[Invoice], IInvoiceRepository):
    """In-memory implementation of the invoice repository."""

    def __init__(self) -> None:
        """Initialize the invoice repository."""
        super().__init__(entity_name="Invoice")

    def find_by_contract(self, contract_id: str) -> list[Invoice]:
        """Find all invoices for a given contract.

        Args:
            contract_id: ID of the contract.

        Returns:
            List of invoices for the contract.
        """
        return self.find_by(lambda i: i.contract_id == contract_id)

    def find_by_tenant(self, tenant_id: str) -> list[Invoice]:
        """Find all invoices for a given tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of invoices for the tenant.
        """
        return self.find_by(lambda i: i.tenant_id == tenant_id)

    def find_overdue(self, current_date: date) -> list[Invoice]:
        """Find all overdue invoices as of the given date.

        Args:
            current_date: Date to check against.

        Returns:
            List of overdue invoices.
        """
        return self.find_by(lambda i: i.is_overdue(current_date))

    def find_by_status(self, status: InvoiceStatus) -> list[Invoice]:
        """Find invoices by status.

        Args:
            status: Invoice status to filter by.

        Returns:
            List of invoices with the specified status.
        """
        return self.find_by(lambda i: i.status == status)
