"""Schema for AI-powered recipe enhancement."""

from pydantic import Field

from mealie.schema.openai._base import OpenAIBase
from mealie.schema.openai.recipe import OpenAIRecipeIngredient, OpenAIRecipeInstruction


class RecipeEnhanceRequest(OpenAIBase):
    """Request schema for enhancing a recipe with AI."""

    target_servings: int | None = Field(
        None,
        ge=1,
        le=100,
        description="Target number of servings to scale to",
    )
    dietary_restrictions: list[str] | None = Field(
        None,
        description="List of dietary restrictions (e.g., ['vegan', 'gluten-free', 'keto', 'dairy-free'])",
    )
    target_units: str | None = Field(
        None,
        description="Target unit system: 'metric' or 'imperial'",
    )
    optimize_for: str | None = Field(
        None,
        description="Optimization goal: 'time', 'cost', 'health', or 'taste'",
    )
    allergies: list[str] | None = Field(
        None,
        description="List of allergies to account for",
    )
    substitutions_only: bool = Field(
        False,
        description="Only return substitutions without full recipe",
    )


class IngredientSubstitution(OpenAIBase):
    """Schema for an ingredient substitution suggestion."""

    original_ingredient: str = Field(
        ...,
        description="Original ingredient to substitute",
    )
    substitute: str = Field(
        ...,
        description="Suggested substitute ingredient",
    )
    quantity_adjustment: str | None = Field(
        None,
        description="How to adjust the quantity (e.g., 'use 1.5x amount')",
    )
    reason: str | None = Field(
        None,
        description="Reason for this substitution",
    )
    notes: str | None = Field(
        None,
        description="Additional notes about the substitution",
    )


class RecipeEnhanceResponse(OpenAIBase):
    """Response schema for AI-enhanced recipe."""

    name: str | None = Field(
        None,
        description="Recipe name (may be modified for dietary version)",
    )
    ingredients: list[OpenAIRecipeIngredient] = Field(
        default_factory=list,
        description="Modified ingredient list",
    )
    instructions: list[OpenAIRecipeInstruction] = Field(
        default_factory=list,
        description="Modified instruction list",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Additional notes about the modifications",
    )
    changes_summary: str = Field(
        ...,
        description="Summary of all changes made",
    )
    substitutions: list[IngredientSubstitution] | None = Field(
        None,
        description="List of ingredient substitutions made",
    )
    new_servings: int | None = Field(
        None,
        description="The new serving count if scaled",
    )
    nutrition_changes: str | None = Field(
        None,
        description="Summary of nutritional changes",
    )
    tips: list[str] | None = Field(
        None,
        description="Cooking tips for the modified recipe",
    )


class PortionScaleRequest(OpenAIBase):
    """Request schema specifically for portion scaling."""

    current_servings: int = Field(
        ...,
        ge=1,
        description="Current number of servings",
    )
    target_servings: int = Field(
        ...,
        ge=1,
        description="Target number of servings",
    )
    scale_instructions: bool = Field(
        True,
        description="Whether to adjust instruction times/temperatures",
    )


class DietarySubstitutionRequest(OpenAIBase):
    """Request schema for dietary substitutions."""

    dietary_type: str = Field(
        ...,
        description="Type of dietary restriction (vegan, vegetarian, gluten-free, keto, dairy-free, etc.)",
    )
    strictness: str = Field(
        "moderate",
        description="How strict the substitution should be: 'strict', 'moderate', or 'flexible'",
    )
    preserve_flavor: bool = Field(
        True,
        description="Whether to prioritize preserving the original flavor profile",
    )
    avoid_ingredients: list[str] | None = Field(
        None,
        description="Additional ingredients to avoid",
    )


class UnitConversionRequest(OpenAIBase):
    """Request schema for unit conversion."""

    target_system: str = Field(
        ...,
        description="Target unit system: 'metric' or 'imperial'",
    )
    convert_temperatures: bool = Field(
        True,
        description="Whether to convert oven temperatures",
    )
    round_amounts: bool = Field(
        True,
        description="Whether to round to sensible amounts",
    )
