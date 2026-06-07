"""ID generation utilities for the Rental Management System."""
from __future__ import annotations

import uuid


def generate_id() -> str:
    """Generate a unique identifier using UUID4.

    Returns:
        A UUID4 string identifier.
    """
    return str(uuid.uuid4())


def generate_prefixed_id(prefix: str) -> str:
    """Generate a unique identifier with a descriptive prefix.

    Args:
        prefix: Short prefix for the ID (e.g., 'TNT', 'SPC', 'CTR').

    Returns:
        A prefixed UUID4 string (e.g., 'TNT-a1b2c3d4...').
    """
    return f"{prefix}-{uuid.uuid4().hex[:12]}"
