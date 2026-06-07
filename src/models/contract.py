"""Contract domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from src.models.enums import ContractStatus


@dataclass
class Contract:
    """Represents a rental contract between a tenant and a space.

    Attributes:
        id: Unique identifier for the contract.
        tenant_id: ID of the tenant party.
        space_id: ID of the rented space.
        start_date: Contract start date.
        end_date: Contract end date.
        monthly_rate: Monthly rental rate agreed upon.
        deposit: Security deposit amount.
        status: Current contract lifecycle status.
        created_at: Timestamp when the contract was created.
    """

    id: str
    tenant_id: str
    space_id: str
    start_date: date
    end_date: date
    monthly_rate: float
    deposit: float = 0.0
    status: ContractStatus = ContractStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)

    def is_active(self) -> bool:
        """Check if the contract is currently active."""
        return self.status == ContractStatus.ACTIVE

    def is_draft(self) -> bool:
        """Check if the contract is still in draft status."""
        return self.status == ContractStatus.DRAFT

    def duration_months(self) -> int:
        """Calculate the contract duration in months.

        Returns:
            Number of months between start and end dates.
        """
        return (self.end_date.year - self.start_date.year) * 12 + (
            self.end_date.month - self.start_date.month
        )

    def activate(self) -> None:
        """Activate a draft contract."""
        self.status = ContractStatus.ACTIVE

    def terminate(self) -> None:
        """Terminate an active contract early."""
        self.status = ContractStatus.TERMINATED

    def expire(self) -> None:
        """Mark the contract as expired."""
        self.status = ContractStatus.EXPIRED

    def cancel(self) -> None:
        """Cancel a draft contract."""
        self.status = ContractStatus.CANCELLED

    def is_expired(self, current_date: date | None = None) -> bool:
        """Check if the contract has passed its end date.

        Args:
            current_date: Date to check against. Defaults to today.

        Returns:
            True if the contract end date has passed.
        """
        check_date = current_date or date.today()
        return check_date > self.end_date
