"""Notification service using the Observer Pattern (GoF).

Implements a publish-subscribe event system where:
- SpaceEventPublisher manages event subscriptions and dispatching
- SpaceEventSubscriber is the abstract observer interface
- BookingQueueNotifier auto-confirms top-priority bookings
- TenantNotifier logs notifications for tenants
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from src.models.notification import Notification
from src.models.space import Space
from src.utils.id_generator import generate_prefixed_id


class SpaceEventSubscriber(ABC):
    """Abstract observer interface for space-related events."""

    @abstractmethod
    def on_event(self, event_type: str, space: Space, **kwargs: object) -> None:
        """Handle a space event notification.

        Args:
            event_type: Type of event (e.g., 'space_available', 'space_occupied').
            space: The space involved in the event.
            **kwargs: Additional event-specific data.
        """


class SpaceEventPublisher:
    """Event publisher for the Observer pattern.

    Manages subscriptions and dispatches events to all registered
    subscribers for each event type.

    Attributes:
        _subscribers: Mapping of event types to subscriber lists.
    """

    def __init__(self) -> None:
        """Initialize with empty subscriber registry."""
        self._subscribers: dict[str, list[SpaceEventSubscriber]] = defaultdict(list)

    def subscribe(self, event_type: str, subscriber: SpaceEventSubscriber) -> None:
        """Register a subscriber for a specific event type.

        Args:
            event_type: Type of event to subscribe to.
            subscriber: Observer to notify when the event occurs.
        """
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: str, subscriber: SpaceEventSubscriber) -> None:
        """Remove a subscriber from a specific event type.

        Args:
            event_type: Type of event to unsubscribe from.
            subscriber: Observer to remove.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                s for s in self._subscribers[event_type] if s is not subscriber
            ]

    def publish(self, event_type: str, space: Space, **kwargs: object) -> None:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event being published.
            space: The space involved in the event.
            **kwargs: Additional event-specific data.
        """
        for subscriber in self._subscribers.get(event_type, []):
            subscriber.on_event(event_type, space, **kwargs)

    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for a given event type.

        Args:
            event_type: Event type to check.

        Returns:
            Number of subscribers.
        """
        return len(self._subscribers.get(event_type, []))


class BookingQueueNotifier(SpaceEventSubscriber):
    """Observer that auto-confirms the top booking when a space becomes available.

    Works with the booking repository to find the highest-priority
    pending booking and confirm it automatically.
    """

    def __init__(self, booking_repository: object) -> None:
        """Initialize with a booking repository.

        Args:
            booking_repository: Repository implementing IBookingRepository.
        """
        self._booking_repo = booking_repository
        self.last_confirmed_booking_id: str | None = None

    def on_event(self, event_type: str, space: Space, **kwargs: object) -> None:
        """Handle space available event by confirming top booking.

        Args:
            event_type: Type of event.
            space: The space that became available.
            **kwargs: Additional event data.
        """
        if event_type == "space_available":
            pending = self._booking_repo.find_pending_for_space(space.id)
            if pending:
                top_booking = pending[0]
                top_booking.confirm()
                self._booking_repo.update(top_booking)
                self.last_confirmed_booking_id = top_booking.id


class TenantNotifier(SpaceEventSubscriber):
    """Observer that creates notifications for tenants about space events.

    Stores notifications in a list for later retrieval.
    """

    def __init__(self) -> None:
        """Initialize with an empty notifications list."""
        self.notifications: list[Notification] = []

    def on_event(self, event_type: str, space: Space, **kwargs: object) -> None:
        """Handle space event by creating a tenant notification.

        Args:
            event_type: Type of event.
            space: The space involved.
            **kwargs: Must include 'tenant_id' for the target tenant.
        """
        tenant_id = kwargs.get("tenant_id", "")
        if tenant_id:
            notification = Notification(
                id=generate_prefixed_id("NTF"),
                tenant_id=str(tenant_id),
                message=f"Space '{space.name}' event: {event_type}",
            )
            self.notifications.append(notification)

    def get_notifications_for_tenant(self, tenant_id: str) -> list[Notification]:
        """Get all notifications for a specific tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            List of notifications for the tenant.
        """
        return [n for n in self.notifications if n.tenant_id == tenant_id]

    def get_unread_count(self, tenant_id: str) -> int:
        """Get the count of unread notifications for a tenant.

        Args:
            tenant_id: ID of the tenant.

        Returns:
            Number of unread notifications.
        """
        return sum(
            1
            for n in self.notifications
            if n.tenant_id == tenant_id and not n.is_read
        )
