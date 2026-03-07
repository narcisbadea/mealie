"""Unit tests for in-app notification schemas."""

import json
import datetime

import pytest

from mealie.schema.user.in_app_notification import (
    InAppNotificationCreate,
    InAppNotificationOut,
    InAppNotificationSummary,
    InAppNotificationMarkRead,
)


class InAppNotificationSchemasTests:
    """Tests for in-app notification Pydantic schemas."""

    def test_in_app_notification_create(self):
        """Test InAppNotificationCreate schema."""
        notification = InAppNotificationCreate(
            user_id="user-123",
            title="Test Notification",
            message="This is a test",
            notification_type="video_import_success",
            data={"recipe_slug": "test-recipe"},
        )

        assert notification.user_id == "user-123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test"
        assert notification.notification_type == "video_import_success"
        assert notification.data == {"recipe_slug": "test-recipe"}

    def test_in_app_notification_create_without_data(self):
        """Test InAppNotificationCreate without optional data."""
        notification = InAppNotificationCreate(
            user_id="user-123",
            title="Test",
            message="Message",
            notification_type="test_type",
        )

        assert notification.data is None

    def test_in_app_notification_out_from_model(self):
        """Test InAppNotificationOut.from_model factory method."""

        # Create a mock model
        class MockModel:
            id = "notification-123"
            title = "Test Notification"
            message = "Test message"
            notification_type = "video_import_success"
            data = json.dumps({"recipe_slug": "test-recipe", "source_type": "youtube"})
            created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
            read_at = None

        notification = InAppNotificationOut.from_model(MockModel())

        assert notification.id == "notification-123"
        assert notification.title == "Test Notification"
        assert notification.notification_type == "video_import_success"
        assert notification.data["recipe_slug"] == "test-recipe"
        assert notification.data["source_type"] == "youtube"
        assert notification.read_at is None

    def test_in_app_notification_out_invalid_json_data(self):
        """Test InAppNotificationOut handles invalid JSON gracefully."""

        class MockModel:
            id = "notification-123"
            title = "Test"
            message = "Message"
            notification_type = "test"
            data = "invalid json{{{"
            created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
            read_at = None

        notification = InAppNotificationOut.from_model(MockModel())

        # Should gracefully handle invalid JSON by returning None
        assert notification.data is None

    def test_in_app_notification_out_null_data(self):
        """Test InAppNotificationOut with null data."""

        class MockModel:
            id = "notification-123"
            title = "Test"
            message = "Message"
            notification_type = "test"
            data = None
            created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
            read_at = datetime.datetime(2025, 1, 1, 13, 0, 0)

        notification = InAppNotificationOut.from_model(MockModel())

        assert notification.data is None
        assert notification.read_at is not None

    def test_in_app_notification_summary(self):
        """Test InAppNotificationSummary schema."""
        summary = InAppNotificationSummary(
            unread_count=5,
            has_unread=True,
        )

        assert summary.unread_count == 5
        assert summary.has_unread is True

    def test_in_app_notification_summary_zero(self):
        """Test InAppNotificationSummary with zero unread."""
        summary = InAppNotificationSummary(
            unread_count=0,
            has_unread=False,
        )

        assert summary.unread_count == 0
        assert summary.has_unread is False

    def test_in_app_notification_mark_read_with_ids(self):
        """Test InAppNotificationMarkRead with specific IDs."""
        mark_read = InAppNotificationMarkRead(notification_ids=["id-1", "id-2", "id-3"])

        assert mark_read.notification_ids == ["id-1", "id-2", "id-3"]

    def test_in_app_notification_mark_read_all(self):
        """Test InAppNotificationMarkRead for marking all as read."""
        mark_read = InAppNotificationMarkRead()  # No IDs = mark all

        assert mark_read.notification_ids is None

    def test_in_app_notification_mark_read_empty_list(self):
        """Test InAppNotificationMarkRead with empty list."""
        mark_read = InAppNotificationMarkRead(notification_ids=[])

        # Empty list should still be valid
        assert mark_read.notification_ids == []

    def test_video_import_success_data_structure(self):
        """Test that video import success data has expected structure."""
        data = {
            "recipe_slug": "my-recipe",
            "recipe_name": "My Recipe",
            "source_url": "https://youtube.com/watch?v=123",
            "source_type": "youtube",
        }

        notification = InAppNotificationCreate(
            user_id="user-123",
            title="YouTube Import Complete",
            message="Recipe 'My Recipe' has been imported successfully.",
            notification_type="video_import_success",
            data=data,
        )

        assert notification.data["recipe_slug"] == "my-recipe"
        assert notification.data["source_type"] == "youtube"

    def test_video_import_failure_data_structure(self):
        """Test that video import failure data has expected structure."""
        data = {
            "source_url": "https://youtube.com/watch?v=123",
            "source_type": "youtube",
            "error": "No transcript available for this video",
        }

        notification = InAppNotificationCreate(
            user_id="user-123",
            title="YouTube Import Failed",
            message="Failed to import recipe: No transcript available for this video",
            notification_type="video_import_failure",
            data=data,
        )

        assert notification.data["error"] == "No transcript available for this video"
        assert notification.data["source_type"] == "youtube"
