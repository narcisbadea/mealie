"""Schema for AI-powered recipe recommendations."""

from pydantic import Field

from mealie.schema.openai._base import OpenAIBase


class RecipeRecommendationRequest(OpenAIBase):
    """Request schema for getting recipe recommendations."""

    recipe_id: str | None = Field(
        None,
        description="Recipe ID to find similar recipes for",
    )
    recipe_name: str | None = Field(
        None,
        description="Recipe name to find similar recipes for",
    )
    cuisine_type: str | None = Field(
        None,
        description="Filter by cuisine type (e.g., 'Italian', 'Mexican')",
    )
    cooking_method: str | None = Field(
        None,
        description="Filter by cooking method (e.g., 'grilled', 'baked')",
    )
    max_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of recommendations to return",
    )
    include_reasons: bool = Field(
        True,
        description="Include reasons for each recommendation",
    )
    exclude_recipe_ids: list[str] | None = Field(
        None,
        description="List of recipe IDs to exclude from results",
    )


class RecipeRecommendation(OpenAIBase):
    """Schema for a single recipe recommendation."""

    recipe_name: str = Field(
        ...,
        description="Name of the recommended recipe",
    )
    recipe_slug: str | None = Field(
        None,
        description="Slug of the recipe if it exists in the database",
    )
    recipe_id: str | None = Field(
        None,
        description="ID of the recipe if it exists in the database",
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score between 0 and 1",
    )
    reason: str | None = Field(
        None,
        description="Reason for this recommendation",
    )
    matching_ingredients: list[str] | None = Field(
        None,
        description="Ingredients that match the original recipe",
    )
    cuisine: str | None = Field(
        None,
        description="Cuisine type of the recipe",
    )
    prep_time_minutes: int | None = Field(
        None,
        description="Estimated preparation time in minutes",
    )


class RecipeRecommendationResponse(OpenAIBase):
    """Response schema for recipe recommendations."""

    recommendations: list[RecipeRecommendation] = Field(
        default_factory=list,
        description="List of recipe recommendations",
    )
    total_found: int | None = Field(
        None,
        description="Total number of similar recipes found",
    )
    query_recipe: str | None = Field(
        None,
        description="The recipe that was used as the query",
    )


class RecipeSimilarityRequest(OpenAIBase):
    """Request schema for finding similar recipes."""

    recipe_ids: list[str] = Field(
        ...,
        min_length=2,
        description="List of recipe IDs to compare for similarity",
    )
    compare_ingredients: bool = Field(
        True,
        description="Include ingredient comparison",
    )
    compare_instructions: bool = Field(
        True,
        description="Include instruction comparison",
    )


class RecipeSimilarityResult(OpenAIBase):
    """Schema for recipe similarity comparison result."""

    recipe_a_id: str = Field(..., description="First recipe ID")
    recipe_b_id: str = Field(..., description="Second recipe ID")
    overall_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall similarity score",
    )
    ingredient_similarity: float | None = Field(
        None,
        description="Ingredient similarity score",
    )
    instruction_similarity: float | None = Field(
        None,
        description="Instruction similarity score",
    )
    is_duplicate: bool = Field(
        False,
        description="Whether the recipes are likely duplicates",
    )
    differences: list[str] | None = Field(
        None,
        description="Key differences between the recipes",
    )


class RecipeSimilarityResponse(OpenAIBase):
    """Response schema for recipe similarity comparison."""

    comparisons: list[RecipeSimilarityResult] = Field(
        default_factory=list,
        description="List of similarity comparisons",
    )
    duplicates_found: int = Field(
        0,
        description="Number of duplicate pairs found",
    )
