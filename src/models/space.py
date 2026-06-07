"""Space domain model."""
from __future__ import annotations

from dataclasses import dataclass

from src.models.enums import SpaceStatus, SpaceType


@dataclass
class Space:
    """Represents a rentable space in the system.

    Attributes:
        id: Unique identifier for the space.
        name: Descriptive name of the space (e.g., 'Office 301').
        type: Type of space (office, apartment, parking, warehouse).
        area_sqm: Area of the space in square meters.
        floor: Floor number where the space is located.
        price_per_month: Monthly rental price.
        status: Current availability status.
    """

    id: str
    name: str
    type: SpaceType
    area_sqm: float
    floor: int
    price_per_month: float
    status: SpaceStatus = SpaceStatus.AVAILABLE

    def is_available(self) -> bool:
        """Check if the space is currently available for rent."""
        return self.status == SpaceStatus.AVAILABLE

    def occupy(self) -> None:
        """Mark the space as occupied."""
        self.status = SpaceStatus.OCCUPIED

    def release(self) -> None:
        """Mark the space as available."""
        self.status = SpaceStatus.AVAILABLE

    def reserve(self) -> None:
        """Mark the space as reserved."""
        self.status = SpaceStatus.RESERVED

    def set_maintenance(self) -> None:
        """Put the space into maintenance mode."""
        self.status = SpaceStatus.MAINTENANCE
