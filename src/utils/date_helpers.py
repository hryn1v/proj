"""Date helper utilities for the Rental Management System."""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta


def months_between(start: date, end: date) -> int:
    """Calculate the number of months between two dates.

    Args:
        start: Start date.
        end: End date.

    Returns:
        Number of whole months between start and end.
    """
    return (end.year - start.year) * 12 + (end.month - start.month)


def days_between(start: date, end: date) -> int:
    """Calculate the number of days between two dates.

    Args:
        start: Start date.
        end: End date.

    Returns:
        Number of days between start and end (can be negative).
    """
    return (end - start).days


def add_months(dt: date, months: int) -> date:
    """Add a number of months to a date.

    Handles month-end edge cases (e.g., Jan 31 + 1 month = Feb 28/29).

    Args:
        dt: Original date.
        months: Number of months to add (can be negative).

    Returns:
        New date with the specified months added.
    """
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_days(dt: date, days: int) -> date:
    """Add a number of days to a date.

    Args:
        dt: Original date.
        days: Number of days to add (can be negative).

    Returns:
        New date with the specified days added.
    """
    return dt + timedelta(days=days)


def is_overdue(due_date: date, current_date: date | None = None) -> bool:
    """Check if a due date has passed.

    Args:
        due_date: The deadline date to check.
        current_date: Date to compare against. Defaults to today.

    Returns:
        True if the current date is past the due date.
    """
    check_date = current_date or date.today()
    return check_date > due_date


def get_current_date() -> date:
    """Get today's date.

    Returns:
        Current date.
    """
    return date.today()


def get_current_datetime() -> datetime:
    """Get the current datetime.

    Returns:
        Current datetime.
    """
    return datetime.now()


def date_range_overlaps(
    start1: date, end1: date, start2: date, end2: date
) -> bool:
    """Check if two date ranges overlap.

    Args:
        start1: Start of first range.
        end1: End of first range.
        start2: Start of second range.
        end2: End of second range.

    Returns:
        True if the ranges overlap.
    """
    return start1 <= end2 and start2 <= end1
