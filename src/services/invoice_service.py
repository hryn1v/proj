"""Invoice management service."""
from __future__ import annotations

from datetime import date

from src.models.invoice import Invoice
from src.services.contract_service import ContractService
from src.services.invoice_factory import (
    DepositInvoiceFactory,
    FinalSettlementFactory,
    InvoiceFactory,
    PenaltyInvoiceFactory,
    RegularInvoiceFactory,
)
from src.services.penalty_strategy import PenaltyStrategy, PercentagePenalty
from src.services.tenant_service import TenantService
from src.storage.invoice_repository import IInvoiceRepository
from src.utils.exceptions import (
    ContractNotActiveError,
    EntityNotFoundError,
    InvoiceAlreadyPaidError,
)


class InvoiceService:
    """Service for managing invoices with Strategy-based penalty calculation.

    Coordinates invoice creation via Factory Method, penalty calculation
    via Strategy pattern, and overdue detection.

    Attributes:
        _invoice_repo: Repository for invoice persistence.
        _contract_service: Service for contract validation.
        _tenant_service: Service for tenant operations.
        _penalty_strategy: Strategy for penalty calculation.
        _regular_factory: Factory for regular invoices.
        _penalty_factory: Factory for penalty invoices.
        _deposit_factory: Factory for deposit invoices.
        _settlement_factory: Factory for final settlement invoices.
    """

    def __init__(
        self,
        invoice_repo: IInvoiceRepository,
        contract_service: ContractService,
        tenant_service: TenantService,
        penalty_strategy: PenaltyStrategy | None = None,
    ) -> None:
        """Initialize with required services and optional penalty strategy.

        Args:
            invoice_repo: Repository implementing IInvoiceRepository.
            contract_service: Service for contract operations.
            tenant_service: Service for tenant operations.
            penalty_strategy: Strategy for penalty calculation. Defaults to PercentagePenalty.
        """
        self._invoice_repo = invoice_repo
        self._contract_service = contract_service
        self._tenant_service = tenant_service
        self._penalty_strategy = penalty_strategy or PercentagePenalty()

        # Factories (Factory Method pattern)
        self._regular_factory: InvoiceFactory = RegularInvoiceFactory()
        self._penalty_factory: InvoiceFactory = PenaltyInvoiceFactory()
        self._deposit_factory: InvoiceFactory = DepositInvoiceFactory()
        self._settlement_factory: InvoiceFactory = FinalSettlementFactory()

    @property
    def penalty_strategy(self) -> PenaltyStrategy:
        """Get the current penalty calculation strategy."""
        return self._penalty_strategy

    @penalty_strategy.setter
    def penalty_strategy(self, strategy: PenaltyStrategy) -> None:
        """Set a new penalty calculation strategy.

        Args:
            strategy: The new penalty strategy to use.
        """
        self._penalty_strategy = strategy

    def generate_regular_invoice(
        self, contract_id: str, issue_date: date, amount: float | None = None
    ) -> Invoice:
        """Generate a regular monthly invoice for a contract.

        Args:
            contract_id: ID of the contract.
            issue_date: Date of invoice issuance.
            amount: Optional amount override.

        Returns:
            The new invoice.

        Raises:
            EntityNotFoundError: If contract not found.
            ContractNotActiveError: If contract is not active.
        """
        contract = self._contract_service.get_contract(contract_id)
        if not contract.is_active():
            raise ContractNotActiveError(contract_id)

        invoice = self._regular_factory.create_invoice(contract, issue_date, amount)
        return self._invoice_repo.add(invoice)

    def generate_deposit_invoice(self, contract_id: str, issue_date: date) -> Invoice:
        """Generate a deposit invoice for a contract.

        Args:
            contract_id: ID of the contract.
            issue_date: Date of invoice issuance.

        Returns:
            The new deposit invoice.
        """
        contract = self._contract_service.get_contract(contract_id)
        invoice = self._deposit_factory.create_invoice(contract, issue_date)
        return self._invoice_repo.add(invoice)

    def generate_penalty_invoice(
        self, contract_id: str, issue_date: date, penalty_amount: float
    ) -> Invoice:
        """Generate a penalty invoice for overdue payments.

        Args:
            contract_id: ID of the contract.
            issue_date: Date of invoice issuance.
            penalty_amount: Penalty amount to charge.

        Returns:
            The new penalty invoice.
        """
        contract = self._contract_service.get_contract(contract_id)
        invoice = self._penalty_factory.create_invoice(contract, issue_date, penalty_amount)
        return self._invoice_repo.add(invoice)

    def generate_settlement_invoice(
        self, contract_id: str, issue_date: date, settlement_amount: float
    ) -> Invoice:
        """Generate a final settlement invoice at check-out.

        Args:
            contract_id: ID of the contract.
            issue_date: Date of invoice issuance.
            settlement_amount: Final settlement amount.

        Returns:
            The new settlement invoice.
        """
        contract = self._contract_service.get_contract(contract_id)
        invoice = self._settlement_factory.create_invoice(contract, issue_date, settlement_amount)
        return self._invoice_repo.add(invoice)

    def apply_penalties(self, current_date: date) -> list[Invoice]:
        """Find overdue invoices and apply penalties using the current strategy.

        Args:
            current_date: Current date for overdue calculation.

        Returns:
            List of invoices that had penalties applied.
        """
        overdue_invoices = self._invoice_repo.find_overdue(current_date)
        penalized = []

        for invoice in overdue_invoices:
            days = invoice.days_overdue(current_date)
            penalty = self._penalty_strategy.calculate(invoice, days)

            if penalty > 0:
                invoice.add_penalty(penalty)
                invoice.mark_overdue()
                self._invoice_repo.update(invoice)

                # Add violation to tenant
                self._tenant_service.add_violation(invoice.tenant_id)
                penalized.append(invoice)

        return penalized

    def mark_invoice_paid(self, invoice_id: str) -> Invoice:
        """Mark an invoice as paid.

        Args:
            invoice_id: ID of the invoice.

        Returns:
            The updated invoice.

        Raises:
            EntityNotFoundError: If invoice not found.
            InvoiceAlreadyPaidError: If invoice is already paid.
        """
        invoice = self.get_invoice(invoice_id)
        if invoice.is_paid():
            raise InvoiceAlreadyPaidError(invoice_id)

        invoice.mark_paid()
        return self._invoice_repo.update(invoice)

    def cancel_invoice(self, invoice_id: str) -> Invoice:
        """Cancel an invoice.

        Args:
            invoice_id: ID of the invoice.

        Returns:
            The cancelled invoice.

        Raises:
            EntityNotFoundError: If invoice not found.
            InvoiceAlreadyPaidError: If invoice is already paid.
        """
        invoice = self.get_invoice(invoice_id)
        if invoice.is_paid():
            raise InvoiceAlreadyPaidError(invoice_id)

        invoice.cancel()
        return self._invoice_repo.update(invoice)

    def get_invoice(self, invoice_id: str) -> Invoice:
        """Retrieve an invoice by ID.

        Args:
            invoice_id: Unique identifier.

        Returns:
            The invoice.

        Raises:
            EntityNotFoundError: If not found.
        """
        invoice = self._invoice_repo.get_by_id(invoice_id)
        if invoice is None:
            raise EntityNotFoundError("Invoice", invoice_id)
        return invoice

    def get_all_invoices(self) -> list[Invoice]:
        """Get every invoice regardless of status.

        Returns:
            List of all invoices.
        """
        return self._invoice_repo.get_all()

    def get_invoices_by_tenant(self, tenant_id: str) -> list[Invoice]:
        """Get all invoices for a tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of invoices.
        """
        return self._invoice_repo.find_by_tenant(tenant_id)

    def get_invoices_by_contract(self, contract_id: str) -> list[Invoice]:
        """Get all invoices for a contract.

        Args:
            contract_id: ID of the contract.

        Returns:
            List of invoices.
        """
        return self._invoice_repo.find_by_contract(contract_id)

    def get_overdue_invoices(self, current_date: date) -> list[Invoice]:
        """Get all overdue invoices.

        Args:
            current_date: Date to check against.

        Returns:
            List of overdue invoices.
        """
        return self._invoice_repo.find_overdue(current_date)
