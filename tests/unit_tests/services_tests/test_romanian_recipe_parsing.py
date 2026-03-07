"""Tests for OpenAI recipe parsing, especially for Romanian language support."""

import pytest

from mealie.schema.openai.recipe import OpenAIRecipe, OpenAIRecipeIngredient
from mealie.services.recipe.recipe_service import OpenAIRecipeService


class TestFragmentedIngredientDetectionTests:
    """Test detection of fragmented ingredients from YouTube Shorts and similar sources."""

    def test_detects_numeric_only_food_as_fragment(self):
        """Test that numeric-only food fields are detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Fragment: just a number
        ingredient = OpenAIRecipeIngredient(
            quantity=None,
            unit=None,
            food="500",
            note=None,
            original_text="500",
        )

        assert service._is_fragmented_ingredient(ingredient) is True

    def test_detects_decimal_as_fragment(self):
        """Test that decimal numbers are detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        ingredient = OpenAIRecipeIngredient(
            quantity=None,
            unit=None,
            food="2.5",
            note=None,
            original_text="2.5",
        )

        assert service._is_fragmented_ingredient(ingredient) is True

    def test_detects_fraction_as_fragment(self):
        """Test that fractions are detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        ingredient = OpenAIRecipeIngredient(
            quantity=None,
            unit=None,
            food="1/2",
            note=None,
            original_text="1/2",
        )

        assert service._is_fragmented_ingredient(ingredient) is True

    def test_detects_unit_word_as_fragment(self):
        """Test that unit words in food field are detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Unit word as food
        test_cases = ["grams", "g", "cups", "cup", "tbsp", "kg", "ml"]
        for unit_word in test_cases:
            ingredient = OpenAIRecipeIngredient(
                quantity=None,
                unit=None,
                food=unit_word,
                note=None,
                original_text=unit_word,
            )
            assert service._is_fragmented_ingredient(ingredient) is True, f"{unit_word} should be detected as fragment"

    def test_does_not_detect_complete_ingredient_as_fragment(self):
        """Test that complete ingredients are not detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Complete ingredient with multi-word food
        ingredient = OpenAIRecipeIngredient(
            quantity=500,
            unit="g",
            food="flour",
            note=None,
            original_text="500g flour",
        )

        assert service._is_fragmented_ingredient(ingredient) is False

    def test_does_not_detect_single_food_word_as_fragment(self):
        """Test that single food words are not detected as fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Single food word (not a unit, not numeric)
        ingredient = OpenAIRecipeIngredient(
            quantity=None,
            unit=None,
            food="flour",
            note=None,
            original_text="flour",
        )

        # "flour" is a known food, not a fragment
        assert service._is_fragmented_ingredient(ingredient) is False

    def test_multi_word_food_not_fragment(self):
        """Test that multi-word food names are never fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        ingredient = OpenAIRecipeIngredient(
            quantity=None,
            unit=None,
            food="olive oil",
            note=None,
            original_text="olive oil",
        )

        assert service._is_fragmented_ingredient(ingredient) is False


class TestFragmentedIngredientMergingTests:
    """Test merging of fragmented ingredients."""

    def test_merge_quantity_unit_food_fragments(self):
        """Test merging [qty, unit, food] fragments into one ingredient."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        fragments = [
            OpenAIRecipeIngredient(quantity=None, unit=None, food="500", note=None, original_text="500"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="grams", note=None, original_text="grams"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="flour", note=None, original_text="flour"),
        ]

        merged = service._merge_fragmented_ingredients(fragments)

        assert len(merged) == 1
        assert merged[0].quantity == 500
        assert merged[0].unit == "grams"
        assert merged[0].food == "flour"

    def test_merge_quantity_unit_food_fragments_romanian(self):
        """Test merging Romanian fragments: ['500', 'g', 'făină']."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        fragments = [
            OpenAIRecipeIngredient(quantity=None, unit=None, food="500", note=None, original_text="500"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="g", note=None, original_text="g"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="făină", note=None, original_text="făină"),
        ]

        merged = service._merge_fragmented_ingredients(fragments)

        assert len(merged) == 1
        assert merged[0].quantity == 500
        assert merged[0].unit == "g"
        assert merged[0].food == "făină"

    def test_merge_quantity_food_fragments_no_unit(self):
        """Test merging [qty, food] fragments without unit."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        fragments = [
            OpenAIRecipeIngredient(quantity=None, unit=None, food="2", note=None, original_text="2"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="eggs", note=None, original_text="eggs"),
        ]

        merged = service._merge_fragmented_ingredients(fragments)

        assert len(merged) == 1
        assert merged[0].quantity == 2
        assert merged[0].unit is None
        assert merged[0].food == "eggs"

    def test_merge_preserves_non_fragment_ingredients(self):
        """Test that non-fragment ingredients are preserved unchanged."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        ingredients = [
            OpenAIRecipeIngredient(quantity=2, unit="cups", food="flour", note=None, original_text="2 cups flour"),
            OpenAIRecipeIngredient(quantity=1, unit=None, food="egg", note=None, original_text="1 egg"),
        ]

        merged = service._merge_fragmented_ingredients(ingredients)

        assert len(merged) == 2
        assert merged[0].quantity == 2
        assert merged[0].unit == "cups"
        assert merged[0].food == "flour"
        assert merged[1].quantity == 1
        assert merged[1].food == "egg"

    def test_merge_mixed_fragments_and_complete(self):
        """Test merging when fragments are mixed with complete ingredients."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        ingredients = [
            # Fragment group
            OpenAIRecipeIngredient(quantity=None, unit=None, food="500", note=None, original_text="500"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="g", note=None, original_text="g"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="flour", note=None, original_text="flour"),
            # Complete ingredient
            OpenAIRecipeIngredient(quantity=2, unit="cups", food="sugar", note=None, original_text="2 cups sugar"),
            # Another fragment group
            OpenAIRecipeIngredient(quantity=None, unit=None, food="3", note=None, original_text="3"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="eggs", note=None, original_text="eggs"),
        ]

        merged = service._merge_fragmented_ingredients(ingredients)

        assert len(merged) == 3
        # First merged fragment
        assert merged[0].quantity == 500
        assert merged[0].unit == "g"
        assert merged[0].food == "flour"
        # Complete ingredient preserved
        assert merged[1].quantity == 2
        assert merged[1].unit == "cups"
        assert merged[1].food == "sugar"
        # Second merged fragment
        assert merged[2].quantity == 3
        assert merged[2].unit is None
        assert merged[2].food == "eggs"

    def test_merge_empty_ingredients_list(self):
        """Test that empty list is handled correctly."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        merged = service._merge_fragmented_ingredients([])
        assert merged == []

    def test_build_ingredient_from_fragments_basic(self):
        """Test building ingredient from basic fragments."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        fragments = [
            OpenAIRecipeIngredient(quantity=None, unit=None, food="500", note=None, original_text="500"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="grams", note=None, original_text="grams"),
            OpenAIRecipeIngredient(quantity=None, unit=None, food="flour", note=None, original_text="flour"),
        ]

        result = service._build_ingredient_from_fragments(fragments)

        assert result is not None
        assert result.quantity == 500
        assert result.unit == "grams"
        assert result.food == "flour"
        assert "500 grams flour" in result.original_text

    def test_build_ingredient_from_empty_fragments(self):
        """Test building ingredient from empty fragment list."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        result = service._build_ingredient_from_fragments([])
        assert result is None


class TestRomanianIngredientParsingTests:
    """Test that Romanian ingredients are parsed and validated correctly."""

    def test_validate_ingredient_no_swap_needed(self):
        """Test that correctly parsed ingredients are not modified."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Correctly parsed ingredient
        ingredient = OpenAIRecipeIngredient(
            quantity=500,
            unit="g",
            food="carne tocată",
            note=None,
            original_text="500g carne tocată",
        )

        result = service._validate_ingredient(ingredient)
        assert result.unit == "g"
        assert result.food == "carne tocată"

    def test_validate_ingredient_swaps_unit_food_for_ceapa(self):
        """Test that 'ceapă' in unit field is corrected to food."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # WRONG: unit="ceapă", food="roșie" - should be swapped
        ingredient = OpenAIRecipeIngredient(
            quantity=1,
            unit="ceapă",
            food="roșie",
            note=None,
            original_text="o ceapă roșie",
        )

        result = service._validate_ingredient(ingredient)
        assert result.unit is None, "Unit should be None after correction"
        assert result.food == "ceapă", "Food should be 'ceapă' after correction"
        assert "roșie" in (result.note or ""), "Original food should be in note"

    def test_validate_ingredient_swaps_unit_food_for_rosii(self):
        """Test that 'roșii' in unit field is corrected to food."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # WRONG: unit="roșii", food="tăiate" - should be swapped
        ingredient = OpenAIRecipeIngredient(
            quantity=3,
            unit="roșii",
            food="tăiate",
            note="cubulețe",
            original_text="trei roșii tăiate cubulețe",
        )

        result = service._validate_ingredient(ingredient)
        assert result.unit is None, "Unit should be None after correction"
        assert result.food == "roșii", "Food should be 'roșii' after correction"

    def test_validate_ingredient_keeps_valid_unit(self):
        """Test that valid units are kept even when food is a food word."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Correct parsing: unit="linguri", food="ulei"
        ingredient = OpenAIRecipeIngredient(
            quantity=2,
            unit="linguri",
            food="ulei de măsline",
            note=None,
            original_text="două linguri ulei de măsline",
        )

        result = service._validate_ingredient(ingredient)
        assert result.unit == "linguri", "Valid unit should be kept"
        assert result.food == "ulei de măsline", "Valid food should be kept"

    def test_validate_ingredient_handles_metric_units(self):
        """Test that metric units are correctly identified."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Various metric units
        test_cases = [
            (500, "g", "carne"),
            (1, "kg", "cartofi"),
            (250, "ml", "lapte"),
            (1, "l", "apă"),
        ]

        for quantity, unit, food in test_cases:
            ingredient = OpenAIRecipeIngredient(
                quantity=quantity,
                unit=unit,
                food=food,
                note=None,
                original_text=f"{quantity}{unit} {food}",
            )
            result = service._validate_ingredient(ingredient)
            assert result.unit == unit, f"Unit {unit} should be preserved"
            assert result.food == food, f"Food {food} should be preserved"

    def test_validate_ingredient_handles_missing_unit(self):
        """Test that ingredients without units are handled correctly."""
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Ingredient without unit
        ingredient = OpenAIRecipeIngredient(
            quantity=1,
            unit=None,
            food="ceapă roșie",
            note="tocată",
            original_text="o ceapă roșie tocată",
        )

        result = service._validate_ingredient(ingredient)
        assert result.unit is None
        assert result.food == "ceapă roșie"
        assert result.note == "tocată"

    def test_convert_recipe_processes_romanian_ingredients(self):
        """Test full recipe conversion with Romanian ingredients."""
        from uuid import uuid4

        from mealie.schema.household.household import HouseholdInDB
        from mealie.schema.recipe.recipe import Recipe
        from mealie.schema.user.user import PrivateUser

        # Create a minimal service instance with mocked dependencies
        service = OpenAIRecipeService.__new__(OpenAIRecipeService)

        # Mock user and household attributes required by _convert_recipe
        mock_user = type("MockUser", (), {"id": uuid4(), "group_id": uuid4()})()
        mock_household = type("MockHousehold", (), {"id": uuid4(), "group_id": mock_user.group_id})()
        service.user = mock_user
        service.household = mock_household

        # Create a recipe with mixed correct and incorrect parsing
        openai_recipe = OpenAIRecipe(
            name="Mititei",
            description="Rețetă tradițională românească",
            ingredients=[
                # Correctly parsed
                OpenAIRecipeIngredient(
                    quantity=500,
                    unit="g",
                    food="carne tocată",
                    note=None,
                    original_text="500g carne tocată",
                ),
                # WRONG: unit and food swapped
                OpenAIRecipeIngredient(
                    quantity=1,
                    unit="ceapă",
                    food="roșie",
                    note="tocată",
                    original_text="o ceapă roșie tocată",
                ),
                # Correctly parsed with note
                OpenAIRecipeIngredient(
                    quantity=3,
                    unit=None,
                    food="roșii",
                    note="tăiate cubulețe",
                    original_text="trei roșii tăiate cubulețe",
                ),
            ],
            instructions=[],
            notes=[],
        )

        result = service._convert_recipe(openai_recipe)

        assert isinstance(result, Recipe)
        assert result.name == "Mititei"
        assert len(result.recipe_ingredient) == 3

        # First ingredient should be unchanged
        assert result.recipe_ingredient[0].quantity == 500
        assert result.recipe_ingredient[0].unit.name == "g"
        assert result.recipe_ingredient[0].food.name == "carne tocată"

        # Second ingredient should have been corrected
        assert result.recipe_ingredient[1].unit is None
        assert result.recipe_ingredient[1].food.name == "ceapă"

        # Third ingredient should be unchanged
        assert result.recipe_ingredient[2].food.name == "roșii"
        assert result.recipe_ingredient[2].note == "tăiate cubulețe"


