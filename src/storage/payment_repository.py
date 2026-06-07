"""Payment repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.payment import Payment
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class IPaymentRepository(IRepository[Payment]):
    """Interface for payment-specific repository operations."""

    @abstractmethod
    def find_by_invoice(self, invoice_id: str) -> list[Payment]:
        """Find all payments for a given invoice."""


class InMemoryPaymentRepository(InMemoryBaseRepository[Payment], IPaymentRepository):
    """In-memory implementation of the payment repository."""

    def __init__(self) -> None:
        """Initialize the payment repository."""
        super().__init__(entity_name="Payment")

    def find_by_invoice(self, invoice_id: str) -> list[Payment]:
        """Find all payments for a given invoice.

        Args:
            invoice_id: ID of the invoice.

        Returns:
            List of payments for the invoice.
        """
        return self.find_by(lambda p: p.invoice_id == invoice_id)
