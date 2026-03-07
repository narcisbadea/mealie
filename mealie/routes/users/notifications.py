"""API routes for in-app notifications."""

from fastapi import APIRouter, HTTPException
from pydantic import UUID4
from sqlalchemy import select, update

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.db.models.users.in_app_notification import InAppNotificationModel
from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.schema.response.responses import SuccessResponse
from mealie.schema.user.in_app_notification import (
    InAppNotificationMarkRead,
    InAppNotificationOut,
    InAppNotificationSummary,
)

router = APIRouter(prefix="/users/notifications", tags=["Users: Notifications"])


@controller(router)
class InAppNotificationsController(BaseUserController):
    """Controller for in-app notifications."""

    @router.get("", response_model=list[InAppNotificationOut])
    def get_notifications(self, include_read: bool = False, limit: int = 50):
        """Get all notifications for the current user."""
        query = select(InAppNotificationModel).where(InAppNotificationModel.user_id == self.user.id)

        if not include_read:
            query = query.where(InAppNotificationModel.read_at.is_(None))

        query = query.order_by(InAppNotificationModel.created_at.desc()).limit(limit)

        results = self.repos.session.execute(query).scalars().all()
        return [InAppNotificationOut.from_model(n) for n in results]

    @router.get("/summary", response_model=InAppNotificationSummary)
    def get_summary(self):
        """Get notification summary (unread count)."""
        query = select(InAppNotificationModel).where(
            InAppNotificationModel.user_id == self.user.id,
            InAppNotificationModel.read_at.is_(None),
        )
        results = self.repos.session.execute(query).scalars().all()
        unread_count = len(results)

        return InAppNotificationSummary(
            unread_count=unread_count,
            has_unread=unread_count > 0,
        )

    @router.post("/mark-read", response_model=SuccessResponse)
    def mark_as_read(self, data: InAppNotificationMarkRead):
        """Mark notifications as read."""
        if data.notification_ids:
            # Mark specific notifications as read
            stmt = (
                update(InAppNotificationModel)
                .where(InAppNotificationModel.id.in_(data.notification_ids))
                .where(InAppNotificationModel.user_id == self.user.id)
                .values(read_at=get_utc_now())
            )
            self.repos.session.execute(stmt)
        else:
            # Mark all as read
            stmt = (
                update(InAppNotificationModel)
                .where(InAppNotificationModel.user_id == self.user.id)
                .where(InAppNotificationModel.read_at.is_(None))
                .values(read_at=get_utc_now())
            )
            self.repos.session.execute(stmt)

        self.repos.session.commit()
        return SuccessResponse.respond("Notifications marked as read")

    @router.delete("/{notification_id}", response_model=SuccessResponse)
    def delete_notification(self, notification_id: UUID4):
        """Delete a notification."""
        notification = self.repos.session.get(InAppNotificationModel, notification_id)

        if not notification:
            raise HTTPException(404, "Notification not found")

        if notification.user_id != self.user.id:
            raise HTTPException(403, "Not authorized to delete this notification")

        self.repos.session.delete(notification)
        self.repos.session.commit()

        return SuccessResponse.respond("Notification deleted")

    @router.delete("", response_model=SuccessResponse)
    def delete_all_read(self):
        """Delete all read notifications."""
        stmt = select(InAppNotificationModel).where(
            InAppNotificationModel.user_id == self.user.id,
            InAppNotificationModel.read_at.isnot(None),
        )
        notifications = self.repos.session.execute(stmt).scalars().all()

        for notification in notifications:
            self.repos.session.delete(notification)

        self.repos.session.commit()
        return SuccessResponse.respond("Read notifications deleted")
