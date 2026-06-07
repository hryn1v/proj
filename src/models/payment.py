"""Payment domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.models.enums import PaymentMethod


@dataclass
class Payment:
    """Represents a payment made against an invoice.

    Attributes:
        id: Unique identifier for the payment.
        invoice_id: ID of the invoice being paid.
        amount: Payment amount.
        payment_date: Timestamp when the payment was made.
        method: Payment method used.
    """

    id: str
    invoice_id: str
    amount: float
    method: PaymentMethod
    payment_date: datetime = field(default_factory=datetime.now)
