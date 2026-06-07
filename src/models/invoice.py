"""Invoice domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from src.models.enums import InvoiceStatus, InvoiceType


@dataclass
class Invoice:
    """Represents a financial invoice for rental charges.

    The total_amount is computed as base_amount + penalty_amount.

    Attributes:
        id: Unique identifier for the invoice.
        contract_id: ID of the associated contract.
        tenant_id: ID of the tenant being billed.
        base_amount: Base rental charge amount.
        penalty_amount: Accumulated penalty charges.
        issue_date: Date the invoice was issued.
        due_date: Payment deadline date.
        status: Current payment status.
        type: Invoice type (regular, penalty, deposit, etc.).
        created_at: Timestamp when the invoice was created.
    """

    id: str
    contract_id: str
    tenant_id: str
    base_amount: float
    issue_date: date
    due_date: date
    penalty_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.PENDING
    type: InvoiceType = InvoiceType.REGULAR
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_amount(self) -> float:
        """Calculate the total invoice amount including penalties."""
        return self.base_amount + self.penalty_amount

    def mark_paid(self) -> None:
        """Mark the invoice as paid."""
        self.status = InvoiceStatus.PAID

    def mark_overdue(self) -> None:
        """Mark the invoice as overdue."""
        self.status = InvoiceStatus.OVERDUE

    def cancel(self) -> None:
        """Cancel the invoice."""
        self.status = InvoiceStatus.CANCELLED

    def is_overdue(self, current_date: date | None = None) -> bool:
        """Check if the invoice is past its due date and unpaid.

        Args:
            current_date: Date to check against. Defaults to today.

        Returns:
            True if the invoice is pending and past due.
        """
        check_date = current_date or date.today()
        return self.status == InvoiceStatus.PENDING and check_date > self.due_date

    def is_paid(self) -> bool:
        """Check if the invoice has been paid."""
        return self.status == InvoiceStatus.PAID

    def add_penalty(self, amount: float) -> None:
        """Add a penalty amount to the invoice.

        Args:
            amount: Penalty amount to add (must be positive).
        """
        if amount > 0:
            self.penalty_amount += amount

    def days_overdue(self, current_date: date | None = None) -> int:
        """Calculate the number of days the invoice is overdue.

        Args:
            current_date: Date to check against. Defaults to today.

        Returns:
            Number of days overdue, or 0 if not overdue.
        """
        check_date = current_date or date.today()
        if check_date > self.due_date and self.status in (InvoiceStatus.PENDING, InvoiceStatus.OVERDUE):
            return (check_date - self.due_date).days
        return 0
