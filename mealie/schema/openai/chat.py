from pydantic import Field

from mealie.schema.openai._base import OpenAIBase


class ChatMessage(OpenAIBase):
    """A single chat message in the conversation."""

    role: str = Field(
        ...,
        description="The role of the message sender: 'user', 'assistant', or 'system'.",
    )
    content: str = Field(
        ...,
        description="The content of the message.",
    )


class RecipeChatRequest(OpenAIBase):
    """Request for the recipe chat assistant."""

    message: str = Field(
        ...,
        description="The user's message or question about recipes.",
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation for context.",
    )
    recipe_context: str | None = Field(
        None,
        description="Optional context about the current recipe being discussed.",
    )


class RecipeChatResponse(OpenAIBase):
    """Response from the recipe chat assistant."""

    message: str = Field(
        ...,
        description="The assistant's response message.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Optional suggestions for follow-up questions or actions.",
    )


class ShoppingItemGroup(OpenAIBase):
    """A group of shopping items categorized by the AI."""

    category: str = Field(
        ...,
        description="The category name for this group of items (e.g., 'Produce', 'Dairy', 'Meat').",
    )
    items: list[str] = Field(
        ...,
        description="List of item descriptions belonging to this category.",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about this category (e.g., storage tips, substitutions).",
    )


class SmartShoppingListRequest(OpenAIBase):
    """Request for AI-powered smart shopping list organization."""

    items: list[str] = Field(
        ...,
        description="List of shopping list items to organize and categorize.",
    )
    preferences: str | None = Field(
        None,
        description="Optional user preferences for organization "
        "(e.g., 'group by store aisle', 'separate perishables').",
    )


class SmartShoppingListResponse(OpenAIBase):
    """Response from the AI shopping list assistant."""

    groups: list[ShoppingItemGroup] = Field(
        default_factory=list,
        description="Organized groups of shopping items.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Shopping tips or suggestions based on the items.",
    )
    missing_staples: list[str] = Field(
        default_factory=list,
        description="Common staples that might be missing from the list.",
    )


class ShoppingItemSuggestion(OpenAIBase):
    """A suggested item for the shopping list."""

    name: str = Field(
        ...,
        description="The name of the suggested item.",
    )
    reason: str = Field(
        ...,
        description="Why this item is being suggested.",
    )
    category: str | None = Field(
        None,
        description="The category this item belongs to.",
    )


class ShoppingSuggestionsRequest(OpenAIBase):
    """Request for shopping list suggestions based on recipes."""

    recipe_names: list[str] = Field(
        ...,
        description="Names of recipes to analyze for shopping suggestions.",
    )
    current_items: list[str] = Field(
        default_factory=list,
        description="Items already on the shopping list.",
    )


class ShoppingSuggestionsResponse(OpenAIBase):
    """Response with shopping suggestions."""

    suggested_items: list[ShoppingItemSuggestion] = Field(
        default_factory=list,
        description="Suggested items to add to the shopping list.",
    )
    tips: list[str] = Field(
        default_factory=list,
        description="General shopping and meal prep tips.",
    )
