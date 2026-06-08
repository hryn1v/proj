"""Unit tests for the interactive CLI REPL (src/cli/repl.py)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.cli.repl import RentalCLI, _parse_date, main


@pytest.fixture
def cli() -> RentalCLI:
    """Return a fresh CLI with empty in-memory state."""
    return RentalCLI()


@pytest.fixture
def seeded(cli: RentalCLI) -> RentalCLI:
    """Return a CLI pre-populated with one tenant, space and active contract."""
    cli.execute('tenant add "Alice" alice@mail.com +380501112233')
    cli.execute('space add "Office" office 50 3 1500')
    tid = cli.tenants.get_all_tenants()[0].id
    sid = cli.spaces.get_all_spaces()[0].id
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=365)).isoformat()
    cli.execute(f"contract create {tid} {sid} {start} {end} 1500 1500")
    cid = cli.contracts.get_all_contracts()[0].id
    cli.execute(f"contract activate {cid}")
    return cli


# ── Parsing & meta commands ───────────────────────────────────────────

def test_empty_input_returns_empty(cli: RentalCLI) -> None:
    assert cli.execute("") == ""
    assert cli.execute("   ") == ""


def test_unbalanced_quotes_returns_error(cli: RentalCLI) -> None:
    assert cli.execute('tenant add "unterminated').startswith("Error:")


def test_help(cli: RentalCLI) -> None:
    out = cli.execute("help")
    assert "Commands" in out and "tenant add" in out
    assert cli.execute("?") == out


def test_quit_and_exit(cli: RentalCLI) -> None:
    assert cli.execute("quit") == "Bye!"
    assert cli.execute("exit") == "Bye!"


def test_unknown_command(cli: RentalCLI) -> None:
    assert cli.execute("frobnicate now").startswith("Unknown command")


def test_unknown_single_word(cli: RentalCLI) -> None:
    assert cli.execute("wat").startswith("Unknown command")


def test_missing_arguments(cli: RentalCLI) -> None:
    assert "missing arguments" in cli.execute("tenant add Alice")


# ── Tenant commands ───────────────────────────────────────────────────

def test_tenant_add_and_list(cli: RentalCLI) -> None:
    out = cli.execute('tenant add "Alice Johnson" alice@mail.com +380501112233')
    assert out.startswith("✓ Registered")
    assert "Alice Johnson" in cli.execute("tenant list")


def test_tenant_list_empty(cli: RentalCLI) -> None:
    assert cli.execute("tenant list") == "(no tenants)"


def test_tenant_show_block_activate_violate(cli: RentalCLI) -> None:
    cli.execute('tenant add "Bob" bob@mail.com +380502223344')
    tid = cli.tenants.get_all_tenants()[0].id
    assert tid in cli.execute(f"tenant show {tid}")
    assert "blocked" in cli.execute(f"tenant block {tid}")
    assert "active" in cli.execute(f"tenant activate {tid}")
    assert "violations=1" in cli.execute(f"tenant violate {tid}")


def test_tenant_show_missing_raises(cli: RentalCLI) -> None:
    assert cli.execute("tenant show TNT-nope").startswith("Error:")


def test_tenant_add_invalid_email(cli: RentalCLI) -> None:
    assert cli.execute('tenant add "Bad" not-an-email +380501112233').startswith("Error:")


# ── Space commands ────────────────────────────────────────────────────

@pytest.mark.parametrize("space_type", ["office", "apartment", "parking", "warehouse"])
def test_space_add_all_types(cli: RentalCLI, space_type: str) -> None:
    out = cli.execute(f'space add "Unit" {space_type} 30 1 500')
    assert out.startswith("✓ Created") and space_type in out


def test_space_invalid_type(cli: RentalCLI) -> None:
    assert cli.execute('space add "Unit" castle 30 1 500').startswith("Error:")


def test_space_list_available_show(cli: RentalCLI) -> None:
    cli.execute('space add "Office" office 50 3 1500')
    sid = cli.spaces.get_all_spaces()[0].id
    assert "Office" in cli.execute("space list")
    assert "Office" in cli.execute("space available")
    assert sid in cli.execute(f"space show {sid}")


def test_space_add_negative_price(cli: RentalCLI) -> None:
    assert cli.execute('space add "Office" office 50 3 -10').startswith("Error:")


# ── Contract commands ─────────────────────────────────────────────────

def test_contract_full_lifecycle(seeded: RentalCLI) -> None:
    cid = seeded.contracts.get_all_contracts()[0].id
    assert "active" in seeded.execute(f"contract show {cid}")
    assert cid in seeded.execute("contract list")
    assert "terminated" in seeded.execute(f"contract terminate {cid}")


def test_contract_invalid_date(cli: RentalCLI) -> None:
    cli.execute('tenant add "Alice" alice@mail.com +380501112233')
    cli.execute('space add "Office" office 50 3 1500')
    tid = cli.tenants.get_all_tenants()[0].id
    sid = cli.spaces.get_all_spaces()[0].id
    assert "invalid date" in cli.execute(f"contract create {tid} {sid} 2026-13-01 2027-01-01 1500")


def test_contract_create_without_deposit(cli: RentalCLI) -> None:
    cli.execute('tenant add "Alice" alice@mail.com +380501112233')
    cli.execute('space add "Office" office 50 3 1500')
    tid = cli.tenants.get_all_tenants()[0].id
    sid = cli.spaces.get_all_spaces()[0].id
    start, end = date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()
    out = cli.execute(f"contract create {tid} {sid} {start} {end} 1500")
    assert out.startswith("✓ Created")


def test_contract_list_empty(cli: RentalCLI) -> None:
    assert cli.execute("contract list") == "(no contracts)"


# ── Booking commands & Observer auto-confirm ──────────────────────────

def test_booking_add_confirm_cancel_list(cli: RentalCLI) -> None:
    cli.execute('tenant add "Alice" alice@mail.com +380501112233')
    cli.execute('space add "Office" office 50 3 1500')
    tid = cli.tenants.get_all_tenants()[0].id
    sid = cli.spaces.get_all_spaces()[0].id
    start, end = date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()
    out = cli.execute(f"booking add {tid} {sid} {start} {end} 5")
    assert out.startswith("✓ Booked") and "priority=5" in out
    bid = cli.bookings.get_all_bookings()[0].id
    assert "confirmed" in cli.execute(f"booking confirm {bid}")
    assert bid in cli.execute("booking list")
    # add a second booking and cancel it
    cli.execute('tenant add "Bob" bob@mail.com +380502223344')
    tid2 = cli.tenants.get_all_tenants()[1].id
    cli.execute(f"booking add {tid2} {sid} {start} {end}")
    bid2 = cli.bookings.get_bookings_by_tenant(tid2)[0].id
    assert "cancelled" in cli.execute(f"booking cancel {bid2}")


def test_booking_list_empty(cli: RentalCLI) -> None:
    assert cli.execute("booking list") == "(no bookings)"


# ── Check-in commands ─────────────────────────────────────────────────

def test_checkin_in_out_list(seeded: RentalCLI) -> None:
    tid = seeded.tenants.get_all_tenants()[0].id
    sid = seeded.spaces.get_all_spaces()[0].id
    cid = seeded.contracts.get_all_contracts()[0].id
    out = seeded.execute(f"checkin in {tid} {sid} {cid}")
    assert out.startswith("✓ Checked in")
    chid = seeded.check_ins.get_active_check_ins()[0].id
    assert chid in seeded.execute("checkin list")
    assert "checked_out" in seeded.execute(f"checkin out {chid}")


def test_checkin_list_empty(cli: RentalCLI) -> None:
    assert cli.execute("checkin list") == "(no check-ins)"


# ── Invoice & payment commands ────────────────────────────────────────

def test_invoice_gen_pay_show_list(seeded: RentalCLI) -> None:
    cid = seeded.contracts.get_all_contracts()[0].id
    out = seeded.execute(f"invoice gen {cid}")
    assert out.startswith("✓ Issued")
    iid = seeded.invoices.get_all_invoices()[0].id
    assert iid in seeded.execute("invoice list")
    assert iid in seeded.execute(f"invoice show {iid}")
    paid = seeded.execute(f"invoice pay {iid} 1500 card")
    assert paid.startswith("✓ Paid") and "card" in paid
    assert "paid" in seeded.execute(f"invoice show {iid}")


def test_invoice_gen_with_explicit_date(seeded: RentalCLI) -> None:
    cid = seeded.contracts.get_all_contracts()[0].id
    assert seeded.execute(f"invoice gen {cid} 2026-01-15").startswith("✓ Issued")


def test_invoice_settle(seeded: RentalCLI) -> None:
    cid = seeded.contracts.get_all_contracts()[0].id
    out = seeded.execute(f"invoice settle {cid} 800 2026-02-01")
    assert out.startswith("✓ Issued") and "final_settlement" in out


def test_invoice_pay_invalid_method(seeded: RentalCLI) -> None:
    cid = seeded.contracts.get_all_contracts()[0].id
    seeded.execute(f"invoice gen {cid}")
    iid = seeded.invoices.get_all_invoices()[0].id
    assert seeded.execute(f"invoice pay {iid} 1500 bitcoin").startswith("Error:")


def test_invoice_list_empty(cli: RentalCLI) -> None:
    assert cli.execute("invoice list") == "(no invoices)"


# ── Penalty strategy commands ─────────────────────────────────────────

def test_penalty_strategies(cli: RentalCLI) -> None:
    assert "FlatRatePenalty" in cli.execute("penalty flat 10")
    assert "PercentagePenalty" in cli.execute("penalty percentage 2.5")
    assert "ProgressivePenalty" in cli.execute("penalty progressive")


# ── Misc commands ─────────────────────────────────────────────────────

def test_stats(cli: RentalCLI) -> None:
    out = cli.execute("stats")
    assert "Tenants:" in out and "Payments:" in out


def test_seed_then_stats(cli: RentalCLI) -> None:
    out = cli.execute("seed")
    assert out.startswith("✓ Seeded")
    stats = cli.execute("stats")
    assert "Tenants:    2" in stats


# ── run() loop & entry point ──────────────────────────────────────────

def test_run_loop_processes_then_quits() -> None:
    lines = iter(["seed", "stats", "quit"])
    outputs: list[str] = []
    RentalCLI().run(input_fn=lambda _prompt: next(lines), output_fn=outputs.append)
    joined = "\n".join(outputs)
    assert joined.startswith("🏢")
    assert "Seeded" in joined
    assert outputs[-1] == "Bye!"


def test_run_loop_handles_eof() -> None:
    def raise_eof(_prompt: str) -> str:
        raise EOFError

    outputs: list[str] = []
    RentalCLI().run(input_fn=raise_eof, output_fn=outputs.append)
    assert outputs[-1] == "\nBye!"


def test_run_loop_skips_blank_lines() -> None:
    lines = iter(["", "   ", "exit"])
    outputs: list[str] = []
    RentalCLI().run(input_fn=lambda _prompt: next(lines), output_fn=outputs.append)
    assert outputs[-1] == "Bye!"


def test_main_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", fake_eof)
    main()  # should start, hit EOF, and return cleanly


# ── _parse_date helper ────────────────────────────────────────────────

def test_parse_date_valid() -> None:
    assert _parse_date("2026-06-08") == date(2026, 6, 8)


def test_parse_date_invalid() -> None:
    with pytest.raises(ValueError, match="invalid date"):
        _parse_date("not-a-date")
