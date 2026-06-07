"""Unit tests for TenantService."""
import pytest

from src.models.enums import TenantStatus
from src.utils.exceptions import (
    EntityNotFoundError,
    TenantBlockedError,
    ValidationError,
)


class TestRegisterTenant:
    def test_register_valid_tenant(self, tenant_service):
        t = tenant_service.register_tenant("Alice", "alice@example.com", "+380501111111")
        assert t.name == "Alice"
        assert t.email == "alice@example.com"
        assert t.status == TenantStatus.ACTIVE

    def test_register_strips_whitespace(self, tenant_service):
        t = tenant_service.register_tenant("  Bob  ", "bob@example.com", "+380502222222")
        assert t.name == "Bob"

    def test_register_lowercases_email(self, tenant_service):
        t = tenant_service.register_tenant("Carl", "CARL@Example.COM", "+380503333333")
        assert t.email == "carl@example.com"

    def test_register_empty_name_raises(self, tenant_service):
        with pytest.raises(ValidationError):
            tenant_service.register_tenant("", "a@b.com", "+380501111111")

    def test_register_invalid_email_raises(self, tenant_service):
        with pytest.raises(ValidationError):
            tenant_service.register_tenant("Dave", "not-an-email", "+380501111111")

    def test_register_invalid_phone_raises(self, tenant_service):
        with pytest.raises(ValidationError):
            tenant_service.register_tenant("Eve", "eve@example.com", "123")

    def test_register_duplicate_email_raises(self, tenant_service):
        tenant_service.register_tenant("F1", "same@example.com", "+380501111111")
        with pytest.raises(ValidationError):
            tenant_service.register_tenant("F2", "same@example.com", "+380502222222")

    def test_register_generates_id(self, tenant_service):
        t = tenant_service.register_tenant("Gina", "gina@example.com", "+380504444444")
        assert t.id.startswith("TNT-")


class TestGetTenant:
    def test_get_existing_tenant(self, tenant_service):
        created = tenant_service.register_tenant("Test", "test@test.com", "+380501234567")
        fetched = tenant_service.get_tenant(created.id)
        assert fetched.id == created.id

    def test_get_nonexistent_raises(self, tenant_service):
        with pytest.raises(EntityNotFoundError):
            tenant_service.get_tenant("nonexistent")


class TestUpdateTenant:
    def test_update_name(self, tenant_service):
        t = tenant_service.register_tenant("Old", "old@test.com", "+380501234567")
        updated = tenant_service.update_tenant(t.id, name="New")
        assert updated.name == "New"

    def test_update_email(self, tenant_service):
        t = tenant_service.register_tenant("Test", "old@test.com", "+380501234567")
        updated = tenant_service.update_tenant(t.id, email="new@test.com")
        assert updated.email == "new@test.com"

    def test_update_phone(self, tenant_service):
        t = tenant_service.register_tenant("Test", "t@t.com", "+380501234567")
        updated = tenant_service.update_tenant(t.id, phone="+380509999999")
        assert updated.phone == "+380509999999"

    def test_update_invalid_email_raises(self, tenant_service):
        t = tenant_service.register_tenant("Test", "t@t.com", "+380501234567")
        with pytest.raises(ValidationError):
            tenant_service.update_tenant(t.id, email="bad")

    def test_update_duplicate_email_raises(self, tenant_service):
        tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        with pytest.raises(ValidationError):
            tenant_service.update_tenant(t2.id, email="a@t.com")

    def test_update_same_email_allowed(self, tenant_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        updated = tenant_service.update_tenant(t.id, email="a@t.com")
        assert updated.email == "a@t.com"


class TestViolationsAndBlocking:
    def test_add_violation_increments(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        updated = tenant_service.add_violation(t.id)
        assert updated.violation_count == 1

    def test_auto_block_after_3_violations(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        for _ in range(3):
            t = tenant_service.add_violation(t.id)
        assert t.is_blocked() is True

    def test_manual_block(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        blocked = tenant_service.block_tenant(t.id)
        assert blocked.is_blocked() is True

    def test_activate_blocked_tenant(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        tenant_service.block_tenant(t.id)
        activated = tenant_service.activate_tenant(t.id)
        assert activated.is_active() is True
        assert activated.violation_count == 0

    def test_ensure_active_passes_for_active(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        result = tenant_service.ensure_tenant_active(t.id)
        assert result.is_active() is True

    def test_ensure_active_raises_for_blocked(self, tenant_service):
        t = tenant_service.register_tenant("V", "v@t.com", "+380501111111")
        tenant_service.block_tenant(t.id)
        with pytest.raises(TenantBlockedError):
            tenant_service.ensure_tenant_active(t.id)


class TestTenantQueries:
    def test_get_all_tenants(self, tenant_service):
        tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        assert len(tenant_service.get_all_tenants()) == 2

    def test_get_active_tenants(self, tenant_service):
        tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        t2 = tenant_service.register_tenant("B", "b@t.com", "+380502222222")
        tenant_service.block_tenant(t2.id)
        active = tenant_service.get_active_tenants()
        assert len(active) == 1

    def test_get_blocked_tenants(self, tenant_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        tenant_service.block_tenant(t.id)
        blocked = tenant_service.get_blocked_tenants()
        assert len(blocked) == 1

    def test_delete_tenant(self, tenant_service):
        t = tenant_service.register_tenant("A", "a@t.com", "+380501111111")
        assert tenant_service.delete_tenant(t.id) is True
        with pytest.raises(EntityNotFoundError):
            tenant_service.get_tenant(t.id)
