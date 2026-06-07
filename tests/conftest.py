"""Shared test fixtures for the Rental Management System."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from src.models.booking import Booking
from src.models.check_in import CheckIn
from src.models.contract import Contract
from src.models.enums import (
    BookingStatus,
    ContractStatus,
    InvoiceType,
    PaymentMethod,
    SpaceStatus,
    SpaceType,
    TenantStatus,
)
from src.models.invoice import Invoice
from src.models.notification import Notification
from src.models.payment import Payment
from src.models.space import Space
from src.models.tenant import Tenant
from src.services.booking_service import BookingService
from src.services.check_in_service import CheckInService
from src.services.contract_service import ContractService
from src.services.invoice_service import InvoiceService
from src.services.notification_service import SpaceEventPublisher
from src.services.payment_service import PaymentService
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.booking_repository import InMemoryBookingRepository
from src.storage.check_in_repository import InMemoryCheckInRepository
from src.storage.contract_repository import InMemoryContractRepository
from src.storage.invoice_repository import InMemoryInvoiceRepository
from src.storage.payment_repository import InMemoryPaymentRepository
from src.storage.space_repository import InMemorySpaceRepository
from src.storage.tenant_repository import InMemoryTenantRepository


# ─── Sample Data Helpers ───────────────────────────────────────────────


def make_tenant(
    id: str = "TNT-test001",
    name: str = "John Doe",
    email: str = "john@example.com",
    phone: str = "+380501234567",
    status: TenantStatus = TenantStatus.ACTIVE,
    violation_count: int = 0,
) -> Tenant:
    """Create a sample tenant for testing."""
    return Tenant(
        id=id, name=name, email=email, phone=phone,
        status=status, violation_count=violation_count,
    )


def make_space(
    id: str = "SPC-test001",
    name: str = "Office 101",
    type: SpaceType = SpaceType.OFFICE,
    area_sqm: float = 50.0,
    floor: int = 1,
    price_per_month: float = 1000.0,
    status: SpaceStatus = SpaceStatus.AVAILABLE,
) -> Space:
    """Create a sample space for testing."""
    return Space(
        id=id, name=name, type=type, area_sqm=area_sqm,
        floor=floor, price_per_month=price_per_month, status=status,
    )


def make_contract(
    id: str = "CTR-test001",
    tenant_id: str = "TNT-test001",
    space_id: str = "SPC-test001",
    start_date: date | None = None,
    end_date: date | None = None,
    monthly_rate: float = 1000.0,
    deposit: float = 2000.0,
    status: ContractStatus = ContractStatus.DRAFT,
) -> Contract:
    """Create a sample contract for testing."""
    today = date.today()
    return Contract(
        id=id, tenant_id=tenant_id, space_id=space_id,
        start_date=start_date or today,
        end_date=end_date or date(today.year + 1, today.month, today.day),
        monthly_rate=monthly_rate, deposit=deposit, status=status,
    )


def make_booking(
    id: str = "BKG-test001",
    tenant_id: str = "TNT-test001",
    space_id: str = "SPC-test001",
    desired_start: date | None = None,
    desired_end: date | None = None,
    priority: int = 0,
    status: BookingStatus = BookingStatus.PENDING,
) -> Booking:
    """Create a sample booking for testing."""
    today = date.today()
    return Booking(
        id=id, tenant_id=tenant_id, space_id=space_id,
        desired_start=desired_start or today + timedelta(days=7),
        desired_end=desired_end or today + timedelta(days=37),
        priority=priority, status=status,
    )


def make_invoice(
    id: str = "INV-test001",
    contract_id: str = "CTR-test001",
    tenant_id: str = "TNT-test001",
    base_amount: float = 1000.0,
    penalty_amount: float = 0.0,
    issue_date: date | None = None,
    due_date: date | None = None,
    type: InvoiceType = InvoiceType.REGULAR,
) -> Invoice:
    """Create a sample invoice for testing."""
    today = date.today()
    return Invoice(
        id=id, contract_id=contract_id, tenant_id=tenant_id,
        base_amount=base_amount, penalty_amount=penalty_amount,
        issue_date=issue_date or today,
        due_date=due_date or today + timedelta(days=30),
        type=type,
    )


def make_payment(
    id: str = "PAY-test001",
    invoice_id: str = "INV-test001",
    amount: float = 1000.0,
    method: PaymentMethod = PaymentMethod.CARD,
) -> Payment:
    """Create a sample payment for testing."""
    return Payment(id=id, invoice_id=invoice_id, amount=amount, method=method)


# ─── Repository Fixtures ──────────────────────────────────────────────


@pytest.fixture
def tenant_repo():
    """Provide a fresh in-memory tenant repository."""
    return InMemoryTenantRepository()


@pytest.fixture
def space_repo():
    """Provide a fresh in-memory space repository."""
    return InMemorySpaceRepository()


@pytest.fixture
def contract_repo():
    """Provide a fresh in-memory contract repository."""
    return InMemoryContractRepository()


@pytest.fixture
def booking_repo():
    """Provide a fresh in-memory booking repository."""
    return InMemoryBookingRepository()


@pytest.fixture
def check_in_repo():
    """Provide a fresh in-memory check-in repository."""
    return InMemoryCheckInRepository()


@pytest.fixture
def invoice_repo():
    """Provide a fresh in-memory invoice repository."""
    return InMemoryInvoiceRepository()


@pytest.fixture
def payment_repo():
    """Provide a fresh in-memory payment repository."""
    return InMemoryPaymentRepository()


# ─── Service Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def event_publisher():
    """Provide a fresh event publisher."""
    return SpaceEventPublisher()


@pytest.fixture
def tenant_service(tenant_repo):
    """Provide a tenant service with fresh repository."""
    return TenantService(tenant_repo)


@pytest.fixture
def space_service(space_repo, event_publisher):
    """Provide a space service with fresh repository and event publisher."""
    return SpaceService(space_repo, event_publisher)


@pytest.fixture
def contract_service(contract_repo, tenant_service, space_service):
    """Provide a contract service with all dependencies."""
    return ContractService(contract_repo, tenant_service, space_service)


@pytest.fixture
def booking_service(booking_repo, tenant_service, space_service):
    """Provide a booking service with all dependencies."""
    return BookingService(booking_repo, tenant_service, space_service)


@pytest.fixture
def check_in_service(check_in_repo, tenant_service, space_service, contract_service):
    """Provide a check-in service with all dependencies."""
    return CheckInService(check_in_repo, tenant_service, space_service, contract_service)


@pytest.fixture
def invoice_service(invoice_repo, contract_service, tenant_service):
    """Provide an invoice service with all dependencies."""
    return InvoiceService(invoice_repo, contract_service, tenant_service)


@pytest.fixture
def payment_service(payment_repo, invoice_service):
    """Provide a payment service with all dependencies."""
    return PaymentService(payment_repo, invoice_service)
