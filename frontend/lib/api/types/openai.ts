/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface ChatMessage {
  role: string;
  content: string;
}
export interface DietarySubstitutionRequest {
  dietary_type: string;
  strictness?: string;
  preserve_flavor?: boolean;
  avoid_ingredients?: string[] | null;
}
export interface IngredientSubstitution {
  original_ingredient: string;
  substitute: string;
  quantity_adjustment?: string | null;
  reason?: string | null;
  notes?: string | null;
}
export interface MealPlanDay {
  date: string;
  breakfast?: string | null;
  lunch?: string | null;
  dinner?: string | null;
  snacks?: string[] | null;
  total_calories?: number | null;
}
export interface MealPlanRequest {
  days?: number;
  dietary_preferences?: string[] | null;
  max_prep_time_minutes?: number | null;
  budget_level?: string | null;
  exclude_recipes?: string[] | null;
  include_ingredients?: string[] | null;
  max_calories_per_day?: number | null;
}
export interface MealPlanResponse {
  days?: MealPlanDay[];
  shopping_list?: ShoppingListItem[];
  total_estimated_cost?: string | null;
  notes?: string | null;
  prep_tips?: string[] | null;
}
export interface ShoppingListItem {
  ingredient: string;
  quantity?: string | null;
  category?: string | null;
}
export interface OpenAIIngredient {
  quantity?: number | null;
  unit?: string | null;
  food?: string | null;
  note?: string | null;
}
export interface OpenAIIngredients {
  ingredients?: OpenAIIngredient[];
}
export interface OpenAIRecipe {
  name: string;
  description?: string | null;
  recipe_yield?: string | null;
  total_time?: string | null;
  prep_time?: string | null;
  perform_time?: string | null;
  ingredients?: OpenAIRecipeIngredient[];
  instructions?: OpenAIRecipeInstruction[];
  notes?: OpenAIRecipeNotes[];
  nutrition?: OpenAIRecipeNutrition | null;
}
export interface OpenAIRecipeIngredient {
  title?: string | null;
  quantity?: number | null;
  unit?: string | null;
  food?: string | null;
  note?: string | null;
  original_text?: string | null;
}
export interface OpenAIRecipeInstruction {
  title?: string | null;
  text: string;
}
export interface OpenAIRecipeNotes {
  title?: string | null;
  text: string;
}
export interface OpenAIRecipeNutrition {
  calories?: string | null;
  fat_content?: string | null;
  protein_content?: string | null;
  carbohydrate_content?: string | null;
  fiber_content?: string | null;
  sugar_content?: string | null;
  sodium_content?: string | null;
  cholesterol_content?: string | null;
  saturated_fat_content?: string | null;
  trans_fat_content?: string | null;
  unsaturated_fat_content?: string | null;
}
export interface OpenAIText {
  text: string;
}
export interface PortionScaleRequest {
  current_servings: number;
  target_servings: number;
  scale_instructions?: boolean;
}
export interface RecipeChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
  recipe_context?: string | null;
}
export interface RecipeChatResponse {
  message: string;
  suggestions?: string[];
}
export interface RecipeEnhanceRequest {
  target_servings?: number | null;
  dietary_restrictions?: string[] | null;
  target_units?: string | null;
  optimize_for?: string | null;
  allergies?: string[] | null;
  substitutions_only?: boolean;
}
export interface RecipeEnhanceResponse {
  name?: string | null;
  ingredients?: OpenAIRecipeIngredient[];
  instructions?: OpenAIRecipeInstruction[];
  notes?: string[];
  changes_summary: string;
  substitutions?: IngredientSubstitution[] | null;
  new_servings?: number | null;
  nutrition_changes?: string | null;
  tips?: string[] | null;
}
export interface RecipeRecommendation {
  recipe_name: string;
  recipe_slug?: string | null;
  recipe_id?: string | null;
  similarity_score: number;
  reason?: string | null;
  matching_ingredients?: string[] | null;
  cuisine?: string | null;
  prep_time_minutes?: number | null;
}
export interface RecipeRecommendationRequest {
  recipe_id?: string | null;
  recipe_name?: string | null;
  cuisine_type?: string | null;
  cooking_method?: string | null;
  max_results?: number;
  include_reasons?: boolean;
  exclude_recipe_ids?: string[] | null;
}
export interface RecipeRecommendationResponse {
  recommendations?: RecipeRecommendation[];
  total_found?: number | null;
  query_recipe?: string | null;
}
export interface RecipeSimilarityRequest {
  recipe_ids: [string, string, ...string[]];
  compare_ingredients?: boolean;
  compare_instructions?: boolean;
}
export interface RecipeSimilarityResponse {
  comparisons?: RecipeSimilarityResult[];
  duplicates_found?: number;
}
export interface RecipeSimilarityResult {
  recipe_a_id: string;
  recipe_b_id: string;
  overall_similarity: number;
  ingredient_similarity?: number | null;
  instruction_similarity?: number | null;
  is_duplicate?: boolean;
  differences?: string[] | null;
}
export interface ShoppingItemGroup {
  category: string;
  items: string[];
  notes?: string | null;
}
export interface ShoppingItemSuggestion {
  name: string;
  reason: string;
  category?: string | null;
}
export interface ShoppingSuggestionsRequest {
  recipe_names: string[];
  current_items?: string[];
}
export interface ShoppingSuggestionsResponse {
  suggested_items?: ShoppingItemSuggestion[];
  tips?: string[];
}
export interface SmartShoppingListRequest {
  items: string[];
  preferences?: string | null;
}
export interface SmartShoppingListResponse {
  groups?: ShoppingItemGroup[];
  suggestions?: string[];
  missing_staples?: string[];
}
export interface UnitConversionRequest {
  target_system: string;
  convert_temperatures?: boolean;
  round_amounts?: boolean;
}
export interface OpenAIBase {}
