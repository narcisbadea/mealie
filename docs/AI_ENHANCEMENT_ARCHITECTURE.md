# AI Enhancement Architecture

This document describes the architecture for new AI-powered features in Mealie.

## Overview

Three new AI features will be implemented:

1. **AI Recipe Enhancement** - Portion scaling, dietary substitutions, unit conversions
2. **AI Meal Planning Assistant** - Intelligent meal planning based on preferences
3. **AI Recipe Recommendations** - Similarity detection and personalized suggestions

## Architecture

### Service Layer

All new services extend `OpenAIService` from `mealie/services/openai/openai.py`:

```
mealie/services/openai/
├── openai.py              # Base OpenAI service (existing)
├── recipe_enhancer.py     # NEW: Recipe enhancement service
├── meal_planner.py        # NEW: Meal planning service
└── recommendations.py     # NEW: Recipe recommendations service
```

### Schema Layer

All schemas extend `OpenAIBase` from `mealie/schema/openai/_base.py`:

```
mealie/schema/openai/
├── _base.py               # Base schema (existing)
├── recipe.py              # Recipe schema (existing)
├── enhancement.py         # NEW: Enhancement request/response schemas
├── meal_plan.py           # NEW: Meal planning schemas
└── recommendations.py     # NEW: Recommendation schemas
```

### Prompts

```
mealie/services/openai/prompts/
├── recipes/
│   ├── portion-scaler.txt       # NEW: Scale recipe portions
│   ├── dietary-substitution.txt # NEW: Dietary substitutions
│   └── unit-converter.txt       # NEW: Unit conversions
├── meal-planning/
│   └── generate-plan.txt        # NEW: Generate meal plans
└── recommendations/
    ├── find-similar.txt         # NEW: Find similar recipes
    └── suggest-pairings.txt     # NEW: Suggest pairings
```

### API Routes

```
mealie/routes/
├── recipe/
│   ├── recommendation_routes.py  # NEW: /api/recipes/recommendations
│   └── ...
├── meal-plan/
│   └── ai_routes.py              # NEW: /api/meal-plans/ai
└── ...
```

## Detailed Specifications

### 1. Recipe Enhancement

**Endpoint:** `POST /api/recipes/{slug}/enhance`

**Request Schema:**
```python
class RecipeEnhanceRequest(OpenAIBase):
    target_servings: int | None = None
    dietary_restrictions: list[str] | None = None  # ["vegan", "gluten-free", "keto"]
    target_units: str | None = None  # "metric" or "imperial"
```

**Response Schema:**
```python
class RecipeEnhanceResponse(OpenAIBase):
    ingredients: list[OpenAIRecipeIngredient]
    instructions: list[OpenAIRecipeInstruction]
    notes: list[str]
    changes_summary: str
```

### 2. Meal Planning

**Endpoint:** `POST /api/meal-plans/ai/generate`

**Request Schema:**
```python
class MealPlanRequest(OpenAIBase):
    days: int = 7
    dietary_preferences: list[str] | None = None
    max_prep_time_minutes: int | None = None
    budget_level: str | None = None  # "low", "medium", "high"
    exclude_recipes: list[str] | None = None  # Recipe IDs to exclude
```

**Response Schema:**
```python
class MealPlanDay(OpenAIBase):
    date: str
    breakfast: str | None  # Recipe slug or name
    lunch: str | None
    dinner: str | None
    snacks: list[str] | None

class MealPlanResponse(OpenAIBase):
    days: list[MealPlanDay]
    shopping_list: list[str]
    total_estimated_cost: str | None
    notes: str | None
```

### 3. Recipe Recommendations

**Endpoint:** `POST /api/recipes/recommendations`

**Request Schema:**
```python
class RecipeRecommendationRequest(OpenAIBase):
    recipe_id: str | None = None  # Find similar to this recipe
    cuisine_type: str | None = None
    cooking_method: str | None = None
    max_results: int = 5
```

**Response Schema:**
```python
class RecipeRecommendation(OpenAIBase):
    recipe_name: str
    recipe_slug: str | None
    similarity_score: float
    reason: str

class RecipeRecommendationResponse(OpenAIBase):
    recommendations: list[RecipeRecommendation]
```

## Implementation Order

1. Create schemas in `mealie/schema/openai/`
2. Create prompts in `mealie/services/openai/prompts/`
3. Create services in `mealie/services/openai/`
4. Create routes in `mealie/routes/`
5. Run `task dev:generate` to generate TypeScript types
6. Implement frontend components

## Frontend Integration

New components needed in `frontend/components/Domain/`:

- `Recipe/RecipeEnhanceDialog.vue` - UI for recipe enhancement
- `MealPlan/AIMealPlanner.vue` - AI meal planning interface
- `Recipe/RecipeRecommendations.vue` - Recommendations sidebar

## Testing

Test files should be created in:
- `tests/unit_tests/services_tests/openai_tests/`
- `tests/integration_tests/`

Mock OpenAI responses for consistent testing.

## Configuration

New environment variables:
- `OPENAI_ENABLE_ENHANCEMENT=true` - Enable/disable enhancement features
- `OPENAI_ENABLE_MEAL_PLANNING=true` - Enable/disable meal planning
- `OPENAI_ENABLE_RECOMMENDATIONS=true` - Enable/disable recommendations