"""Unit tests for SpaceService."""
import pytest

from src.models.enums import SpaceStatus, SpaceType
from src.services.notification_service import SpaceEventPublisher, TenantNotifier
from src.utils.exceptions import EntityNotFoundError, SpaceNotAvailableError, ValidationError


class TestCreateSpace:
    def test_create_valid_space(self, space_service):
        s = space_service.create_space("Office 1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        assert s.name == "Office 1"
        assert s.type == SpaceType.OFFICE
        assert s.status == SpaceStatus.AVAILABLE

    def test_create_generates_id(self, space_service):
        s = space_service.create_space("Apt 1", SpaceType.APARTMENT, 80.0, 2, 2000.0)
        assert s.id.startswith("SPC-")

    def test_create_empty_name_raises(self, space_service):
        with pytest.raises(ValidationError):
            space_service.create_space("", SpaceType.OFFICE, 50.0, 1, 1000.0)

    def test_create_zero_area_raises(self, space_service):
        with pytest.raises(ValidationError):
            space_service.create_space("X", SpaceType.OFFICE, 0, 1, 1000.0)

    def test_create_negative_price_raises(self, space_service):
        with pytest.raises(ValidationError):
            space_service.create_space("X", SpaceType.OFFICE, 50.0, 1, -100.0)


class TestSpaceOperations:
    def test_get_space(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        fetched = space_service.get_space(s.id)
        assert fetched.id == s.id

    def test_get_nonexistent_raises(self, space_service):
        with pytest.raises(EntityNotFoundError):
            space_service.get_space("nope")

    def test_ensure_available_passes(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        result = space_service.ensure_space_available(s.id)
        assert result.is_available()

    def test_ensure_available_raises_when_occupied(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        space_service.occupy_space(s.id)
        with pytest.raises(SpaceNotAvailableError):
            space_service.ensure_space_available(s.id)

    def test_occupy_space(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        occupied = space_service.occupy_space(s.id)
        assert occupied.status == SpaceStatus.OCCUPIED

    def test_release_space(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        space_service.occupy_space(s.id)
        released = space_service.release_space(s.id)
        assert released.status == SpaceStatus.AVAILABLE

    def test_set_maintenance(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        result = space_service.set_maintenance(s.id)
        assert result.status == SpaceStatus.MAINTENANCE

    def test_reserve_space(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        result = space_service.reserve_space(s.id)
        assert result.status == SpaceStatus.RESERVED

    def test_delete_space(self, space_service):
        s = space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        assert space_service.delete_space(s.id) is True


class TestSpaceQueries:
    def test_get_available_spaces(self, space_service):
        space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        s2 = space_service.create_space("S2", SpaceType.PARKING, 15.0, 0, 200.0)
        space_service.occupy_space(s2.id)
        available = space_service.get_available_spaces()
        assert len(available) == 1

    def test_get_spaces_by_type(self, space_service):
        space_service.create_space("O1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        space_service.create_space("P1", SpaceType.PARKING, 15.0, 0, 200.0)
        offices = space_service.get_spaces_by_type(SpaceType.OFFICE)
        assert len(offices) == 1

    def test_get_spaces_by_floor(self, space_service):
        space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        space_service.create_space("S2", SpaceType.OFFICE, 60.0, 2, 1200.0)
        f1 = space_service.get_spaces_by_floor(1)
        assert len(f1) == 1

    def test_get_all_spaces(self, space_service):
        space_service.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        space_service.create_space("S2", SpaceType.PARKING, 15.0, 0, 200.0)
        assert len(space_service.get_all_spaces()) == 2


class TestSpaceEvents:
    def test_release_publishes_event(self, space_repo):
        publisher = SpaceEventPublisher()
        notifier = TenantNotifier()
        publisher.subscribe("space_available", notifier)
        from src.services.space_service import SpaceService
        svc = SpaceService(space_repo, publisher)
        s = svc.create_space("S1", SpaceType.OFFICE, 50.0, 1, 1000.0)
        svc.occupy_space(s.id)
        svc.release_space(s.id, tenant_id="T1")
        assert len(notifier.notifications) == 1
        assert notifier.notifications[0].tenant_id == "T1"
