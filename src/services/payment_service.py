"""Payment processing service."""
from __future__ import annotations

from src.models.enums import PaymentMethod
from src.models.payment import Payment
from src.services.invoice_service import InvoiceService
from src.storage.payment_repository import IPaymentRepository
from src.utils.exceptions import (
    EntityNotFoundError,
    InvoiceAlreadyPaidError,
    ValidationError,
)
from src.utils.id_generator import generate_prefixed_id
from src.utils.validators import validate_positive_amount


class PaymentService:
    """Service for processing payments against invoices.

    Validates payment amounts, records payments, and updates
    invoice status upon successful payment.

    Attributes:
        _payment_repo: Repository for payment persistence.
        _invoice_service: Service for invoice operations.
    """

    def __init__(
        self,
        payment_repo: IPaymentRepository,
        invoice_service: InvoiceService,
    ) -> None:
        """Initialize with required repositories and services.

        Args:
            payment_repo: Repository implementing IPaymentRepository.
            invoice_service: Service for invoice operations.
        """
        self._payment_repo = payment_repo
        self._invoice_service = invoice_service

    def process_payment(
        self,
        invoice_id: str,
        amount: float,
        method: PaymentMethod,
    ) -> Payment:
        """Process a payment for an invoice.

        Args:
            invoice_id: ID of the invoice being paid.
            amount: Payment amount.
            method: Payment method used.

        Returns:
            The recorded payment.

        Raises:
            EntityNotFoundError: If invoice not found.
            InvoiceAlreadyPaidError: If invoice is already paid.
            ValidationError: If amount is invalid or insufficient.
        """
        invoice = self._invoice_service.get_invoice(invoice_id)

        if invoice.is_paid():
            raise InvoiceAlreadyPaidError(invoice_id)

        if not validate_positive_amount(amount):
            raise ValidationError("amount", "Payment amount must be positive")

        if amount < invoice.total_amount:
            raise ValidationError(
                "amount",
                f"Payment amount ({amount}) is less than invoice total ({invoice.total_amount})"
            )

        payment = Payment(
            id=generate_prefixed_id("PAY"),
            invoice_id=invoice_id,
            amount=amount,
            method=method,
        )

        recorded = self._payment_repo.add(payment)
        self._invoice_service.mark_invoice_paid(invoice_id)

        return recorded

    def get_payment(self, payment_id: str) -> Payment:
        """Retrieve a payment by ID.

        Args:
            payment_id: Unique identifier.

        Returns:
            The payment.

        Raises:
            EntityNotFoundError: If not found.
        """
        payment = self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise EntityNotFoundError("Payment", payment_id)
        return payment

    def get_all_payments(self) -> list[Payment]:
        """Get every recorded payment.

        Returns:
            List of all payments.
        """
        return self._payment_repo.get_all()

    def get_payments_for_invoice(self, invoice_id: str) -> list[Payment]:
        """Get all payments for an invoice.

        Args:
            invoice_id: ID of the invoice.

        Returns:
            List of payments.
        """
        return self._payment_repo.find_by_invoice(invoice_id)

    def get_total_paid_for_invoice(self, invoice_id: str) -> float:
        """Calculate the total amount paid for an invoice.

        Args:
            invoice_id: ID of the invoice.

        Returns:
            Total paid amount.
        """
        payments = self._payment_repo.find_by_invoice(invoice_id)
        return sum(p.amount for p in payments)
