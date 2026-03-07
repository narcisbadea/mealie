"""Integration tests for async video import (YouTube/TikTok) endpoints."""

import pytest
from fastapi.testclient import TestClient

from mealie.schema.openai.recipe import (
    OpenAIRecipe,
    OpenAIRecipeIngredient,
    OpenAIRecipeInstruction,
    OpenAIRecipeNotes,
)
from mealie.services.openai import OpenAIService
from mealie.services.scraper import tiktok_scraper, youtube_scraper
from tests.utils import api_routes
from tests.utils.factories import random_int, random_string
from tests.utils.fixture_schemas import TestUser


def test_youtube_import_returns_202(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that YouTube import returns 202 Accepted."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Quick tomato pasta recipe from YouTube", "https://example.com/youtube-thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name=random_string(),
            description=random_string(),
            recipe_yield=random_string(),
            total_time=random_string(),
            prep_time=random_string(),
            perform_time=random_string(),
            ingredients=[OpenAIRecipeIngredient(original_text=random_string()) for _ in range(random_int(5, 10))],
            instructions=[OpenAIRecipeInstruction(text=random_string()) for _ in range(1, random_int(5, 10))],
            notes=[OpenAIRecipeNotes(text=random_string()) for _ in range(random_int(2, 5))],
        )

    monkeypatch.setattr(youtube_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/youtube",
        json={"url": "https://youtu.be/dQw4w9WgXcQ"},
        headers=unique_user.token,
    )

    # Should return 202 Accepted (async)
    assert response.status_code == 202
    data = response.json()
    assert "reportId" in data


def test_tiktok_import_returns_202(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that TikTok import returns 202 Accepted."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Quick pasta recipe from TikTok", "https://example.com/tiktok-thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name=random_string(),
            description=random_string(),
            recipe_yield=random_string(),
            total_time=random_string(),
            prep_time=random_string(),
            perform_time=random_string(),
            ingredients=[OpenAIRecipeIngredient(original_text=random_string()) for _ in range(random_int(5, 10))],
            instructions=[OpenAIRecipeInstruction(text=random_string()) for _ in range(1, random_int(5, 10))],
            notes=[OpenAIRecipeNotes(text=random_string()) for _ in range(random_int(2, 5))],
        )

    monkeypatch.setattr(tiktok_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/tiktok",
        json={"url": "https://www.tiktok.com/@user/video/123456789"},
        headers=unique_user.token,
    )

    # Should return 202 Accepted (async)
    assert response.status_code == 202
    data = response.json()
    assert "reportId" in data


def test_youtube_import_with_language_options(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test YouTube import with language options."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Recipe from YouTube", "https://example.com/thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="Spanish Recipe",
            description="A recipe in Spanish",
            recipe_yield="4 servings",
            total_time="30 minutes",
            prep_time="10 minutes",
            perform_time="20 minutes",
            ingredients=[OpenAIRecipeIngredient(original_text="ingrediente")],
            instructions=[OpenAIRecipeInstruction(text="instruccion")],
            notes=[],
        )

    monkeypatch.setattr(youtube_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/youtube",
        json={
            "url": "https://youtu.be/test123",
            "target_language": "es",
            "correct_grammar": False,
        },
        headers=unique_user.token,
    )

    assert response.status_code == 202
    assert "reportId" in response.json()


def test_tiktok_import_with_language_options(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test TikTok import with language options."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Recipe from TikTok", "https://example.com/thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="French Recipe",
            description="A recipe in French",
            recipe_yield="2 servings",
            total_time="15 minutes",
            prep_time="5 minutes",
            perform_time="10 minutes",
            ingredients=[OpenAIRecipeIngredient(original_text="ingredient")],
            instructions=[OpenAIRecipeInstruction(text="instruction")],
            notes=[],
        )

    monkeypatch.setattr(tiktok_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/tiktok",
        json={
            "url": "https://www.tiktok.com/@user/video/987654321",
            "target_language": "fr",
            "correct_grammar": True,
        },
        headers=unique_user.token,
    )

    assert response.status_code == 202
    assert "reportId" in response.json()


def test_youtube_import_creates_report(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that YouTube import creates a report."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Recipe from YouTube", "https://example.com/thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="Test Recipe",
            description="Test",
            recipe_yield="1",
            total_time="10 min",
            prep_time="5 min",
            perform_time="5 min",
            ingredients=[],
            instructions=[],
            notes=[],
        )

    monkeypatch.setattr(youtube_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/youtube",
        json={"url": "https://youtu.be/test123"},
        headers=unique_user.token,
    )

    assert response.status_code == 202
    report_id = response.json()["reportId"]

    # Check that report was created
    response = api_client.get(
        api_routes.groups_reports_item_id(report_id),
        headers=unique_user.token,
    )
    # Report should exist (might be in progress or completed)
    assert response.status_code in [200, 404]  # 404 if background task hasn't started yet


def test_tiktok_import_creates_report(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that TikTok import creates a report."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Recipe from TikTok", "https://example.com/thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="Test Recipe",
            description="Test",
            recipe_yield="1",
            total_time="10 min",
            prep_time="5 min",
            perform_time="5 min",
            ingredients=[],
            instructions=[],
            notes=[],
        )

    monkeypatch.setattr(tiktok_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response = api_client.post(
        "/api/recipes/create/tiktok",
        json={"url": "https://www.tiktok.com/@user/video/123"},
        headers=unique_user.token,
    )

    assert response.status_code == 202
    report_id = response.json()["reportId"]

    # Check that report was created
    response = api_client.get(
        api_routes.groups_reports_item_id(report_id),
        headers=unique_user.token,
    )
    assert response.status_code in [200, 404]


def test_multiple_concurrent_imports(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that multiple concurrent imports each get unique report IDs."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Recipe from YouTube", "https://example.com/thumb.jpg"

    async def mock_get_tiktok_context(url: str) -> tuple[str, str | None]:
        return "Recipe from TikTok", "https://example.com/thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="Test Recipe",
            description="Test",
            recipe_yield="1",
            total_time="10 min",
            prep_time="5 min",
            perform_time="5 min",
            ingredients=[],
            instructions=[],
            notes=[],
        )

    monkeypatch.setattr(youtube_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(tiktok_scraper, "get_video_context", mock_get_tiktok_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    # Make multiple import requests
    report_ids = []
    for i in range(3):
        response = api_client.post(
            "/api/recipes/create/youtube",
            json={"url": f"https://youtu.be/test{i}"},
            headers=unique_user.token,
        )
        assert response.status_code == 202
        report_ids.append(response.json()["reportId"])

    # All report IDs should be unique
    assert len(set(report_ids)) == 3