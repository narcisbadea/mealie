<template>
  <div>
    <RecipePageInfoCard
      :recipe="recipe"
      :recipe-scale="recipeScale"
      :landscape="landscape"
    />
    <v-divider />
    <RecipeActionMenu
      :recipe="recipe"
      :slug="recipe.slug"
      :recipe-scale="recipeScale"
      :can-edit="canEditRecipe"
      :name="recipe.name"
      :logged-in="isOwnGroup"
      :open="isEditMode"
      :recipe-id="recipe.id"
      class="ml-auto mt-n7 pb-4"
      @close="$emit('close')"
      @json="toggleEditMode()"
      @edit="setMode(PageMode.EDIT)"
      @save="$emit('save')"
      @delete="$emit('delete')"
      @print="printRecipe"
      @enhanced="applyEnhancement"
    />
  </div>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useRecipePermissions } from "~/composables/recipes";
import RecipePageInfoCard from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInfoCard.vue";
import RecipeActionMenu from "~/components/Domain/Recipe/RecipeActionMenu.vue";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import type { HouseholdSummary } from "~/lib/api/types/household";
import type { Recipe } from "~/lib/api/types/recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { RecipeEnhanceResponse } from "~/lib/api/types/openai";
import { usePageState, usePageUser, PageMode } from "~/composables/recipe-page/shared-state";
import { alert } from "~/composables/use-toast";

interface Props {
  recipe: NoUndefinedField<Recipe>;
  recipeScale?: number;
  landscape?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  recipeScale: 1,
  landscape: false,
});

defineEmits(["save", "delete", "print", "close"]);

const { recipeImage } = useStaticRoutes();
const { imageKey, setMode, toggleEditMode, isEditMode } = usePageState(props.recipe.slug);
const { user } = usePageUser();
const { isOwnGroup } = useLoggedInState();

const recipeHousehold = ref<HouseholdSummary>();
if (user) {
  const userApi = useUserApi();
  userApi.households.getOne(props.recipe.householdId).then(({ data }) => {
    recipeHousehold.value = data || undefined;
  });
}
const { canEditRecipe } = useRecipePermissions(props.recipe, recipeHousehold, user);

function printRecipe() {
  window.print();
}

const i18n = useI18n();

function applyEnhancement(result: RecipeEnhanceResponse) {
  // Apply the enhancement results to the recipe
  if (result.name) {
    props.recipe.name = result.name;
  }
  if (result.ingredients && result.ingredients.length > 0) {
    // Update ingredients with enhanced versions
    props.recipe.recipeIngredient = result.ingredients.map((ing) => ({
      id: "",
      quantity: ing.quantity ?? null,
      unit: ing.unit ?? null,
      food: ing.food ?? "",
      note: ing.note ?? null,
      originalText: ing.original_text ?? "",
      referenceId: "",
    }));
  }
  if (result.instructions && result.instructions.length > 0) {
    // Update instructions with enhanced versions
    props.recipe.recipeInstructions = result.instructions.map((inst) => ({
      id: "",
      text: inst.text,
      title: inst.title ?? "",
      summary: "",
      ingredientReferences: [],
    }));
  }
  if (result.new_servings) {
    props.recipe.recipeYield = `${result.new_servings} servings`;
  }
  // Add notes from enhancement
  if (result.notes && result.notes.length > 0) {
    const existingNotes = props.recipe.notes || [];
    props.recipe.notes = [
      ...existingNotes,
      ...result.notes.map(note => ({ title: "", text: note })),
    ];
  }

  alert.success(i18n.t("recipe.enhance-applied") as string);
}

const hideImage = ref(false);

const recipeImageUrl = computed(() => {
  return recipeImage(props.recipe.id, props.recipe.image, imageKey.value);
});

watch(
  () => recipeImageUrl.value,
  () => {
    hideImage.value = false;
  },
);
</script>
