"""Base in-memory repository implementation.

Provides a generic in-memory storage backend using a dictionary,
implementing all CRUD operations from the IRepository interface.
"""
from __future__ import annotations

from collections.abc import Callable

from src.storage.interfaces import IRepository
from src.utils.exceptions import EntityAlreadyExistsError, EntityNotFoundError


class InMemoryBaseRepository[T](IRepository[T]):
    """Generic in-memory repository using a dict as the data store.

    All entities must have an 'id' attribute of type str.

    Attributes:
        _store: Internal dictionary mapping entity IDs to entities.
        _entity_name: Human-readable name of the entity type for error messages.
    """

    def __init__(self, entity_name: str = "Entity") -> None:
        """Initialize the repository with an empty store.

        Args:
            entity_name: Name of the entity type for error messages.
        """
        self._store: dict[str, T] = {}
        self._entity_name = entity_name

    def get_by_id(self, entity_id: str) -> T | None:
        """Retrieve an entity by its unique identifier.

        Args:
            entity_id: Unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.
        """
        return self._store.get(entity_id)

    def get_all(self) -> list[T]:
        """Retrieve all entities from the repository.

        Returns:
            List of all entities.
        """
        return list(self._store.values())

    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists in the repository.

        Args:
            entity_id: Unique identifier to check.

        Returns:
            True if the entity exists.
        """
        return entity_id in self._store

    def count(self) -> int:
        """Get the total number of entities in the repository.

        Returns:
            Number of entities.
        """
        return len(self._store)

    def add(self, entity: T) -> T:
        """Add a new entity to the repository.

        Args:
            entity: Entity to add (must have an 'id' attribute).

        Returns:
            The added entity.

        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists.
        """
        entity_id = getattr(entity, "id")
        if entity_id in self._store:
            raise EntityAlreadyExistsError(self._entity_name, entity_id)
        self._store[entity_id] = entity
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity in the repository.

        Args:
            entity: Entity with updated data.

        Returns:
            The updated entity.

        Raises:
            EntityNotFoundError: If the entity does not exist.
        """
        entity_id = getattr(entity, "id")
        if entity_id not in self._store:
            raise EntityNotFoundError(self._entity_name, entity_id)
        self._store[entity_id] = entity
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete an entity from the repository.

        Args:
            entity_id: ID of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.
        """
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def clear(self) -> None:
        """Remove all entities from the repository."""
        self._store.clear()

    def find_by(self, predicate: Callable[[T], bool]) -> list[T]:
        """Find entities matching a predicate function.

        Args:
            predicate: A callable that takes an entity and returns True if it matches.

        Returns:
            List of matching entities.
        """
        return [entity for entity in self._store.values() if predicate(entity)]
