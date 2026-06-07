"""Invoice creation factories using the Factory Method Pattern (GoF).

Provides specialized factories for creating different types of invoices:
- RegularInvoiceFactory: Monthly rent invoices
- PenaltyInvoiceFactory: Overdue penalty invoices
- DepositInvoiceFactory: Security deposit invoices
- FinalSettlementFactory: Check-out settlement invoices
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.models.contract import Contract
from src.models.enums import InvoiceType
from src.models.invoice import Invoice
from src.utils.date_helpers import add_days
from src.utils.id_generator import generate_prefixed_id


class InvoiceFactory(ABC):
    """Abstract factory for creating invoices.

    Implements the Factory Method pattern to encapsulate
    invoice creation logic for different invoice types.
    """

    @abstractmethod
    def create_invoice(
        self,
        contract: Contract,
        issue_date: date,
        amount: float | None = None,
    ) -> Invoice:
        """Create an invoice for the given contract.

        Args:
            contract: The contract to generate the invoice for.
            issue_date: Date of invoice issuance.
            amount: Optional override for the invoice amount.

        Returns:
            A new Invoice instance.
        """


class RegularInvoiceFactory(InvoiceFactory):
    """Factory for creating regular monthly rent invoices.

    Uses the contract's monthly rate as the base amount and
    sets the due date 30 days from the issue date.
    """

    def __init__(self, payment_terms_days: int = 30) -> None:
        """Initialize with payment terms.

        Args:
            payment_terms_days: Number of days until payment is due. Defaults to 30.
        """
        self._payment_terms_days = payment_terms_days

    def create_invoice(
        self,
        contract: Contract,
        issue_date: date,
        amount: float | None = None,
    ) -> Invoice:
        """Create a regular monthly invoice.

        Args:
            contract: The associated contract.
            issue_date: Date of invoice issuance.
            amount: Optional amount override. Defaults to monthly rate.

        Returns:
            A new regular Invoice.
        """
        return Invoice(
            id=generate_prefixed_id("INV"),
            contract_id=contract.id,
            tenant_id=contract.tenant_id,
            base_amount=amount or contract.monthly_rate,
            issue_date=issue_date,
            due_date=add_days(issue_date, self._payment_terms_days),
            type=InvoiceType.REGULAR,
        )


class PenaltyInvoiceFactory(InvoiceFactory):
    """Factory for creating penalty invoices for overdue payments.

    Creates an invoice with a short payment term (7 days)
    to encourage prompt payment of penalties.
    """

    def __init__(self, payment_terms_days: int = 7) -> None:
        """Initialize with payment terms.

        Args:
            payment_terms_days: Days until penalty payment is due. Defaults to 7.
        """
        self._payment_terms_days = payment_terms_days

    def create_invoice(
        self,
        contract: Contract,
        issue_date: date,
        amount: float | None = None,
    ) -> Invoice:
        """Create a penalty invoice.

        Args:
            contract: The associated contract.
            issue_date: Date of invoice issuance.
            amount: Penalty amount. Must be provided.

        Returns:
            A new penalty Invoice.

        Raises:
            ValueError: If amount is not provided.
        """
        if amount is None or amount <= 0:
            raise ValueError("Penalty invoice requires a positive amount")
        return Invoice(
            id=generate_prefixed_id("PEN"),
            contract_id=contract.id,
            tenant_id=contract.tenant_id,
            base_amount=amount,
            issue_date=issue_date,
            due_date=add_days(issue_date, self._payment_terms_days),
            type=InvoiceType.PENALTY,
        )


class DepositInvoiceFactory(InvoiceFactory):
    """Factory for creating security deposit invoices.

    Uses the contract's deposit amount with immediate payment terms.
    """

    def __init__(self, payment_terms_days: int = 7) -> None:
        """Initialize with payment terms.

        Args:
            payment_terms_days: Days until deposit is due. Defaults to 7.
        """
        self._payment_terms_days = payment_terms_days

    def create_invoice(
        self,
        contract: Contract,
        issue_date: date,
        amount: float | None = None,
    ) -> Invoice:
        """Create a deposit invoice.

        Args:
            contract: The associated contract.
            issue_date: Date of invoice issuance.
            amount: Optional amount override. Defaults to contract deposit.

        Returns:
            A new deposit Invoice.
        """
        return Invoice(
            id=generate_prefixed_id("DEP"),
            contract_id=contract.id,
            tenant_id=contract.tenant_id,
            base_amount=amount or contract.deposit,
            issue_date=issue_date,
            due_date=add_days(issue_date, self._payment_terms_days),
            type=InvoiceType.DEPOSIT,
        )


class FinalSettlementFactory(InvoiceFactory):
    """Factory for creating final settlement invoices at check-out.

    Calculates remaining charges and creates a settlement invoice
    with a 14-day payment term.
    """

    def __init__(self, payment_terms_days: int = 14) -> None:
        """Initialize with payment terms.

        Args:
            payment_terms_days: Days until settlement is due. Defaults to 14.
        """
        self._payment_terms_days = payment_terms_days

    def create_invoice(
        self,
        contract: Contract,
        issue_date: date,
        amount: float | None = None,
    ) -> Invoice:
        """Create a final settlement invoice.

        Args:
            contract: The associated contract.
            issue_date: Date of invoice issuance.
            amount: Settlement amount. Must be provided.

        Returns:
            A new final settlement Invoice.

        Raises:
            ValueError: If amount is not provided.
        """
        if amount is None or amount <= 0:
            raise ValueError("Final settlement invoice requires a positive amount")
        return Invoice(
            id=generate_prefixed_id("SET"),
            contract_id=contract.id,
            tenant_id=contract.tenant_id,
            base_amount=amount,
            issue_date=issue_date,
            due_date=add_days(issue_date, self._payment_terms_days),
            type=InvoiceType.FINAL_SETTLEMENT,
        )
