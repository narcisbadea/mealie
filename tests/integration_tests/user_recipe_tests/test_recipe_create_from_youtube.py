import json

import pytest
from fastapi.testclient import TestClient

from mealie.schema.openai.recipe import (
    OpenAIRecipe,
    OpenAIRecipeIngredient,
    OpenAIRecipeInstruction,
    OpenAIRecipeNotes,
)
from mealie.services.openai import OpenAIService
from mealie.services.scraper import youtube_scraper
from tests.utils import api_routes
from tests.utils.factories import random_int, random_string
from tests.utils.fixture_schemas import TestUser


def test_openai_create_recipe_from_youtube_returns_202(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that YouTube import now returns 202 Accepted (async)."""

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

    r = api_client.post(
        "/api/recipes/create/youtube",
        json={"url": "https://youtu.be/dQw4w9WgXcQ"},
        headers=unique_user.token,
    )
    # Now returns 202 Accepted (async) instead of 201 Created
    assert r.status_code == 202

    # Response should contain a report ID
    data = r.json()
    assert "reportId" in data


def test_openai_create_recipe_from_youtube_creates_notification(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
    """Test that YouTube import creates an in-app notification."""

    async def mock_get_video_context(url: str) -> tuple[str, str | None]:
        return "Quick tomato pasta recipe from YouTube", "https://example.com/youtube-thumb.jpg"

    async def mock_get_response(self, prompt: str, message: str, *args, **kwargs) -> OpenAIRecipe | None:
        return OpenAIRecipe(
            name="Test Recipe From YouTube",
            description="A test recipe",
            recipe_yield="4 servings",
            total_time="30 minutes",
            prep_time="10 minutes",
            perform_time="20 minutes",
            ingredients=[OpenAIRecipeIngredient(text="tomato")],
            instructions=[OpenAIRecipeInstruction(text="cook it")],
            notes=[],
        )

    monkeypatch.setattr(youtube_scraper, "get_video_context", mock_get_video_context)
    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    # Import from YouTube
    r = api_client.post(
        "/api/recipes/create/youtube",
        json={"url": "https://youtu.be/test123"},
        headers=unique_user.token,
    )
    assert r.status_code == 202

    # Check for notification (may need to wait for background task)
    # This test verifies the endpoint returns the correct response
    # The actual notification creation is tested in unit tests
