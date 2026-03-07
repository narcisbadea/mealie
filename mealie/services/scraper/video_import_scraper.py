"""Service for async video imports (YouTube/TikTok) with notifications."""

import json

from pydantic import UUID4

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.db.models.users import InAppNotificationModel
from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe_scraper import ScrapeRecipeTikTok, ScrapeRecipeYouTube
from mealie.schema.reports.reports import (
    ReportCategory,
    ReportCreate,
    ReportEntryCreate,
    ReportSummaryStatus,
)
from mealie.schema.user.user import GroupInDB, PrivateUser
from mealie.services._base_service import BaseService
from mealie.services.recipe.recipe_service import RecipeService


class VideoImportScraperService(BaseService):
    """Service for async video imports with in-app notifications."""

    def __init__(
        self,
        service: RecipeService,
        repos: AllRepositories,
        user: PrivateUser,
        group: GroupInDB,
        translator: Translator,
    ) -> None:
        self.service = service
        self.repos = repos
        self.user = user
        self.group = group
        self.translator = translator
        super().__init__()

    def get_report_id(self, source: str, url: str) -> UUID4:
        """Create a report for the video import and return its ID."""
        import_report = ReportCreate(
            name=f"Video Import: {source}",
            category=ReportCategory.video_import,
            status=ReportSummaryStatus.in_progress,
            group_id=self.group.id,
        )

        self.report = self.repos.group_reports.create(import_report)
        return self.report.id

    def _create_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        data: dict | None = None,
    ) -> None:
        """Create an in-app notification for the user."""
        notification = InAppNotificationModel(
            session=self.repos.session,
            user_id=self.user.id,
            title=title,
            message=message,
            notification_type=notification_type,
            data=json.dumps(data) if data else None,
            created_at=get_utc_now(),
            read_at=None,
        )
        self.repos.session.add(notification)
        self.repos.session.commit()

    def _add_report_entry(self, success: bool, message: str, exception: str = "") -> None:
        """Add an entry to the report."""
        entry = ReportEntryCreate(
            report_id=self.report.id,
            success=success,
            message=message,
            exception=exception,
        )
        self.repos.group_report_entries.create(entry)

    def _finalize_report(self, success: bool) -> None:
        """Update the report status."""
        self.report.status = ReportSummaryStatus.success if success else ReportSummaryStatus.failure
        self.repos.group_reports.update(self.report.id, self.report)

    async def scrape_youtube(self, req: ScrapeRecipeYouTube) -> None:
        """Scrape a YouTube video and create a recipe."""
        if not hasattr(self, "report"):
            self.get_report_id("YouTube", req.url)

        try:
            recipe = await self.service.create_from_youtube(req.url, req.target_language, req.correct_grammar)

            self._add_report_entry(
                success=True,
                message=f"Successfully imported recipe '{recipe.name}' from YouTube",
            )
            self._finalize_report(success=True)

            self._create_notification(
                title="YouTube Import Complete",
                message=f"Recipe '{recipe.name}' has been imported successfully.",
                notification_type="video_import_success",
                data={
                    "recipe_slug": recipe.slug,
                    "recipe_name": recipe.name,
                    "source_url": req.url,
                    "source_type": "youtube",
                },
            )

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Failed to import YouTube video: {req.url}")
            self.logger.exception(e)

            self._add_report_entry(
                success=False,
                message=f"Failed to import recipe from YouTube: {req.url}",
                exception=error_message,
            )
            self._finalize_report(success=False)

            self._create_notification(
                title="YouTube Import Failed",
                message=f"Failed to import recipe: {error_message}",
                notification_type="video_import_failure",
                data={
                    "source_url": req.url,
                    "source_type": "youtube",
                    "error": error_message,
                },
            )

    async def scrape_tiktok(self, req: ScrapeRecipeTikTok) -> None:
        """Scrape a TikTok video and create a recipe."""
        if not hasattr(self, "report"):
            self.get_report_id("TikTok", req.url)

        try:
            recipe = await self.service.create_from_tiktok(req.url, req.target_language, req.correct_grammar)

            self._add_report_entry(
                success=True,
                message=f"Successfully imported recipe '{recipe.name}' from TikTok",
            )
            self._finalize_report(success=True)

            self._create_notification(
                title="TikTok Import Complete",
                message=f"Recipe '{recipe.name}' has been imported successfully.",
                notification_type="video_import_success",
                data={
                    "recipe_slug": recipe.slug,
                    "recipe_name": recipe.name,
                    "source_url": req.url,
                    "source_type": "tiktok",
                },
            )

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Failed to import TikTok video: {req.url}")
            self.logger.exception(e)

            self._add_report_entry(
                success=False,
                message=f"Failed to import recipe from TikTok: {req.url}",
                exception=error_message,
            )
            self._finalize_report(success=False)

            self._create_notification(
                title="TikTok Import Failed",
                message=f"Failed to import recipe: {error_message}",
                notification_type="video_import_failure",
                data={
                    "source_url": req.url,
                    "source_type": "tiktok",
                    "error": error_message,
                },
            )
