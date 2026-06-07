"""Notification domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    """Represents a notification sent to a tenant.

    Used by the Observer pattern to track space availability
    and other event-driven messages.

    Attributes:
        id: Unique identifier for the notification.
        tenant_id: ID of the tenant receiving the notification.
        message: Notification message content.
        created_at: Timestamp when the notification was created.
        is_read: Whether the notification has been read.
    """

    id: str
    tenant_id: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False

    def mark_read(self) -> None:
        """Mark the notification as read."""
        self.is_read = True
