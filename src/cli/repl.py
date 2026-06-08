"""Interactive REPL for the Rental Management System.

Provides a command-driven shell to manage tenants, spaces, contracts,
bookings, check-ins, invoices and payments against the in-memory backend.

The :class:`RentalCLI` is split so that :meth:`RentalCLI.execute` is a pure
function (line in, text out) and therefore fully unit-testable, while
:meth:`RentalCLI.run` only wires that to ``input``/``print`` for interactive use.
"""
from __future__ import annotations

import shlex
from collections.abc import Callable
from datetime import date

from src.models.booking import Booking
from src.models.check_in import CheckIn
from src.models.contract import Contract
from src.models.enums import PaymentMethod, SpaceType
from src.models.invoice import Invoice
from src.models.payment import Payment
from src.models.space import Space
from src.models.tenant import Tenant
from src.services.booking_service import BookingService
from src.services.check_in_service import CheckInService
from src.services.contract_service import ContractService
from src.services.invoice_service import InvoiceService
from src.services.notification_service import (
    BookingQueueNotifier,
    SpaceEventPublisher,
    TenantNotifier,
)
from src.services.payment_service import PaymentService
from src.services.penalty_strategy import (
    FlatRatePenalty,
    PercentagePenalty,
    ProgressivePenalty,
)
from src.services.space_service import SpaceService
from src.services.tenant_service import TenantService
from src.storage.booking_repository import InMemoryBookingRepository
from src.storage.check_in_repository import InMemoryCheckInRepository
from src.storage.contract_repository import InMemoryContractRepository
from src.storage.invoice_repository import InMemoryInvoiceRepository
from src.storage.payment_repository import InMemoryPaymentRepository
from src.storage.space_repository import InMemorySpaceRepository
from src.storage.tenant_repository import InMemoryTenantRepository
from src.utils.exceptions import RentalSystemError

BANNER = "🏢  Rental Management System — interactive CLI.  Type 'help' for commands, 'quit' to exit."

HELP_TEXT = """\
Commands (arguments in <> are required, [] optional):

  Tenants
    tenant add <name> <email> <phone>      Register a tenant
    tenant list                            List all tenants
    tenant show <id>                       Show one tenant
    tenant block <id>                      Block a tenant
    tenant activate <id>                   Re-activate a tenant
    tenant violate <id>                    Record a violation (auto-blocks at 3)

  Spaces            (type: office | apartment | parking | warehouse)
    space add <name> <type> <area> <floor> <price>   Create a space
    space list                             List all spaces
    space available                        List available spaces
    space show <id>                        Show one space

  Contracts         (dates: YYYY-MM-DD)
    contract create <tenant_id> <space_id> <start> <end> <rate> [deposit]
    contract activate <id>                 Activate (occupies the space)
    contract terminate <id>                Terminate (releases the space)
    contract list                          List all contracts
    contract show <id>                     Show one contract

  Bookings          (priority: integer, higher = served first)
    booking add <tenant_id> <space_id> <start> <end> [priority]
    booking confirm <id>                   Confirm a booking
    booking cancel <id>                    Cancel a booking
    booking list                           List all bookings

  Check-ins
    checkin in <tenant_id> <space_id> <contract_id>   Check a tenant in
    checkin out <id>                       Check out
    checkin list                           List active check-ins

  Invoices & payments   (method: cash | card | bank_transfer)
    invoice gen <contract_id> [issue_date]            Regular invoice
    invoice settle <contract_id> <amount> [issue_date] Final settlement
    invoice pay <invoice_id> <amount> <method>        Pay an invoice
    invoice list                           List all invoices
    invoice show <id>                      Show one invoice

  Penalty strategy (Strategy pattern)
    penalty flat <daily_rate>              Flat daily fee
    penalty percentage <daily_percent>     Percentage of invoice per day
    penalty progressive                    Escalating tiered penalty

  Misc
    seed                                   Load a small sample dataset
    stats                                  Show counts of all entities
    help                                   Show this help
    quit | exit                            Leave the CLI
"""


