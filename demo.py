#!/usr/bin/env python3
"""
Interactive CLI Demo for the Rental Management System.

Run: python3 demo.py
"""
from __future__ import annotations

from datetime import date, timedelta

from src.models.enums import PaymentMethod, SpaceType
from src.services.booking_service import BookingService
from src.services.check_in_service import CheckInService
from src.services.contract_service import ContractService
from src.services.invoice_service import InvoiceService
from src.services.notification_service import BookingQueueNotifier, SpaceEventPublisher, TenantNotifier
from src.services.payment_service import PaymentService
from src.services.penalty_strategy import FlatRatePenalty, PercentagePenalty, ProgressivePenalty
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.booking_repository import InMemoryBookingRepository
from src.storage.check_in_repository import InMemoryCheckInRepository
from src.storage.contract_repository import InMemoryContractRepository
from src.storage.invoice_repository import InMemoryInvoiceRepository
from src.storage.payment_repository import InMemoryPaymentRepository
from src.storage.space_repository import InMemorySpaceRepository
from src.storage.tenant_repository import InMemoryTenantRepository


# ─── Colors ────────────────────────────────────────────────────────────
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")


def step(num: int, text: str) -> None:
    print(f"\n{BOLD}{YELLOW}  ▸ Step {num}: {text}{RESET}")


def ok(text: str) -> None:
    print(f"    {GREEN}✓{RESET} {text}")


def info(text: str) -> None:
    print(f"    {DIM}{text}{RESET}")


def err(text: str) -> None:
    print(f"    {RED}✗ {text}{RESET}")


