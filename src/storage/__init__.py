"""Storage package for the Rental Management System.

Exports all repository interfaces and in-memory implementations.
"""
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.booking_repository import (
    IBookingRepository,
    InMemoryBookingRepository,
)
from src.storage.check_in_repository import (
    ICheckInRepository,
    InMemoryCheckInRepository,
)
from src.storage.contract_repository import (
    IContractRepository,
    InMemoryContractRepository,
)
from src.storage.interfaces import IReadRepository, IRepository, IWriteRepository
from src.storage.invoice_repository import (
    IInvoiceRepository,
    InMemoryInvoiceRepository,
)
from src.storage.payment_repository import (
    IPaymentRepository,
    InMemoryPaymentRepository,
)
from src.storage.space_repository import ISpaceRepository, InMemorySpaceRepository
from src.storage.tenant_repository import ITenantRepository, InMemoryTenantRepository

__all__ = [
    "IReadRepository",
    "IWriteRepository",
    "IRepository",
    "InMemoryBaseRepository",
    "ITenantRepository",
    "InMemoryTenantRepository",
    "ISpaceRepository",
    "InMemorySpaceRepository",
    "IContractRepository",
    "InMemoryContractRepository",
    "IBookingRepository",
    "InMemoryBookingRepository",
    "ICheckInRepository",
    "InMemoryCheckInRepository",
    "IInvoiceRepository",
    "InMemoryInvoiceRepository",
    "IPaymentRepository",
    "InMemoryPaymentRepository",
]
