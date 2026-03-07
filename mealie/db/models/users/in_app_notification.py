from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from sqlalchemy import ForeignKey, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime
from mealie.db.models._model_utils.guid import GUID

if TYPE_CHECKING:
    from .users import User


class InAppNotificationModel(SqlAlchemyBase, BaseMixins):
    """In-app notification for users."""

    __tablename__ = "in_app_notifications"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    # The user who receives this notification
    user_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = orm.relationship("User", back_populates="in_app_notifications")

    # Notification content
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)

    # Notification type (e.g., "video_import_success", "video_import_failure")
    notification_type: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Optional reference data (JSON string)
    # For video imports: {"recipe_slug": "...", "recipe_name": "...", "source_url": "..."}
    data: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(NaiveDateTime, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(NaiveDateTime, nullable=True, index=True)

    model_config = ConfigDict(exclude=["user"])

    @auto_init()
    def __init__(self, **_) -> None:
        pass
