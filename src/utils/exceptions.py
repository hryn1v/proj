"""Custom exception hierarchy for the Rental Management System."""
from __future__ import annotations


class RentalSystemError(Exception):
    """Base exception for all rental system errors."""


class EntityNotFoundError(RentalSystemError):
    """Raised when a requested entity does not exist in the repository."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """Initialize with entity type and ID.

        Args:
            entity_type: Name of the entity type (e.g., 'Tenant').
            entity_id: ID of the missing entity.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class EntityAlreadyExistsError(RentalSystemError):
    """Raised when attempting to add an entity that already exists."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """Initialize with entity type and ID.

        Args:
            entity_type: Name of the entity type.
            entity_id: ID of the duplicate entity.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' already exists")


class InvalidStateTransitionError(RentalSystemError):
    """Raised when an entity state transition is not allowed."""

    def __init__(self, entity_type: str, current_state: str, target_state: str) -> None:
        """Initialize with transition details.

        Args:
            entity_type: Name of the entity type.
            current_state: Current state of the entity.
            target_state: Attempted target state.
        """
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'"
        )


class ValidationError(RentalSystemError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str) -> None:
        """Initialize with field and error message.

        Args:
            field: Name of the field that failed validation.
            message: Description of the validation error.
        """
        self.field = field
        super().__init__(f"Validation error on '{field}': {message}")


class BusinessRuleViolationError(RentalSystemError):
    """Raised when a business rule is violated."""


class TenantBlockedError(BusinessRuleViolationError):
    """Raised when a blocked tenant attempts a restricted action."""

    def __init__(self, tenant_id: str) -> None:
        """Initialize with tenant ID.

        Args:
            tenant_id: ID of the blocked tenant.
        """
        self.tenant_id = tenant_id
        super().__init__(f"Tenant '{tenant_id}' is blocked and cannot perform this action")


class SpaceNotAvailableError(BusinessRuleViolationError):
    """Raised when attempting to use a space that is not available."""

    def __init__(self, space_id: str) -> None:
        """Initialize with space ID.

        Args:
            space_id: ID of the unavailable space.
        """
        self.space_id = space_id
        super().__init__(f"Space '{space_id}' is not available")


class ContractNotActiveError(BusinessRuleViolationError):
    """Raised when an operation requires an active contract."""

    def __init__(self, contract_id: str) -> None:
        """Initialize with contract ID.

        Args:
            contract_id: ID of the non-active contract.
        """
        self.contract_id = contract_id
        super().__init__(f"Contract '{contract_id}' is not active")


class InvoiceAlreadyPaidError(BusinessRuleViolationError):
    """Raised when attempting to pay an already-paid invoice."""

    def __init__(self, invoice_id: str) -> None:
        """Initialize with invoice ID.

        Args:
            invoice_id: ID of the already-paid invoice.
        """
        self.invoice_id = invoice_id
        super().__init__(f"Invoice '{invoice_id}' has already been paid")


class DuplicateBookingError(BusinessRuleViolationError):
    """Raised when a tenant has a duplicate pending booking for a space."""

    def __init__(self, tenant_id: str, space_id: str) -> None:
        """Initialize with tenant and space IDs.

        Args:
            tenant_id: ID of the tenant.
            space_id: ID of the space.
        """
        self.tenant_id = tenant_id
        self.space_id = space_id
        super().__init__(
            f"Tenant '{tenant_id}' already has a pending booking for space '{space_id}'"
        )