class RentalCLI:
    """Command dispatcher and in-memory state holder for the rental shell."""

    def __init__(self) -> None:
        """Bootstrap every service against fresh in-memory repositories."""
        tenant_repo = InMemoryTenantRepository()
        space_repo = InMemorySpaceRepository()
        contract_repo = InMemoryContractRepository()
        booking_repo = InMemoryBookingRepository()
        check_in_repo = InMemoryCheckInRepository()
        invoice_repo = InMemoryInvoiceRepository()
        payment_repo = InMemoryPaymentRepository()

        # Observer pattern: auto-confirm queued bookings when a space frees up.
        publisher = SpaceEventPublisher()
        publisher.subscribe("space_available", BookingQueueNotifier(booking_repo))
        publisher.subscribe("space_available", TenantNotifier())

        self.tenants = TenantService(tenant_repo)
        self.spaces = SpaceService(space_repo, publisher)
        self.contracts = ContractService(contract_repo, self.tenants, self.spaces)
        self.bookings = BookingService(booking_repo, self.tenants, self.spaces)
        self.check_ins = CheckInService(check_in_repo, self.tenants, self.spaces, self.contracts)
        self.invoices = InvoiceService(invoice_repo, self.contracts, self.tenants)
        self.payments = PaymentService(payment_repo, self.invoices)

        self._handlers: dict[str, Callable[[list[str]], str]] = {
            "tenant add": self._tenant_add,
            "tenant list": self._tenant_list,
            "tenant show": self._tenant_show,
            "tenant block": self._tenant_block,
            "tenant activate": self._tenant_activate,
            "tenant violate": self._tenant_violate,
            "space add": self._space_add,
            "space list": self._space_list,
            "space available": self._space_available,
            "space show": self._space_show,
            "contract create": self._contract_create,
            "contract activate": self._contract_activate,
            "contract terminate": self._contract_terminate,
            "contract list": self._contract_list,
            "contract show": self._contract_show,
            "booking add": self._booking_add,
            "booking confirm": self._booking_confirm,
            "booking cancel": self._booking_cancel,
            "booking list": self._booking_list,
            "checkin in": self._checkin_in,
            "checkin out": self._checkin_out,
            "checkin list": self._checkin_list,
            "invoice gen": self._invoice_gen,
            "invoice settle": self._invoice_settle,
            "invoice pay": self._invoice_pay,
            "invoice list": self._invoice_list,
            "invoice show": self._invoice_show,
            "penalty flat": self._penalty_flat,
            "penalty percentage": self._penalty_percentage,
            "penalty progressive": self._penalty_progressive,
        }

    # ── Public API ────────────────────────────────────────────────────

    def execute(self, line: str) -> str:
        """Parse and run a single command line, returning its text output.

        Args:
            line: Raw command line (may contain quoted arguments).

        Returns:
            Human-readable result, or an ``Error: ...`` message on failure.
            Empty input and the ``quit``/``exit``/``help`` words are handled too.
        """
        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            return f"Error: could not parse input ({exc})"
        if not tokens:
            return ""

        word = tokens[0].lower()
        if word in {"quit", "exit"}:
            return "Bye!"
        if word in {"help", "?"}:
            return HELP_TEXT
        if word == "stats":
            return self._stats()
        if word == "seed":
            return self._seed()

        if len(tokens) >= 2:
            key = f"{word} {tokens[1].lower()}"
            handler = self._handlers.get(key)
            if handler is not None:
                try:
                    return handler(tokens[2:])
                except (RentalSystemError, ValueError) as exc:
                    return f"Error: {exc}"
                except IndexError:
                    return f"Error: missing arguments for '{key}'. Type 'help'."

        return f"Unknown command: '{line.strip()}'. Type 'help' for the list."

    def run(
        self,
        input_fn: Callable[[str], str] | None = None,
        output_fn: Callable[[str], None] | None = None,
    ) -> None:
        """Run the interactive read-eval-print loop.

        Args:
            input_fn: Callable used to read a line (injectable for tests).
                Defaults to the built-in ``input`` (resolved at call time).
            output_fn: Callable used to write output (injectable for tests).
                Defaults to the built-in ``print`` (resolved at call time).
        """
        input_fn = input_fn or input
        output_fn = output_fn or print
        output_fn(BANNER)
        while True:
            try:
                line = input_fn("rms> ")
            except (EOFError, KeyboardInterrupt):
                output_fn("\nBye!")
                return
            result = self.execute(line)
            if result:
                output_fn(result)
            if result == "Bye!":
                return

    # ── Tenant handlers ───────────────────────────────────────────────

    def _tenant_add(self, args: list[str]) -> str:
        name, email, phone = args[0], args[1], args[2]
        tenant = self.tenants.register_tenant(name, email, phone)
        return f"✓ Registered {self._fmt_tenant(tenant)}"

    def _tenant_list(self, args: list[str]) -> str:
        return self._table([self._fmt_tenant(t) for t in self.tenants.get_all_tenants()], "tenants")

    def _tenant_show(self, args: list[str]) -> str:
        return self._fmt_tenant(self.tenants.get_tenant(args[0]))

    def _tenant_block(self, args: list[str]) -> str:
        return f"✓ Blocked {self._fmt_tenant(self.tenants.block_tenant(args[0]))}"

    def _tenant_activate(self, args: list[str]) -> str:
        return f"✓ Activated {self._fmt_tenant(self.tenants.activate_tenant(args[0]))}"

    def _tenant_violate(self, args: list[str]) -> str:
        return f"✓ Violation recorded → {self._fmt_tenant(self.tenants.add_violation(args[0]))}"

    # ── Space handlers ────────────────────────────────────────────────

    def _space_add(self, args: list[str]) -> str:
        name, type_str, area, floor, price = args[0], args[1], args[2], args[3], args[4]
        space = self.spaces.create_space(
            name, SpaceType(type_str.lower()), float(area), int(floor), float(price)
        )
        return f"✓ Created {self._fmt_space(space)}"

    def _space_list(self, args: list[str]) -> str:
        return self._table([self._fmt_space(s) for s in self.spaces.get_all_spaces()], "spaces")

    def _space_available(self, args: list[str]) -> str:
        return self._table([self._fmt_space(s) for s in self.spaces.get_available_spaces()], "available spaces")

    def _space_show(self, args: list[str]) -> str:
        return self._fmt_space(self.spaces.get_space(args[0]))

    # ── Contract handlers ─────────────────────────────────────────────

    def _contract_create(self, args: list[str]) -> str:
        deposit = float(args[5]) if len(args) > 5 else 0.0
        contract = self.contracts.create_contract(
            args[0], args[1], _parse_date(args[2]), _parse_date(args[3]), float(args[4]), deposit
        )
        return f"✓ Created {self._fmt_contract(contract)}"

    def _contract_activate(self, args: list[str]) -> str:
        return f"✓ Activated {self._fmt_contract(self.contracts.activate_contract(args[0]))}"

    def _contract_terminate(self, args: list[str]) -> str:
        return f"✓ Terminated {self._fmt_contract(self.contracts.terminate_contract(args[0]))}"

    def _contract_list(self, args: list[str]) -> str:
        rows = [self._fmt_contract(c) for c in self.contracts.get_all_contracts()]
        return self._table(rows, "contracts")

    def _contract_show(self, args: list[str]) -> str:
        return self._fmt_contract(self.contracts.get_contract(args[0]))

    # ── Booking handlers ──────────────────────────────────────────────

    def _booking_add(self, args: list[str]) -> str:
        priority = int(args[4]) if len(args) > 4 else 0
        booking = self.bookings.create_booking(
            args[0], args[1], _parse_date(args[2]), _parse_date(args[3]), priority
        )
        return f"✓ Booked {self._fmt_booking(booking)}"

    def _booking_confirm(self, args: list[str]) -> str:
        return f"✓ Confirmed {self._fmt_booking(self.bookings.confirm_booking(args[0]))}"

    def _booking_cancel(self, args: list[str]) -> str:
        return f"✓ Cancelled {self._fmt_booking(self.bookings.cancel_booking(args[0]))}"

    def _booking_list(self, args: list[str]) -> str:
        rows = [self._fmt_booking(b) for b in self.bookings.get_all_bookings()]
        return self._table(rows, "bookings")

    # ── Check-in handlers ─────────────────────────────────────────────

    def _checkin_in(self, args: list[str]) -> str:
        record = self.check_ins.check_in(args[0], args[1], args[2])
        return f"✓ Checked in {self._fmt_checkin(record)}"

    def _checkin_out(self, args: list[str]) -> str:
        return f"✓ Checked out {self._fmt_checkin(self.check_ins.check_out(args[0]))}"

    def _checkin_list(self, args: list[str]) -> str:
        return self._table([self._fmt_checkin(c) for c in self.check_ins.get_active_check_ins()], "check-ins")

    # ── Invoice & payment handlers ────────────────────────────────────

    def _invoice_gen(self, args: list[str]) -> str:
        issue = _parse_date(args[1]) if len(args) > 1 else date.today()
        invoice = self.invoices.generate_regular_invoice(args[0], issue)
        return f"✓ Issued {self._fmt_invoice(invoice)}"

    def _invoice_settle(self, args: list[str]) -> str:
        issue = _parse_date(args[2]) if len(args) > 2 else date.today()
        invoice = self.invoices.generate_settlement_invoice(args[0], issue, float(args[1]))
        return f"✓ Issued {self._fmt_invoice(invoice)}"

    def _invoice_pay(self, args: list[str]) -> str:
        payment = self.payments.process_payment(args[0], float(args[1]), PaymentMethod(args[2].lower()))
        return f"✓ Paid {self._fmt_payment(payment)}"

    def _invoice_list(self, args: list[str]) -> str:
        rows = [self._fmt_invoice(i) for i in self.invoices.get_all_invoices()]
        return self._table(rows, "invoices")

    def _invoice_show(self, args: list[str]) -> str:
        return self._fmt_invoice(self.invoices.get_invoice(args[0]))

    # ── Penalty strategy handlers ─────────────────────────────────────

    def _penalty_flat(self, args: list[str]) -> str:
        self.invoices.penalty_strategy = FlatRatePenalty(float(args[0]))
        return f"✓ Penalty strategy → FlatRatePenalty({float(args[0])}/day)"

    def _penalty_percentage(self, args: list[str]) -> str:
        self.invoices.penalty_strategy = PercentagePenalty(float(args[0]))
        return f"✓ Penalty strategy → PercentagePenalty({float(args[0])}%/day)"

    def _penalty_progressive(self, args: list[str]) -> str:
        self.invoices.penalty_strategy = ProgressivePenalty()
        return "✓ Penalty strategy → ProgressivePenalty (tiered)"

    # ── Misc handlers ─────────────────────────────────────────────────

    def _stats(self) -> str:
        return (
            "Current in-memory state:\n"
            f"  Tenants:    {len(self.tenants.get_all_tenants())} "
            f"({len(self.tenants.get_active_tenants())} active, "
            f"{len(self.tenants.get_blocked_tenants())} blocked)\n"
            f"  Spaces:     {len(self.spaces.get_all_spaces())} "
            f"({len(self.spaces.get_available_spaces())} available)\n"
            f"  Contracts:  {len(self.contracts.get_all_contracts())}\n"
            f"  Bookings:   {len(self.bookings.get_all_bookings())}\n"
            f"  Check-ins:  {len(self.check_ins.get_active_check_ins())} active\n"
            f"  Invoices:   {len(self.invoices.get_all_invoices())}\n"
            f"  Payments:   {len(self.payments.get_all_payments())} recorded"
        )

    def _seed(self) -> str:
        """Populate a small sample dataset to explore the commands quickly."""
        alice = self.tenants.register_tenant("Alice Johnson", "alice@mail.com", "+380501112233")
        self.tenants.register_tenant("Bob Smith", "bob@mail.com", "+380502223344")
        office = self.spaces.create_space("Office 301", SpaceType.OFFICE, 50.0, 3, 1500.0)
        self.spaces.create_space("Parking A-12", SpaceType.PARKING, 12.0, 0, 200.0)
        contract = self.contracts.create_contract(
            alice.id, office.id, date.today(), date(date.today().year + 1, date.today().month, 1), 1500.0, 1500.0
        )
        self.contracts.activate_contract(contract.id)
        return (
            "✓ Seeded sample data:\n"
            f"  tenant  {alice.id}  (Alice, active)\n"
            f"  space   {office.id}  (Office 301, now occupied)\n"
            f"  contract {contract.id}  (active)\n"
            "Try: 'invoice gen " + contract.id + "' then 'stats'."
        )

    # ── Formatting helpers ────────────────────────────────────────────

    @staticmethod
    def _fmt_tenant(t: Tenant) -> str:
        return f"{t.id}  {t.name} <{t.email}>  {t.status.value}  violations={t.violation_count}"

    @staticmethod
    def _fmt_space(s: Space) -> str:
        return (
            f"{s.id}  {s.name}  {s.type.value}  {s.area_sqm}m² floor {s.floor}  "
            f"{s.price_per_month}/mo  {s.status.value}"
        )

    @staticmethod
    def _fmt_contract(c: Contract) -> str:
        return (
            f"{c.id}  tenant={c.tenant_id} space={c.space_id}  "
            f"{c.start_date}→{c.end_date}  {c.monthly_rate}/mo  {c.status.value}"
        )

    @staticmethod
    def _fmt_booking(b: Booking) -> str:
        return (
            f"{b.id}  tenant={b.tenant_id} space={b.space_id}  "
            f"{b.desired_start}→{b.desired_end}  priority={b.priority}  {b.status.value}"
        )

    @staticmethod
    def _fmt_checkin(c: CheckIn) -> str:
        out = c.check_out_date.strftime("%Y-%m-%d %H:%M") if c.check_out_date else "—"
        return (
            f"{c.id}  tenant={c.tenant_id} space={c.space_id}  "
            f"in={c.check_in_date:%Y-%m-%d %H:%M}  out={out}  {c.status.value}"
        )

    @staticmethod
    def _fmt_invoice(i: Invoice) -> str:
        return (
            f"{i.id}  contract={i.contract_id}  {i.type.value}  "
            f"base={i.base_amount} penalty={i.penalty_amount} total={i.total_amount}  {i.status.value}"
        )

    @staticmethod
    def _fmt_payment(p: Payment) -> str:
        return f"{p.id}  invoice={p.invoice_id}  {p.amount}  {p.method.value}  {p.payment_date:%Y-%m-%d %H:%M}"

    @staticmethod
    def _table(rows: list[str], label: str) -> str:
        if not rows:
            return f"(no {label})"
        return "\n".join(rows) + f"\n— {len(rows)} {label}"


def _parse_date(text: str) -> date:
    """Parse an ISO ``YYYY-MM-DD`` date, raising ValueError with a clear message."""
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid date '{text}', expected YYYY-MM-DD") from exc


def main() -> None:
    """Entry point: start an interactive :class:`RentalCLI` session."""
    RentalCLI().run()


if __name__ == "__main__":
    main()
