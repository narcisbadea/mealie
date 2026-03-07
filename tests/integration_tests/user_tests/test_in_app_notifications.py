"""Integration tests for in-app notification endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.db.models.users.in_app_notification import InAppNotificationModel
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


# Notification routes
def notifications_route():
    return "/api/users/notifications"


def notifications_summary_route():
    return "/api/users/notifications/summary"


def notifications_mark_read_route():
    return "/api/users/notifications/mark-read"


def notification_item_route(notification_id: str):
    return f"/api/users/notifications/{notification_id}"


def create_notification(
    unique_user: TestUser, title: str, message: str, notification_type: str, data: dict | None = None, read_at=None
):
    """Helper function to create a notification in the database."""
    notification = InAppNotificationModel(
        session=unique_user.repos.session,
        user_id=unique_user.user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        data=json.dumps(data) if data else None,
        created_at=get_utc_now(),
        read_at=read_at,
    )
    unique_user.repos.session.add(notification)
    unique_user.repos.session.commit()
    unique_user.repos.session.refresh(notification)
    return notification


class InAppNotificationsTests:
    """Tests for in-app notification CRUD operations."""

    def test_get_notifications_empty(self, api_client: TestClient, unique_user: TestUser):
        """Test getting notifications when none exist."""
        response = api_client.get(notifications_route(), headers=unique_user.token)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_summary_no_notifications(self, api_client: TestClient, unique_user: TestUser):
        """Test getting summary when no notifications exist."""
        response = api_client.get(notifications_summary_route(), headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0
        assert data["has_unread"] is False

    def test_create_and_get_notification(self, api_client: TestClient, unique_user: TestUser):
        """Test creating a notification directly via database and retrieving it."""
        create_notification(
            unique_user,
            title="Test Notification",
            message="This is a test notification",
            notification_type="video_import_success",
            data={"recipe_slug": "test-recipe"},
        )

        # Get notifications
        response = api_client.get(notifications_route(), headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Notification"
        assert data[0]["notification_type"] == "video_import_success"
        assert data[0]["data"]["recipe_slug"] == "test-recipe"
        assert data[0]["read_at"] is None

    def test_get_summary_with_unread(self, api_client: TestClient, unique_user: TestUser):
        """Test getting summary with unread notifications."""
        # Create multiple notifications
        for i in range(3):
            create_notification(
                unique_user,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="video_import_success",
            )

        response = api_client.get(notifications_summary_route(), headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 3
        assert data["has_unread"] is True

    def test_mark_single_notification_as_read(self, api_client: TestClient, unique_user: TestUser):
        """Test marking a single notification as read."""
        notification = create_notification(
            unique_user,
            title="Test Notification",
            message="Test message",
            notification_type="video_import_success",
        )

        # Mark as read
        response = api_client.post(
            notifications_mark_read_route(),
            json={"notification_ids": [str(notification.id)]},
            headers=unique_user.token,
        )
        assert response.status_code == 200

        # Verify it's marked as read
        response = api_client.get(notifications_route(), headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # By default, only unread are returned

        # Check with include_read=True
        response = api_client.get(notifications_route(), params={"include_read": True}, headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["read_at"] is not None

    def test_mark_all_notifications_as_read(self, api_client: TestClient, unique_user: TestUser):
        """Test marking all notifications as read."""
        # Create multiple notifications
        for i in range(5):
            create_notification(
                unique_user,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="video_import_success",
            )

        # Mark all as read
        response = api_client.post(
            notifications_mark_read_route(),
            json={},
            headers=unique_user.token,
        )
        assert response.status_code == 200

        # Verify summary shows 0 unread
        response = api_client.get(notifications_summary_route(), headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0
        assert data["has_unread"] is False

    def test_delete_notification(self, api_client: TestClient, unique_user: TestUser):
        """Test deleting a single notification."""
        notification = create_notification(
            unique_user,
            title="Test Notification",
            message="Test message",
            notification_type="video_import_success",
        )

        # Delete notification
        response = api_client.delete(notification_item_route(str(notification.id)), headers=unique_user.token)
        assert response.status_code == 200

        # Verify it's deleted
        response = api_client.get(notifications_route(), params={"include_read": True}, headers=unique_user.token)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_delete_notification_unauthorized(
        self, api_client: TestClient, unique_user: TestUser, admin_user: TestUser
    ):
        """Test that a user cannot delete another user's notification."""
        notification = create_notification(
            unique_user,
            title="Test Notification",
            message="Test message",
            notification_type="video_import_success",
        )

        # Try to delete as admin_user (should fail)
        response = api_client.delete(notification_item_route(str(notification.id)), headers=admin_user.token)
        assert response.status_code == 403

    def test_delete_notification_not_found(self, api_client: TestClient, unique_user: TestUser):
        """Test deleting a non-existent notification."""
        response = api_client.delete(notification_item_route("non-existent-id"), headers=unique_user.token)
        assert response.status_code == 404

    def test_delete_all_read_notifications(self, api_client: TestClient, unique_user: TestUser):
        """Test deleting all read notifications."""
        # Create read and unread notifications
        for i in range(3):
            create_notification(
                unique_user,
                title=f"Read Notification {i}",
                message=f"Message {i}",
                notification_type="video_import_success",
                read_at=get_utc_now(),  # Already read
            )

        for i in range(2):
            create_notification(
                unique_user,
                title=f"Unread Notification {i}",
                message=f"Message {i}",
                notification_type="video_import_failure",
            )

        # Delete all read
        response = api_client.delete(notifications_route(), headers=unique_user.token)
        assert response.status_code == 200

        # Verify only unread remain
        response = api_client.get(notifications_route(), params={"include_read": True}, headers=unique_user.token)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for n in data:
            assert n["read_at"] is None

    def test_get_notifications_with_limit(self, api_client: TestClient, unique_user: TestUser):
        """Test getting notifications with limit parameter."""
        # Create many notifications
        for i in range(10):
            create_notification(
                unique_user,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="video_import_success",
            )

        # Get with limit
        response = api_client.get(notifications_route(), params={"limit": 5}, headers=unique_user.token)
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_notification_data_json_parsing(self, api_client: TestClient, unique_user: TestUser):
        """Test that notification data is correctly parsed from JSON."""
        data = {
            "recipe_slug": "test-recipe",
            "recipe_name": "Test Recipe",
            "source_url": "https://youtube.com/watch?v=test",
            "source_type": "youtube",
        }

        create_notification(
            unique_user,
            title="YouTube Import Complete",
            message="Recipe imported successfully",
            notification_type="video_import_success",
            data=data,
        )

        response = api_client.get(notifications_route(), headers=unique_user.token)
        assert response.status_code == 200
        result = response.json()[0]
        assert result["data"]["recipe_slug"] == "test-recipe"
        assert result["data"]["recipe_name"] == "Test Recipe"
        assert result["data"]["source_type"] == "youtube"
