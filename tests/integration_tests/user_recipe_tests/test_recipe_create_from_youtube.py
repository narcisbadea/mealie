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


def test_openai_create_recipe_from_youtube(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    unique_user: TestUser,
):
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
            ingredients=[OpenAIRecipeIngredient(text=random_string()) for _ in range(random_int(5, 10))],
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
    assert r.status_code == 201

    slug: str = json.loads(r.text)
    r = api_client.get(api_routes.recipes_slug(slug), headers=unique_user.token)
    assert r.status_code == 200
