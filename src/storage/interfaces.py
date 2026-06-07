"""Abstract repository interfaces for the Rental Management System.

Defines the generic repository contract using the Repository pattern
with Interface Segregation (separate read and write interfaces).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IReadRepository[T](ABC):
    """Interface for read-only repository operations."""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> T | None:
        """Retrieve an entity by its unique identifier.

        Args:
            entity_id: Unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.
        """

    @abstractmethod
    def get_all(self) -> list[T]:
        """Retrieve all entities from the repository.

        Returns:
            List of all entities.
        """

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists in the repository.

        Args:
            entity_id: Unique identifier to check.

        Returns:
            True if the entity exists.
        """

    @abstractmethod
    def count(self) -> int:
        """Get the total number of entities in the repository.

        Returns:
            Number of entities.
        """


class IWriteRepository[T](ABC):
    """Interface for write repository operations."""

    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity to the repository.

        Args:
            entity: Entity to add.

        Returns:
            The added entity.

        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists.
        """

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity in the repository.

        Args:
            entity: Entity with updated data.

        Returns:
            The updated entity.

        Raises:
            EntityNotFoundError: If the entity does not exist.
        """

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity from the repository.

        Args:
            entity_id: ID of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.
        """


class IRepository[T](IReadRepository[T], IWriteRepository[T], ABC):
    """Combined read-write repository interface."""