def main() -> None:
    # ─── Bootstrap all services ────────────────────────────────────
    tenant_repo = InMemoryTenantRepository()
    space_repo = InMemorySpaceRepository()
    contract_repo = InMemoryContractRepository()
    booking_repo = InMemoryBookingRepository()
    check_in_repo = InMemoryCheckInRepository()
    invoice_repo = InMemoryInvoiceRepository()
    payment_repo = InMemoryPaymentRepository()

    # Observer pattern: set up event publisher with subscribers
    publisher = SpaceEventPublisher()
    booking_notifier = BookingQueueNotifier(booking_repo)
    tenant_notifier = TenantNotifier()
    publisher.subscribe("space_available", booking_notifier)
    publisher.subscribe("space_available", tenant_notifier)

    tenant_svc = TenantService(tenant_repo)
    space_svc = SpaceService(space_repo, publisher)
    contract_svc = ContractService(contract_repo, tenant_svc, space_svc)
    booking_svc = BookingService(booking_repo, tenant_svc, space_svc)
    check_in_svc = CheckInService(check_in_repo, tenant_svc, space_svc, contract_svc)
    invoice_svc = InvoiceService(invoice_repo, contract_svc, tenant_svc)
    payment_svc = PaymentService(payment_repo, invoice_svc)

    header("🏢 RENTAL MANAGEMENT SYSTEM — Live Demo")
    print(f"  {DIM}This demo walks through the full rental lifecycle.{RESET}")
    print(f"  {DIM}All data is in-memory — nothing is saved to disk.{RESET}")
    input(f"\n  {DIM}Press Enter to start...{RESET}")

    # ─── 1. Register tenants ───────────────────────────────────────
    step(1, "Register Tenants")
    alice = tenant_svc.register_tenant("Alice Johnson", "alice@example.com", "+380501111111")
    ok(f"Registered: {alice.name} (ID: {alice.id}, Status: {alice.status.value})")

    bob = tenant_svc.register_tenant("Bob Smith", "bob@example.com", "+380502222222")
    ok(f"Registered: {bob.name} (ID: {bob.id}, Status: {bob.status.value})")

    carol = tenant_svc.register_tenant("Carol Williams", "carol@example.com", "+380503333333")
    ok(f"Registered: {carol.name} (ID: {carol.id}, Status: {carol.status.value})")

    info(f"Total tenants: {len(tenant_svc.get_all_tenants())}")

    # ─── 2. Create spaces ─────────────────────────────────────────
    step(2, "Create Rentable Spaces")
    office = space_svc.create_space("Premium Office 301", SpaceType.OFFICE, 75.0, 3, 1500.0)
    ok(f"Created: {office.name} — {office.type.value}, {office.area_sqm}m², ₴{office.price_per_month}/mo")

    apt = space_svc.create_space("Apartment 102", SpaceType.APARTMENT, 90.0, 1, 2500.0)
    ok(f"Created: {apt.name} — {apt.type.value}, {apt.area_sqm}m², ₴{apt.price_per_month}/mo")

    parking = space_svc.create_space("Parking P-05", SpaceType.PARKING, 15.0, -1, 200.0)
    ok(f"Created: {parking.name} — {parking.type.value}, {parking.area_sqm}m², ₴{parking.price_per_month}/mo")

    info(f"Available spaces: {len(space_svc.get_available_spaces())}")

    # ─── 3. Book a space (priority queue) ──────────────────────────
    step(3, "Book Spaces (Priority Queue)")
    b1 = booking_svc.create_booking(
        bob.id, office.id,
        date.today() + timedelta(days=7), date.today() + timedelta(days=187),
        priority=1,
    )
    ok(f"Bob booked {office.name} with priority {b1.priority} (Status: {b1.status.value})")

    b2 = booking_svc.create_booking(
        carol.id, office.id,
        date.today() + timedelta(days=7), date.today() + timedelta(days=187),
        priority=10,
    )
    ok(f"Carol booked {office.name} with priority {b2.priority} (Status: {b2.status.value})")

    queue = booking_svc.get_pending_bookings_for_space(office.id)
    info(f"Queue for {office.name}: {[f'{tenant_svc.get_tenant(b.tenant_id).name} (pri={b.priority})' for b in queue]}")

    # ─── 4. Create & activate contract ─────────────────────────────
    step(4, "Create & Activate Contract")
    contract = contract_svc.create_contract(
        alice.id, office.id,
        date.today(), date.today() + timedelta(days=365),
        1500.0, 3000.0,
    )
    ok(f"Draft contract: {contract.id} (₴{contract.monthly_rate}/mo, deposit ₴{contract.deposit})")

    contract = contract_svc.activate_contract(contract.id)
    ok(f"Contract ACTIVATED → Space status: {space_svc.get_space(office.id).status.value}")

    # ─── 5. Check-in ───────────────────────────────────────────────
    step(5, "Check-In Tenant")
    check_in = check_in_svc.check_in(alice.id, office.id, contract.id)
    ok(f"Alice checked into {office.name} at {check_in.check_in_date.strftime('%Y-%m-%d %H:%M')}")

    # ─── 6. Generate & pay invoices ────────────────────────────────
    step(6, "Generate & Pay Invoices")

    dep_inv = invoice_svc.generate_deposit_invoice(contract.id, date.today())
    ok(f"Deposit invoice: {dep_inv.id} — ₴{dep_inv.total_amount} ({dep_inv.type.value})")

    reg_inv = invoice_svc.generate_regular_invoice(contract.id, date.today())
    ok(f"Monthly invoice: {reg_inv.id} — ₴{reg_inv.total_amount} ({reg_inv.type.value})")

    pay1 = payment_svc.process_payment(dep_inv.id, dep_inv.total_amount, PaymentMethod.BANK_TRANSFER)
    ok(f"Paid deposit: ₴{pay1.amount} via {pay1.method.value}")

    pay2 = payment_svc.process_payment(reg_inv.id, reg_inv.total_amount, PaymentMethod.CARD)
    ok(f"Paid monthly:  ₴{pay2.amount} via {pay2.method.value}")

    info(f"All invoices paid: {all(i.is_paid() for i in invoice_svc.get_invoices_by_contract(contract.id))}")

    # ─── 7. Penalty demo (Strategy Pattern) ────────────────────────
    step(7, "Penalty Calculation (Strategy Pattern)")
    from tests.conftest import make_invoice
    demo_inv = make_invoice(base_amount=1000.0)

    for strategy_name, strategy in [
        ("FlatRate(₴10/day)", FlatRatePenalty(10.0)),
        ("Percentage(1%/day)", PercentagePenalty(0.01)),
        ("Progressive(1%→2%→5%)", ProgressivePenalty(0.01, 0.02, 0.05)),
    ]:
        p = strategy.calculate(demo_inv, 15)
        ok(f"{strategy_name}: 15 days overdue on ₴1000 → penalty ₴{p:.2f}")

    # ─── 8. Check-out & terminate ──────────────────────────────────
    step(8, "Check-Out & Terminate Contract")
    check_in = check_in_svc.check_out(check_in.id)
    ok(f"Alice checked out at {check_in.check_out_date.strftime('%Y-%m-%d %H:%M')}")

    contract = contract_svc.terminate_contract(contract.id)
    ok(f"Contract terminated → Space status: {space_svc.get_space(office.id).status.value}")

    # ─── 9. Observer Pattern triggers ──────────────────────────────
    step(9, "Observer Pattern — Auto-Confirmation")
    info(f"Space '{office.name}' released → event published to {publisher.get_subscriber_count('space_available')} subscribers")

    if booking_notifier.last_confirmed_booking_id:
        confirmed = booking_repo.get_by_id(booking_notifier.last_confirmed_booking_id)
        tenant_name = tenant_svc.get_tenant(confirmed.tenant_id).name
        ok(f"Auto-confirmed booking for {tenant_name} (priority {confirmed.priority})")
    else:
        info("No bookings were auto-confirmed (they were for a different space release)")

    notifications = tenant_notifier.notifications
    if notifications:
        ok(f"Notifications sent: {len(notifications)}")

    # ─── 10. Violation & blocking demo ─────────────────────────────
    step(10, "Violation Tracking & Auto-Blocking")
    for i in range(3):
        dave = tenant_svc.get_tenant(bob.id) if i > 0 else bob
        dave = tenant_svc.add_violation(bob.id)
        ok(f"Violation #{dave.violation_count} → Status: {dave.status.value}")

    info(f"Bob is now blocked: {tenant_svc.get_tenant(bob.id).is_blocked()}")

    try:
        booking_svc.create_booking(
            bob.id, apt.id,
            date.today() + timedelta(days=14), date.today() + timedelta(days=44),
        )
    except Exception as e:
        err(f"Blocked tenant can't book: {e}")

    # ─── Summary ───────────────────────────────────────────────────
    header("📊 Final System State")
    print(f"  Tenants:   {tenant_repo.count()} ({len(tenant_svc.get_active_tenants())} active, {len(tenant_svc.get_blocked_tenants())} blocked)")
    print(f"  Spaces:    {space_repo.count()} ({len(space_svc.get_available_spaces())} available)")
    print(f"  Contracts: {contract_repo.count()}")
    print(f"  Bookings:  {booking_repo.count()}")
    print(f"  Invoices:  {invoice_repo.count()}")
    print(f"  Payments:  {payment_repo.count()}")
    print()


if __name__ == "__main__":
    main()
