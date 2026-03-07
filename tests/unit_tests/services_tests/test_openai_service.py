import pytest

import mealie.services.openai.openai as openai_module
from mealie.services.openai.openai import OpenAIService


class _SettingsStub:
    OPENAI_ENABLED = True
    OPENAI_MODEL = "gpt-4o"
    OPENAI_WORKERS = 1
    OPENAI_SEND_DATABASE_DATA = False
    OPENAI_ENABLE_IMAGE_SERVICES = True
    OPENAI_CUSTOM_PROMPT_DIR = None
    OPENAI_BASE_URL = None
    OPENAI_API_KEY = "dummy"
    OPENAI_REQUEST_TIMEOUT = 30
    OPENAI_CUSTOM_HEADERS = {}
    OPENAI_CUSTOM_PARAMS = {}


@pytest.fixture()
def settings_stub(tmp_path, monkeypatch):
    s = _SettingsStub()

    prompts_dir = tmp_path / "prompts"
    (prompts_dir / "recipes").mkdir(parents=True)
    default_prompt = prompts_dir / "recipes" / "parse-recipe-ingredients.txt"
    default_prompt.write_text("DEFAULT PROMPT")

    monkeypatch.setattr(OpenAIService, "PROMPTS_DIR", prompts_dir)

    def _fake_get_app_settings():
        return s

    monkeypatch.setattr(openai_module, "get_app_settings", _fake_get_app_settings)
    return s


def test_get_prompt_default_only(settings_stub):
    svc = OpenAIService()
    out = svc.get_prompt("recipes.parse-recipe-ingredients")
    assert out == "DEFAULT PROMPT"


def test_get_prompt_custom_dir_used(settings_stub, tmp_path):
    custom_dir = tmp_path / "custom"
    (custom_dir / "recipes").mkdir(parents=True)
    (custom_dir / "recipes" / "parse-recipe-ingredients.txt").write_text("CUSTOM PROMPT")

    settings_stub.OPENAI_CUSTOM_PROMPT_DIR = str(custom_dir)

    svc = OpenAIService()
    out = svc.get_prompt("recipes.parse-recipe-ingredients")
    assert out == "CUSTOM PROMPT"


def test_get_prompt_custom_empty_falls_back_to_default(settings_stub, tmp_path):
    custom_dir = tmp_path / "custom"
    (custom_dir / "recipes").mkdir(parents=True)
    (custom_dir / "recipes" / "parse-recipe-ingredients.txt").write_text("")

    settings_stub.OPENAI_CUSTOM_PROMPT_DIR = str(custom_dir)
    svc = OpenAIService()
    out = svc.get_prompt("recipes.parse-recipe-ingredients")
    assert out == "DEFAULT PROMPT"


def test_get_prompt_raises_when_no_files(settings_stub, monkeypatch):
    # Point PROMPTS_DIR to an empty temp folder (already done in fixture) but remove default file
    prompts_dir = OpenAIService.PROMPTS_DIR
    for p in prompts_dir.rglob("*.txt"):
        p.unlink()

    svc = OpenAIService()
    with pytest.raises(OSError) as ei:
        svc.get_prompt("recipes.parse-recipe-ingredients")
    assert "Unable to load prompt" in str(ei.value)


# =============================================================================
# Video Prompt Content Tests
# =============================================================================


