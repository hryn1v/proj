"""Space management service."""
from __future__ import annotations

from src.models.enums import SpaceType
from src.models.space import Space
from src.services.notification_service import SpaceEventPublisher
from src.storage.space_repository import ISpaceRepository
from src.utils.exceptions import (
    EntityNotFoundError,
    SpaceNotAvailableError,
    ValidationError,
)
from src.utils.id_generator import generate_prefixed_id
from src.utils.validators import validate_non_empty_string, validate_positive_amount


class SpaceService:
    """Service for managing rentable spaces.

    Handles space creation, status transitions, availability checks,
    and publishes events via the Observer pattern when spaces become available.

    Attributes:
        _space_repo: Repository for space persistence.
        _event_publisher: Optional event publisher for Observer pattern.
    """

    def __init__(
        self,
        space_repo: ISpaceRepository,
        event_publisher: SpaceEventPublisher | None = None,
    ) -> None:
        """Initialize with a space repository and optional event publisher.

        Args:
            space_repo: Repository implementing ISpaceRepository.
            event_publisher: Optional publisher for space events.
        """
        self._space_repo = space_repo
        self._event_publisher = event_publisher

    def create_space(
        self,
        name: str,
        space_type: SpaceType,
        area_sqm: float,
        floor: int,
        price_per_month: float,
    ) -> Space:
        """Create a new rentable space.

        Args:
            name: Descriptive name for the space.
            space_type: Type of space.
            area_sqm: Area in square meters.
            floor: Floor number.
            price_per_month: Monthly rental price.

        Returns:
            The newly created space.

        Raises:
            ValidationError: If input validation fails.
        """
        if not validate_non_empty_string(name):
            raise ValidationError("name", "Name cannot be empty")
        if not validate_positive_amount(area_sqm):
            raise ValidationError("area_sqm", "Area must be positive")
        if not validate_positive_amount(price_per_month):
            raise ValidationError("price_per_month", "Price must be positive")

        space = Space(
            id=generate_prefixed_id("SPC"),
            name=name.strip(),
            type=space_type,
            area_sqm=area_sqm,
            floor=floor,
            price_per_month=price_per_month,
        )
        return self._space_repo.add(space)

    def get_space(self, space_id: str) -> Space:
        """Retrieve a space by ID.

        Args:
            space_id: Unique identifier of the space.

        Returns:
            The space.

        Raises:
            EntityNotFoundError: If the space does not exist.
        """
        space = self._space_repo.get_by_id(space_id)
        if space is None:
            raise EntityNotFoundError("Space", space_id)
        return space

    def ensure_space_available(self, space_id: str) -> Space:
        """Verify a space exists and is available.

        Args:
            space_id: ID of the space.

        Returns:
            The available space.

        Raises:
            EntityNotFoundError: If space not found.
            SpaceNotAvailableError: If space is not available.
        """
        space = self.get_space(space_id)
        if not space.is_available():
            raise SpaceNotAvailableError(space_id)
        return space

    def occupy_space(self, space_id: str) -> Space:
        """Mark a space as occupied.

        Args:
            space_id: ID of the space to occupy.

        Returns:
            Updated space.

        Raises:
            EntityNotFoundError: If space not found.
        """
        space = self.get_space(space_id)
        space.occupy()
        return self._space_repo.update(space)

    def release_space(self, space_id: str, **event_kwargs: object) -> Space:
        """Release a space back to available status and publish event.

        Args:
            space_id: ID of the space to release.
            **event_kwargs: Additional data for the space_available event.

        Returns:
            Updated space.

        Raises:
            EntityNotFoundError: If space not found.
        """
        space = self.get_space(space_id)
        space.release()
        updated = self._space_repo.update(space)

        if self._event_publisher:
            self._event_publisher.publish("space_available", updated, **event_kwargs)

        return updated

    def set_maintenance(self, space_id: str) -> Space:
        """Put a space into maintenance mode.

        Args:
            space_id: ID of the space.

        Returns:
            Updated space.
        """
        space = self.get_space(space_id)
        space.set_maintenance()
        return self._space_repo.update(space)

    def reserve_space(self, space_id: str) -> Space:
        """Mark a space as reserved.

        Args:
            space_id: ID of the space.

        Returns:
            Updated space.
        """
        space = self.get_space(space_id)
        space.reserve()
        return self._space_repo.update(space)

    def get_available_spaces(self) -> list[Space]:
        """Get all available spaces.

        Returns:
            List of available spaces.
        """
        return self._space_repo.find_available()

    def get_spaces_by_type(self, space_type: SpaceType) -> list[Space]:
        """Get all spaces of a given type.

        Args:
            space_type: Type to filter by.

        Returns:
            List of matching spaces.
        """
        return self._space_repo.find_by_type(space_type)

    def get_spaces_by_floor(self, floor: int) -> list[Space]:
        """Get all spaces on a given floor.

        Args:
            floor: Floor number.

        Returns:
            List of spaces on the floor.
        """
        return self._space_repo.find_by_floor(floor)

    def get_all_spaces(self) -> list[Space]:
        """Get all spaces in the system.

        Returns:
            List of all spaces.
        """
        return self._space_repo.get_all()

    def delete_space(self, space_id: str) -> bool:
        """Delete a space.

        Args:
            space_id: ID of the space to delete.

        Returns:
            True if deleted.

        Raises:
            EntityNotFoundError: If space not found.
        """
        self.get_space(space_id)
        return self._space_repo.delete(space_id)
