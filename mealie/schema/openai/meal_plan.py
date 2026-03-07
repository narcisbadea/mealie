"""Schema for AI-powered meal planning."""

from pydantic import Field

from mealie.schema.openai._base import OpenAIBase


class MealPlanRequest(OpenAIBase):
    """Request schema for generating an AI meal plan."""

    days: int = Field(7, description="Number of days to plan")
    dietary_preferences: list[str] | None = Field(
        None,
        description="List of dietary preferences (e.g., ['vegetarian', 'gluten-free'])",
    )
    max_prep_time_minutes: int | None = Field(
        None,
        description="Maximum preparation time per meal in minutes",
    )
    budget_level: str | None = Field(
        None,
        description="Budget level: 'low', 'medium', or 'high'",
    )
    exclude_recipes: list[str] | None = Field(
        None,
        description="List of recipe slugs to exclude from the plan",
    )
    include_ingredients: list[str] | None = Field(
        None,
        description="Ingredients that should be used in the meal plan",
    )
    max_calories_per_day: int | None = Field(
        None,
        description="Maximum calories per day",
    )


class MealPlanDay(OpenAIBase):
    """Schema for a single day in the meal plan."""

    date: str = Field(
        ...,
        description="Date for this meal plan day (YYYY-MM-DD format)",
    )
    breakfast: str | None = Field(
        None,
        description="Breakfast recipe name or suggestion",
    )
    lunch: str | None = Field(
        None,
        description="Lunch recipe name or suggestion",
    )
    dinner: str | None = Field(
        None,
        description="Dinner recipe name or suggestion",
    )
    snacks: list[str] | None = Field(
        None,
        description="List of snack suggestions",
    )
    total_calories: int | None = Field(
        None,
        description="Estimated total calories for the day",
    )


class ShoppingListItem(OpenAIBase):
    """Schema for a shopping list item."""

    ingredient: str = Field(
        ...,
        description="Ingredient name",
    )
    quantity: str | None = Field(
        None,
        description="Quantity needed (e.g., '2 cups')",
    )
    category: str | None = Field(
        None,
        description="Category for grouping (e.g., 'Produce', 'Dairy')",
    )


class MealPlanResponse(OpenAIBase):
    """Response schema for AI-generated meal plan."""

    days: list[MealPlanDay] = Field(
        default_factory=list,
        description="List of meal plan days",
    )
    shopping_list: list[ShoppingListItem] = Field(
        default_factory=list,
        description="Optimized shopping list for all meals",
    )
    total_estimated_cost: str | None = Field(
        None,
        description="Estimated total cost for the meal plan",
    )
    notes: str | None = Field(
        None,
        description="Additional notes or suggestions",
    )
    prep_tips: list[str] | None = Field(
        None,
        description="Meal prep tips for the week",
    )