class VideoPromptContentTests:
    """
    Tests for parse-recipe-video.txt prompt content.
    These tests verify that the prompt contains all required sections for
    proper JSON format enforcement and platform-specific guidance.
    """

    @pytest.fixture()
    def video_prompt(self):
        """Load the actual video prompt file."""
        return OpenAIService.PROMPTS_DIR / "recipes" / "parse-recipe-video.txt"

    def test_prompt_file_exists(self, video_prompt):
        """Verify the video prompt file exists."""
        assert video_prompt.exists(), "parse-recipe-video.txt should exist"

    def test_json_format_enforcement_section(self, video_prompt):
        """Verify the prompt has explicit JSON format enforcement at the top."""
        content = video_prompt.read_text()
        # Check for critical JSON enforcement warning
        assert "INVALID JSON" in content, "Prompt should warn about invalid JSON"
        assert "JSON.parse()" in content, "Prompt should mention JSON.parse()"
        assert "MINIMALLY VALID RESPONSE" in content, "Prompt should show minimally valid response example"

    def test_json_schema_section(self, video_prompt):
        """Verify the prompt contains the exact JSON schema."""
        content = video_prompt.read_text()
        # Check for required schema fields
        assert '"name"' in content, "Schema should include name field"
        assert '"ingredients"' in content, "Schema should include ingredients field"
        assert '"instructions"' in content, "Schema should include instructions field"
        assert '"food"' in content, "Schema should include food field in ingredients"
        assert '"quantity"' in content, "Schema should include quantity field"
        assert '"unit"' in content, "Schema should include unit field"
        assert '"original_text"' in content, "Schema should include original_text field"

    def test_platform_specific_guidance_tiktok(self, video_prompt):
        """Verify TikTok-specific guidance is present."""
        content = video_prompt.read_text()
        assert "TIKTOK" in content.upper(), "Prompt should have TikTok section"
        # Check for TikTok-specific handling instructions
        assert "text overlay" in content.lower() or "text overlays" in content.lower(), (
            "Prompt should handle TikTok text overlays"
        )
        assert "fast-paced" in content.lower() or "quick cut" in content.lower(), (
            "Prompt should address TikTok's fast-paced content"
        )

    def test_platform_specific_guidance_youtube(self, video_prompt):
        """Verify YouTube-specific guidance is present."""
        content = video_prompt.read_text()
        assert "YOUTUBE" in content.upper(), "Prompt should have YouTube section"
        # Check for YouTube-specific handling instructions
        assert "sponsor" in content.lower(), "Prompt should mention sponsor segment handling"
        assert "section" in content.lower() and "header" in content.lower(), (
            "Prompt should address section headers for YouTube"
        )

    def test_anti_pattern_examples(self, video_prompt):
        """Verify multiple anti-pattern examples exist."""
        content = video_prompt.read_text()
        # Count WRONG/RIGHT pairs - should have at least 9 per Builder's notes
        wrong_count = content.count("WRONG:")
        right_count = content.count("RIGHT:")
        assert wrong_count >= 9, f"Prompt should have at least 9 anti-pattern examples, found {wrong_count}"
        assert right_count >= 9, f"Prompt should have at least 9 correct pattern examples, found {right_count}"

        # Check for specific anti-patterns mentioned in Builder's notes
        assert 'food": null' in content or 'food": null' in content, "Prompt should show anti-pattern for null food"
        assert 'food": ""' in content or 'food"": ""' in content or "food cannot be empty" in content.lower(), (
            "Prompt should show anti-pattern for empty food string"
        )

    def test_edge_case_no_recipe_found(self, video_prompt):
        """Verify edge case handling for when no recipe is found."""
        content = video_prompt.read_text()
        assert "no recipe" in content.lower(), "Prompt should handle 'no recipe found' scenario"
        assert '"ingredients": []' in content or '"ingredients":[]' in content, (
            "Prompt should show empty ingredients array for no-recipe case"
        )

    def test_incomplete_ingredients_guidance(self, video_prompt):
        """Verify guidance for incomplete ingredients."""
        content = video_prompt.read_text()
        assert "fabricate" in content.lower() or "guess" in content.lower(), (
            "Prompt should warn against fabricating missing values"
        )
        assert "null for missing" in content.lower() or "null for" in content.lower(), (
            "Prompt should instruct to use null for missing values"
        )

    def test_self_check_instructions(self, video_prompt):
        """Verify self-check instructions exist for model validation."""
        content = video_prompt.read_text()
        assert "SELF-CHECK" in content.upper() or "VERIFY" in content.upper(), "Prompt should have self-check section"
        # Check for specific validation points
        assert 'non-empty "food"' in content or "food field" in content.lower(), (
            "Self-check should verify food field is non-empty"
        )
        assert "syntactically valid" in content.lower() or "trailing comma" in content.lower(), (
            "Self-check should verify JSON syntax"
        )

    def test_unit_vs_food_field_distinction(self, video_prompt):
        """Verify clear distinction between unit and food fields."""
        content = video_prompt.read_text()
        assert '"onion"' in content, "Prompt should show onion as food example"
        assert "NOT a unit" in content.upper() or "not a unit" in content.lower(), (
            "Prompt should explicitly state when something is NOT a unit"
        )
        assert "measurement unit" in content.lower(), "Prompt should explain measurement units"

    def test_required_fields_marked(self, video_prompt):
        """Verify REQUIRED fields are clearly marked in the prompt."""
        content = video_prompt.read_text()
        assert "REQUIRED" in content, "Prompt should mark required fields"
        # Check name is marked as required
        lines = content.split("\n")
        name_line_required = any("name" in line.lower() and "required" in line.lower() for line in lines)
        assert name_line_required, "name field should be marked as REQUIRED"

    def test_field_rules_section(self, video_prompt):
        """Verify field rules section exists with detailed guidance."""
        content = video_prompt.read_text()
        assert "FIELD RULES" in content.upper() or "field rules" in content.lower(), (
            "Prompt should have FIELD RULES section"
        )
        # Check for key field rule descriptions
        assert "food:" in content, "Field rules should describe food field"
        assert "unit:" in content, "Field rules should describe unit field"
        assert "quantity:" in content, "Field rules should describe quantity field"

    def test_multilingual_support(self, video_prompt):
        """Verify prompt has language-specific examples for multilingual support."""
        content = video_prompt.read_text()
        # Check for Romanian examples (as shown in the prompt)
        assert "ROMANIAN" in content.upper() or "romanian" in content.lower(), (
            "Prompt should have Romanian language examples"
        )
        # Check for at least one other language
        languages_present = sum(
            [
                "ENGLISH" in content.upper(),
                "ITALIAN" in content.upper(),
                "SPANISH" in content.upper(),
                "ROMANIAN" in content.upper(),
            ]
        )
        assert languages_present >= 2, "Prompt should have examples in at least 2 languages"
