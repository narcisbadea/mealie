"""Unit tests for the VideoImportScraperService."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_scraper import ScrapeRecipeTikTok, ScrapeRecipeYouTube
from mealie.schema.reports.reports import ReportCategory, ReportSummaryStatus
from mealie.schema.user.user import GroupInDB, PrivateUser
from mealie.services.scraper.video_import_scraper import VideoImportScraperService


@pytest.fixture
def mock_recipe():
    """Create a mock recipe for testing."""
    recipe = MagicMock(spec=Recipe)
    recipe.name = "Test Recipe"
    recipe.slug = "test-recipe"
    return recipe


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=PrivateUser)
    user.id = uuid4()
    return user


@pytest.fixture
def mock_group():
    """Create a mock group for testing."""
    group = MagicMock(spec=GroupInDB)
    group.id = uuid4()
    return group


@pytest.fixture
def mock_repos():
    """Create a mock repository factory."""
    repos = MagicMock()
    repos.session = MagicMock()
    repos.group_reports = MagicMock()
    repos.group_report_entries = MagicMock()

    # Mock report creation
    mock_report = MagicMock()
    mock_report.id = uuid4()
    mock_report.status = ReportSummaryStatus.in_progress
    repos.group_reports.create.return_value = mock_report
    repos.group_reports.update.return_value = mock_report

    return repos


@pytest.fixture
def mock_translator():
    """Create a mock translator."""
    return MagicMock()


@pytest.fixture
def mock_recipe_service():
    """Create a mock recipe service."""
    return MagicMock()


class VideoImportScraperServiceTests:
    """Tests for VideoImportScraperService."""

    def test_get_report_id_creates_report(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator
    ):
        """Test that get_report_id creates a report with correct category."""
        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        report_id = service.get_report_id("YouTube", "https://youtube.com/watch?v=test")

        assert report_id == mock_repos.group_reports.create.return_value.id
        mock_repos.group_reports.create.assert_called_once()
        call_args = mock_repos.group_reports.create.call_args[0][0]
        assert call_args.category == ReportCategory.video_import
        assert call_args.name == "Video Import: YouTube"
        assert call_args.group_id == mock_group.id

    @pytest.mark.asyncio
    async def test_scrape_youtube_success(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator, mock_recipe
    ):
        """Test successful YouTube import creates notification with recipe data."""
        mock_recipe_service.create_from_youtube = AsyncMock(return_value=mock_recipe)

        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeYouTube(url="https://youtube.com/watch?v=test")
        await service.scrape_youtube(request)

        # Verify recipe was created
        mock_recipe_service.create_from_youtube.assert_called_once_with("https://youtube.com/watch?v=test", None, True)

        # Verify notification was added to session
        mock_repos.session.add.assert_called()
        assert len(added_objects) == 1

        # Verify notification attributes
        notification = added_objects[0]
        assert notification.user_id == mock_user.id
        assert notification.title == "YouTube Import Complete"
        assert "Test Recipe" in notification.message
        assert notification.notification_type == "video_import_success"

        # Verify notification data contains recipe info
        data = json.loads(notification.data)
        assert data["recipe_slug"] == "test-recipe"
        assert data["recipe_name"] == "Test Recipe"
        assert data["source_url"] == "https://youtube.com/watch?v=test"
        assert data["source_type"] == "youtube"

        # Verify report was finalized as success
        assert service.report.status == ReportSummaryStatus.success

    @pytest.mark.asyncio
    async def test_scrape_youtube_failure(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator
    ):
        """Test failed YouTube import creates failure notification."""
        mock_recipe_service.create_from_youtube = AsyncMock(side_effect=Exception("No transcript available"))

        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeYouTube(url="https://youtube.com/watch?v=test")
        await service.scrape_youtube(request)

        # Verify notification was created for failure
        assert len(added_objects) == 1
        notification = added_objects[0]
        assert notification.title == "YouTube Import Failed"
        assert notification.notification_type == "video_import_failure"

        # Verify notification data contains error info
        data = json.loads(notification.data)
        assert "error" in data
        assert "No transcript available" in data["error"]
        assert data["source_type"] == "youtube"

        # Verify report was finalized as failure
        assert service.report.status == ReportSummaryStatus.failure

    @pytest.mark.asyncio
    async def test_scrape_tiktok_success(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator, mock_recipe
    ):
        """Test successful TikTok import creates notification with recipe data."""
        mock_recipe_service.create_from_tiktok = AsyncMock(return_value=mock_recipe)

        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeTikTok(url="https://tiktok.com/@user/video/123")
        await service.scrape_tiktok(request)

        # Verify recipe was created
        mock_recipe_service.create_from_tiktok.assert_called_once_with("https://tiktok.com/@user/video/123", None, True)

        # Verify notification was created
        assert len(added_objects) == 1
        notification = added_objects[0]
        assert notification.title == "TikTok Import Complete"
        assert notification.notification_type == "video_import_success"

        # Verify notification data contains recipe info
        data = json.loads(notification.data)
        assert data["recipe_slug"] == "test-recipe"
        assert data["source_type"] == "tiktok"

    @pytest.mark.asyncio
    async def test_scrape_tiktok_failure(self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator):
        """Test failed TikTok import creates failure notification."""
        mock_recipe_service.create_from_tiktok = AsyncMock(side_effect=Exception("Could not fetch video captions"))

        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeTikTok(url="https://tiktok.com/@user/video/123")
        await service.scrape_tiktok(request)

        # Verify notification was created for failure
        assert len(added_objects) == 1
        notification = added_objects[0]
        assert notification.title == "TikTok Import Failed"
        assert notification.notification_type == "video_import_failure"

        # Verify notification data contains error info
        data = json.loads(notification.data)
        assert "Could not fetch video captions" in data["error"]
        assert data["source_type"] == "tiktok"

    @pytest.mark.asyncio
    async def test_scrape_youtube_with_language_options(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator, mock_recipe
    ):
        """Test YouTube import with language and grammar options."""
        mock_recipe_service.create_from_youtube = AsyncMock(return_value=mock_recipe)

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeYouTube(
            url="https://youtube.com/watch?v=test",
            target_language="es",
            correct_grammar=False,
        )
        await service.scrape_youtube(request)

        # Verify options were passed correctly
        mock_recipe_service.create_from_youtube.assert_called_once_with("https://youtube.com/watch?v=test", "es", False)

    @pytest.mark.asyncio
    async def test_scrape_openai_parsing_failure(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator
    ):
        """Test handling of OpenAI parsing failures."""
        mock_recipe_service.create_from_youtube = AsyncMock(
            side_effect=ValueError("OpenAI failed to parse recipe from transcript")
        )

        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        request = ScrapeRecipeYouTube(url="https://youtube.com/watch?v=test")
        await service.scrape_youtube(request)

        # Verify failure notification
        assert len(added_objects) == 1
        notification = added_objects[0]
        assert notification.notification_type == "video_import_failure"
        data = json.loads(notification.data)
        assert "OpenAI failed to parse" in data["error"]

    def test_create_notification_without_data(
        self, mock_recipe_service, mock_repos, mock_user, mock_group, mock_translator
    ):
        """Test notification creation without optional data."""
        # Mock the session.add to capture the notification
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_repos.session.add.side_effect = capture_add

        service = VideoImportScraperService(
            service=mock_recipe_service,
            repos=mock_repos,
            user=mock_user,
            group=mock_group,
            translator=mock_translator,
        )

        service._create_notification(
            title="Test Notification",
            message="Test message",
            notification_type="test_type",
            data=None,
        )

        assert len(added_objects) == 1
        notification = added_objects[0]
        assert notification.data is None
