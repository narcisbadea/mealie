import datetime
import json
from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict, Field

from mealie.schema._mealie import MealieModel

if TYPE_CHECKING:
    from mealie.db.models.users.in_app_notification import InAppNotificationModel


class InAppNotificationCreate(MealieModel):
    """Schema for creating an in-app notification."""

    user_id: str
    title: str
    message: str
    notification_type: str
    data: dict[str, Any] | None = None


class InAppNotificationOut(MealieModel):
    """Schema for outputting an in-app notification."""

    id: str
    title: str
    message: str
    notification_type: str
    data: dict[str, Any] | None = None
    created_at: datetime.datetime
    read_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model: "InAppNotificationModel") -> "InAppNotificationOut":  # type: ignore
        """Create InAppNotificationOut from the database model."""
        data_dict = None
        if model.data:
            try:
                data_dict = json.loads(model.data)
            except json.JSONDecodeError:
                data_dict = None

        return cls(
            id=str(model.id),
            title=model.title,
            message=model.message,
            notification_type=model.notification_type,
            data=data_dict,
            created_at=model.created_at,
            read_at=model.read_at,
        )


class InAppNotificationSummary(MealieModel):
    """Summary of notifications for the bell icon."""

    unread_count: int
    has_unread: bool


class InAppNotificationMarkRead(MealieModel):
    """Schema for marking notifications as read."""

    notification_ids: list[str] | None = Field(
        default=None, description="List of notification IDs to mark as read. If None, marks all as read."
    )
