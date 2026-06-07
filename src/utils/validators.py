"""Input validation utilities for the Rental Management System."""
from __future__ import annotations

import re
from datetime import date


def validate_email(email: str) -> bool:
    """Validate an email address format using regex.

    Args:
        email: Email address string to validate.

    Returns:
        True if the email format is valid.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate a phone number format.

    Accepts digits with optional leading '+' and minimum 7 digits.

    Args:
        phone: Phone number string to validate.

    Returns:
        True if the phone format is valid.
    """
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    pattern = r"^\+?\d{7,15}$"
    return bool(re.match(pattern, cleaned))


def validate_date_range(start: date, end: date) -> bool:
    """Validate that a start date is before an end date.

    Args:
        start: Start date of the range.
        end: End date of the range.

    Returns:
        True if start is strictly before end.
    """
    return start < end


def validate_positive_amount(amount: float) -> bool:
    """Validate that an amount is strictly positive.

    Args:
        amount: Financial amount to validate.

    Returns:
        True if amount is greater than zero.
    """
    return amount > 0


def validate_non_negative_amount(amount: float) -> bool:
    """Validate that an amount is non-negative.

    Args:
        amount: Financial amount to validate.

    Returns:
        True if amount is greater than or equal to zero.
    """
    return amount >= 0


def validate_non_empty_string(value: str) -> bool:
    """Validate that a string is not empty or whitespace-only.

    Args:
        value: String value to validate.

    Returns:
        True if the string contains non-whitespace characters.
    """
    return bool(value and value.strip())
