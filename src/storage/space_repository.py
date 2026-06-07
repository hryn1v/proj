"""Space repository interface and in-memory implementation."""
from __future__ import annotations

from abc import abstractmethod

from src.models.enums import SpaceStatus, SpaceType
from src.models.space import Space
from src.storage.base_repository import InMemoryBaseRepository
from src.storage.interfaces import IRepository


class ISpaceRepository(IRepository[Space]):
    """Interface for space-specific repository operations."""

    @abstractmethod
    def find_by_type(self, space_type: SpaceType) -> list[Space]:
        """Find all spaces of a given type."""

    @abstractmethod
    def find_available(self) -> list[Space]:
        """Find all available spaces."""

    @abstractmethod
    def find_by_status(self, status: SpaceStatus) -> list[Space]:
        """Find all spaces with a given status."""

    @abstractmethod
    def find_by_floor(self, floor: int) -> list[Space]:
        """Find all spaces on a given floor."""


class InMemorySpaceRepository(InMemoryBaseRepository[Space], ISpaceRepository):
    """In-memory implementation of the space repository."""

    def __init__(self) -> None:
        """Initialize the space repository."""
        super().__init__(entity_name="Space")

    def find_by_type(self, space_type: SpaceType) -> list[Space]:
        """Find all spaces of a given type.

        Args:
            space_type: Type of space to filter by.

        Returns:
            List of matching spaces.
        """
        return self.find_by(lambda s: s.type == space_type)

    def find_available(self) -> list[Space]:
        """Find all available spaces.

        Returns:
            List of available spaces.
        """
        return self.find_by(lambda s: s.status == SpaceStatus.AVAILABLE)

    def find_by_status(self, status: SpaceStatus) -> list[Space]:
        """Find all spaces with a given status.

        Args:
            status: Space status to filter by.

        Returns:
            List of spaces with the specified status.
        """
        return self.find_by(lambda s: s.status == status)

    def find_by_floor(self, floor: int) -> list[Space]:
        """Find all spaces on a given floor.

        Args:
            floor: Floor number to filter by.

        Returns:
            List of spaces on the specified floor.
        """
        return self.find_by(lambda s: s.floor == floor)