class TestKnownUnitsAndFoodsTests:
    """Test the KNOWN_UNITS and KNOWN_FOODS sets."""

    def test_known_units_contains_metric(self):
        """Test that metric units are in KNOWN_UNITS."""
        assert "g" in OpenAIRecipeService.KNOWN_UNITS
        assert "kg" in OpenAIRecipeService.KNOWN_UNITS
        assert "ml" in OpenAIRecipeService.KNOWN_UNITS
        assert "l" in OpenAIRecipeService.KNOWN_UNITS

    def test_known_units_contains_romanian(self):
        """Test that Romanian units are in KNOWN_UNITS."""
        assert "linguri" in OpenAIRecipeService.KNOWN_UNITS
        assert "linguriță" in OpenAIRecipeService.KNOWN_UNITS
        assert "căni" in OpenAIRecipeService.KNOWN_UNITS
        assert "mână" in OpenAIRecipeService.KNOWN_UNITS

    def test_known_foods_contains_romanian(self):
        """Test that Romanian foods are in KNOWN_FOODS."""
        assert "ceapă" in OpenAIRecipeService.KNOWN_FOODS
        assert "ceapa" in OpenAIRecipeService.KNOWN_FOODS  # ASCII variant
        assert "usturoi" in OpenAIRecipeService.KNOWN_FOODS
        assert "roșii" in OpenAIRecipeService.KNOWN_FOODS
        assert "rosii" in OpenAIRecipeService.KNOWN_FOODS  # ASCII variant
        assert "carne" in OpenAIRecipeService.KNOWN_FOODS

    def test_known_foods_contains_english(self):
        """Test that English foods are in KNOWN_FOODS."""
        assert "onion" in OpenAIRecipeService.KNOWN_FOODS
        assert "garlic" in OpenAIRecipeService.KNOWN_FOODS
        assert "tomatoes" in OpenAIRecipeService.KNOWN_FOODS
        assert "chicken" in OpenAIRecipeService.KNOWN_FOODS
