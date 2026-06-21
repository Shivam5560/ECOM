from __future__ import annotations

from notification_service.schemas import Notification


class NotificationService:
    def __init__(self) -> None:
        self.notifications: list[Notification] = []

    def create(self, *, user_id: str, event_type: str, message: str) -> Notification:
        notification = Notification(user_id=user_id, event_type=event_type, message=message, created_by=user_id)
        self.notifications.append(notification)
        return notification
