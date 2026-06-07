"""Unit tests for the Tenant model."""
import pytest
from src.models.tenant import Tenant
from src.models.enums import TenantStatus
from tests.conftest import make_tenant


class TestTenantCreation:
    """Tests for tenant creation and default values."""

    def test_create_tenant_with_defaults(self):
        tenant = make_tenant()
        assert tenant.id == "TNT-test001"
        assert tenant.name == "John Doe"
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.violation_count == 0

    def test_create_tenant_with_custom_values(self):
        tenant = make_tenant(id="TNT-custom", name="Jane", email="jane@test.com")
        assert tenant.id == "TNT-custom"
        assert tenant.name == "Jane"
        assert tenant.email == "jane@test.com"

    def test_tenant_registered_at_is_set(self):
        tenant = make_tenant()
        assert tenant.registered_at is not None


class TestTenantStatus:
    """Tests for tenant status transitions."""

    def test_is_active_when_active(self):
        tenant = make_tenant(status=TenantStatus.ACTIVE)
        assert tenant.is_active() is True
        assert tenant.is_blocked() is False

    def test_is_blocked_when_blocked(self):
        tenant = make_tenant(status=TenantStatus.BLOCKED)
        assert tenant.is_blocked() is True
        assert tenant.is_active() is False

    def test_block_tenant(self):
        tenant = make_tenant()
        tenant.block()
        assert tenant.status == TenantStatus.BLOCKED
        assert tenant.is_blocked() is True

    def test_activate_tenant(self):
        tenant = make_tenant(status=TenantStatus.BLOCKED, violation_count=5)
        tenant.activate()
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.violation_count == 0

    def test_deactivate_tenant(self):
        tenant = make_tenant()
        tenant.deactivate()
        assert tenant.status == TenantStatus.INACTIVE


class TestTenantViolations:
    """Tests for violation tracking."""

    def test_add_violation(self):
        tenant = make_tenant()
        tenant.add_violation()
        assert tenant.violation_count == 1

    def test_add_multiple_violations(self):
        tenant = make_tenant()
        for _ in range(5):
            tenant.add_violation()
        assert tenant.violation_count == 5

    def test_activate_resets_violations(self):
        tenant = make_tenant(violation_count=3)
        tenant.activate()
        assert tenant.violation_count == 0
