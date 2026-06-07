"""Unit tests for the Space model."""
import pytest
from src.models.space import Space
from src.models.enums import SpaceStatus, SpaceType
from tests.conftest import make_space


class TestSpaceCreation:
    def test_create_space_with_defaults(self):
        space = make_space()
        assert space.id == "SPC-test001"
        assert space.name == "Office 101"
        assert space.type == SpaceType.OFFICE
        assert space.status == SpaceStatus.AVAILABLE

    def test_create_apartment(self):
        space = make_space(type=SpaceType.APARTMENT, name="Apt 201")
        assert space.type == SpaceType.APARTMENT

    def test_create_parking(self):
        space = make_space(type=SpaceType.PARKING, area_sqm=15.0)
        assert space.type == SpaceType.PARKING
        assert space.area_sqm == 15.0

    def test_create_warehouse(self):
        space = make_space(type=SpaceType.WAREHOUSE, floor=0)
        assert space.type == SpaceType.WAREHOUSE


class TestSpaceStatus:
    def test_is_available_when_available(self):
        space = make_space()
        assert space.is_available() is True

    def test_is_not_available_when_occupied(self):
        space = make_space(status=SpaceStatus.OCCUPIED)
        assert space.is_available() is False

    def test_occupy_space(self):
        space = make_space()
        space.occupy()
        assert space.status == SpaceStatus.OCCUPIED
        assert space.is_available() is False

    def test_release_space(self):
        space = make_space(status=SpaceStatus.OCCUPIED)
        space.release()
        assert space.status == SpaceStatus.AVAILABLE

    def test_reserve_space(self):
        space = make_space()
        space.reserve()
        assert space.status == SpaceStatus.RESERVED

    def test_set_maintenance(self):
        space = make_space()
        space.set_maintenance()
        assert space.status == SpaceStatus.MAINTENANCE
        assert space.is_available() is False
