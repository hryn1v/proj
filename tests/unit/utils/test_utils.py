"""Unit tests for utility modules."""
import pytest
from datetime import date, datetime
from src.utils.validators import (
    validate_email, validate_phone, validate_date_range,
    validate_positive_amount, validate_non_negative_amount, validate_non_empty_string,
)
from src.utils.date_helpers import (
    months_between, days_between, add_months, add_days,
    is_overdue, date_range_overlaps,
)
from src.utils.id_generator import generate_id, generate_prefixed_id
from src.utils.exceptions import (
    EntityNotFoundError, EntityAlreadyExistsError, InvalidStateTransitionError,
    ValidationError, TenantBlockedError, SpaceNotAvailableError,
)


# ─── Validator Tests ───────────────────────────────────────────────────

class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("test@example.com") is True

    def test_valid_email_with_dots(self):
        assert validate_email("user.name@domain.co.uk") is True

    def test_invalid_no_at(self):
        assert validate_email("notanemail") is False

    def test_invalid_no_domain(self):
        assert validate_email("user@") is False

    def test_empty_string(self):
        assert validate_email("") is False


class TestValidatePhone:
    def test_valid_phone(self):
        assert validate_phone("+380501234567") is True

    def test_valid_phone_no_plus(self):
        assert validate_phone("380501234567") is True

    def test_valid_with_spaces(self):
        assert validate_phone("+380 50 123 4567") is True

    def test_too_short(self):
        assert validate_phone("123") is False

    def test_empty(self):
        assert validate_phone("") is False


class TestValidateDateRange:
    def test_valid_range(self):
        assert validate_date_range(date(2025, 1, 1), date(2025, 12, 31)) is True

    def test_same_dates(self):
        assert validate_date_range(date(2025, 1, 1), date(2025, 1, 1)) is False

    def test_inverted_range(self):
        assert validate_date_range(date(2025, 12, 31), date(2025, 1, 1)) is False


class TestValidateAmounts:
    def test_positive(self):
        assert validate_positive_amount(100.0) is True

    def test_zero_not_positive(self):
        assert validate_positive_amount(0) is False

    def test_negative_not_positive(self):
        assert validate_positive_amount(-1) is False

    def test_non_negative_zero(self):
        assert validate_non_negative_amount(0) is True

    def test_non_negative_positive(self):
        assert validate_non_negative_amount(10.0) is True

    def test_non_negative_negative(self):
        assert validate_non_negative_amount(-0.01) is False


class TestValidateString:
    def test_non_empty(self):
        assert validate_non_empty_string("hello") is True

    def test_empty(self):
        assert validate_non_empty_string("") is False

    def test_whitespace_only(self):
        assert validate_non_empty_string("   ") is False


# ─── Date Helper Tests ─────────────────────────────────────────────────

class TestMonthsBetween:
    def test_same_month(self):
        assert months_between(date(2025, 1, 1), date(2025, 1, 31)) == 0

    def test_one_year(self):
        assert months_between(date(2025, 1, 1), date(2026, 1, 1)) == 12

    def test_six_months(self):
        assert months_between(date(2025, 1, 1), date(2025, 7, 1)) == 6


class TestDaysBetween:
    def test_same_day(self):
        assert days_between(date(2025, 1, 1), date(2025, 1, 1)) == 0

    def test_ten_days(self):
        assert days_between(date(2025, 1, 1), date(2025, 1, 11)) == 10

    def test_negative(self):
        assert days_between(date(2025, 1, 11), date(2025, 1, 1)) == -10


class TestAddMonths:
    def test_add_one_month(self):
        assert add_months(date(2025, 1, 15), 1) == date(2025, 2, 15)

    def test_add_twelve_months(self):
        assert add_months(date(2025, 1, 1), 12) == date(2026, 1, 1)

    def test_month_end_overflow(self):
        # Jan 31 + 1 month -> Feb 28
        result = add_months(date(2025, 1, 31), 1)
        assert result == date(2025, 2, 28)

    def test_leap_year(self):
        result = add_months(date(2024, 1, 31), 1)
        assert result == date(2024, 2, 29)


class TestAddDays:
    def test_add_positive(self):
        assert add_days(date(2025, 1, 1), 10) == date(2025, 1, 11)

    def test_add_negative(self):
        assert add_days(date(2025, 1, 11), -10) == date(2025, 1, 1)


class TestIsOverdue:
    def test_overdue(self):
        assert is_overdue(date(2024, 1, 1), date(2025, 1, 1)) is True

    def test_not_overdue(self):
        assert is_overdue(date(2026, 12, 31), date(2025, 1, 1)) is False

    def test_on_due_date(self):
        assert is_overdue(date(2025, 1, 1), date(2025, 1, 1)) is False


class TestDateRangeOverlaps:
    def test_overlapping(self):
        assert date_range_overlaps(
            date(2025, 1, 1), date(2025, 6, 1),
            date(2025, 3, 1), date(2025, 9, 1),
        ) is True

    def test_adjacent_not_overlapping(self):
        # end1 == start2, they touch but by our definition this is overlap
        assert date_range_overlaps(
            date(2025, 1, 1), date(2025, 3, 1),
            date(2025, 3, 1), date(2025, 6, 1),
        ) is True

    def test_non_overlapping(self):
        assert date_range_overlaps(
            date(2025, 1, 1), date(2025, 3, 1),
            date(2025, 4, 1), date(2025, 6, 1),
        ) is False


# ─── ID Generator Tests ───────────────────────────────────────────────

class TestIdGenerator:
    def test_generate_id_is_string(self):
        assert isinstance(generate_id(), str)

    def test_generate_id_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_prefixed_id(self):
        pid = generate_prefixed_id("TNT")
        assert pid.startswith("TNT-")
        assert len(pid) > 4

    def test_prefixed_ids_unique(self):
        ids = {generate_prefixed_id("SPC") for _ in range(100)}
        assert len(ids) == 100


# ─── Exception Tests ──────────────────────────────────────────────────

class TestExceptions:
    def test_entity_not_found(self):
        e = EntityNotFoundError("Tenant", "123")
        assert "Tenant" in str(e)
        assert "123" in str(e)
        assert e.entity_type == "Tenant"
        assert e.entity_id == "123"

    def test_entity_already_exists(self):
        e = EntityAlreadyExistsError("Space", "456")
        assert "Space" in str(e)
        assert e.entity_id == "456"

    def test_invalid_state_transition(self):
        e = InvalidStateTransitionError("Contract", "draft", "terminated")
        assert "draft" in str(e)
        assert "terminated" in str(e)

    def test_validation_error(self):
        e = ValidationError("email", "invalid format")
        assert "email" in str(e)
        assert e.field == "email"

    def test_tenant_blocked(self):
        e = TenantBlockedError("T1")
        assert "T1" in str(e)
        assert e.tenant_id == "T1"

    def test_space_not_available(self):
        e = SpaceNotAvailableError("S1")
        assert "S1" in str(e)
