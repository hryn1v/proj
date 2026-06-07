"""Tenant management service."""
from __future__ import annotations

from src.models.enums import TenantStatus
from src.models.tenant import Tenant
from src.storage.tenant_repository import ITenantRepository
from src.utils.exceptions import (
    EntityNotFoundError,
    TenantBlockedError,
    ValidationError,
)
from src.utils.id_generator import generate_prefixed_id
from src.utils.validators import validate_email, validate_non_empty_string, validate_phone


class TenantService:
    """Service for managing tenant lifecycle and operations.

    Handles tenant registration, updates, blocking, and queries.
    Enforces business rules like automatic blocking after 3 violations.

    Attributes:
        _tenant_repo: Repository for tenant persistence.
        _max_violations: Threshold for automatic blocking.
    """

    MAX_VIOLATIONS_BEFORE_BLOCK = 3

    def __init__(self, tenant_repo: ITenantRepository) -> None:
        """Initialize with a tenant repository.

        Args:
            tenant_repo: Repository implementing ITenantRepository.
        """
        self._tenant_repo = tenant_repo

    def register_tenant(self, name: str, email: str, phone: str) -> Tenant:
        """Register a new tenant in the system.

        Args:
            name: Full name of the tenant.
            email: Contact email address.
            phone: Contact phone number.

        Returns:
            The newly created tenant.

        Raises:
            ValidationError: If input validation fails.
            EntityAlreadyExistsError: If email is already registered.
        """
        if not validate_non_empty_string(name):
            raise ValidationError("name", "Name cannot be empty")
        if not validate_email(email):
            raise ValidationError("email", "Invalid email format")
        if not validate_phone(phone):
            raise ValidationError("phone", "Invalid phone format")

        existing = self._tenant_repo.find_by_email(email)
        if existing:
            raise ValidationError("email", f"Email '{email}' is already registered")

        tenant = Tenant(
            id=generate_prefixed_id("TNT"),
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
        )
        return self._tenant_repo.add(tenant)

    def get_tenant(self, tenant_id: str) -> Tenant:
        """Retrieve a tenant by ID.

        Args:
            tenant_id: Unique identifier of the tenant.

        Returns:
            The tenant.

        Raises:
            EntityNotFoundError: If the tenant does not exist.
        """
        tenant = self._tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            raise EntityNotFoundError("Tenant", tenant_id)
        return tenant

    def update_tenant(self, tenant_id: str, name: str | None = None,
                      email: str | None = None, phone: str | None = None) -> Tenant:
        """Update tenant information.

        Args:
            tenant_id: ID of the tenant to update.
            name: New name (optional).
            email: New email (optional).
            phone: New phone (optional).

        Returns:
            Updated tenant.

        Raises:
            EntityNotFoundError: If tenant not found.
            ValidationError: If new values are invalid.
        """
        tenant = self.get_tenant(tenant_id)

        if name is not None:
            if not validate_non_empty_string(name):
                raise ValidationError("name", "Name cannot be empty")
            tenant.name = name.strip()

        if email is not None:
            if not validate_email(email):
                raise ValidationError("email", "Invalid email format")
            existing = self._tenant_repo.find_by_email(email)
            if existing and existing.id != tenant_id:
                raise ValidationError("email", f"Email '{email}' is already registered")
            tenant.email = email.strip().lower()

        if phone is not None:
            if not validate_phone(phone):
                raise ValidationError("phone", "Invalid phone format")
            tenant.phone = phone.strip()

        return self._tenant_repo.update(tenant)

    def add_violation(self, tenant_id: str) -> Tenant:
        """Record a violation for a tenant and auto-block if threshold reached.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            Updated tenant (possibly blocked).

        Raises:
            EntityNotFoundError: If tenant not found.
        """
        tenant = self.get_tenant(tenant_id)
        tenant.add_violation()

        if tenant.violation_count >= self.MAX_VIOLATIONS_BEFORE_BLOCK:
            tenant.block()

        return self._tenant_repo.update(tenant)

    def block_tenant(self, tenant_id: str) -> Tenant:
        """Manually block a tenant.

        Args:
            tenant_id: ID of the tenant to block.

        Returns:
            The blocked tenant.

        Raises:
            EntityNotFoundError: If tenant not found.
        """
        tenant = self.get_tenant(tenant_id)
        tenant.block()
        return self._tenant_repo.update(tenant)

    def activate_tenant(self, tenant_id: str) -> Tenant:
        """Reactivate a blocked or inactive tenant.

        Args:
            tenant_id: ID of the tenant to activate.

        Returns:
            The reactivated tenant.

        Raises:
            EntityNotFoundError: If tenant not found.
        """
        tenant = self.get_tenant(tenant_id)
        tenant.activate()
        return self._tenant_repo.update(tenant)

    def ensure_tenant_active(self, tenant_id: str) -> Tenant:
        """Verify a tenant exists and is active (not blocked).

        Args:
            tenant_id: ID of the tenant.

        Returns:
            The active tenant.

        Raises:
            EntityNotFoundError: If tenant not found.
            TenantBlockedError: If tenant is blocked.
        """
        tenant = self.get_tenant(tenant_id)
        if tenant.is_blocked():
            raise TenantBlockedError(tenant_id)
        return tenant

    def get_all_tenants(self) -> list[Tenant]:
        """Get all tenants in the system.

        Returns:
            List of all tenants.
        """
        return self._tenant_repo.get_all()

    def get_active_tenants(self) -> list[Tenant]:
        """Get all active tenants.

        Returns:
            List of active tenants.
        """
        return self._tenant_repo.find_active()

    def get_blocked_tenants(self) -> list[Tenant]:
        """Get all blocked tenants.

        Returns:
            List of blocked tenants.
        """
        return self._tenant_repo.find_by_status(TenantStatus.BLOCKED)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant from the system.

        Args:
            tenant_id: ID of the tenant to delete.

        Returns:
            True if deleted successfully.

        Raises:
            EntityNotFoundError: If tenant not found.
        """
        self.get_tenant(tenant_id)
        return self._tenant_repo.delete(tenant_id)
