<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('recipe.enhance-recipe')"
    :icon="$globals.icons.robot"
    max-width="600"
  >
    <v-card-text>
      <p class="text-body-2 mb-4">
        {{ $t('recipe.enhance-description') }}
      </p>

      <v-text-field
        v-model.number="targetServings"
        :label="$t('recipe.target-servings')"
        type="number"
        min="1"
        max="100"
        :hint="$t('recipe.target-servings-hint')"
        persistent-hint
        class="mb-4"
      />

      <v-select
        v-model="dietaryRestrictions"
        :items="dietaryOptions"
        :label="$t('recipe.dietary-restrictions')"
        multiple
        chips
        closable-chips
        :hint="$t('recipe.dietary-restrictions-hint')"
        persistent-hint
        class="mb-4"
      />

      <v-select
        v-model="targetUnits"
        :items="unitOptions"
        :label="$t('recipe.target-units')"
        clearable
        :hint="$t('recipe.target-units-hint')"
        persistent-hint
        class="mb-4"
      />

      <v-combobox
        v-model="allergies"
        :items="commonAllergies"
        :label="$t('recipe.allergies')"
        multiple
        chips
        closable-chips
        clearable
        :hint="$t('recipe.allergies-hint')"
        persistent-hint
        class="mb-4"
      />

      <v-select
        v-model="optimizeFor"
        :items="optimizationOptions"
        :label="$t('recipe.optimize-for')"
        clearable
        :hint="$t('recipe.optimize-for-hint')"
        persistent-hint
      />
    </v-card-text>

    <v-card-actions class="justify-end">
      <BaseButton
        cancel
        @click="dialog = false"
      />
      <BaseButton
        color="primary"
        :loading="isLoading"
        :disabled="!hasModifications"
        @click="enhanceRecipe"
      >
        {{ $t('recipe.apply-enhancement') }}
      </BaseButton>
    </v-card-actions>

    <!-- Results Section -->
    <v-divider v-if="result" />
    <v-card-text v-if="result">
      <h3 class="text-h6 mb-2">
        {{ $t('recipe.enhancement-result') }}
      </h3>

      <v-alert
        type="info"
        variant="tonal"
        class="mb-4"
      >
        {{ result.changes_summary }}
      </v-alert>

      <div v-if="result.substitutions && result.substitutions.length > 0">
        <h4 class="text-subtitle-1 mb-2">
          {{ $t('recipe.substitutions') }}
        </h4>
        <v-list density="compact">
          <v-list-item
            v-for="(sub, idx) in result.substitutions"
            :key="idx"
          >
            <v-list-item-title>
              {{ sub.original_ingredient }} → {{ sub.substitute }}
            </v-list-item-title>
            <v-list-item-subtitle v-if="sub.reason">
              {{ sub.reason }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>

      <div v-if="result.tips && result.tips.length > 0">
        <h4 class="text-subtitle-1 mb-2">
          {{ $t('recipe.tips') }}
        </h4>
        <ul class="text-body-2 pl-4">
          <li
            v-for="(tip, idx) in result.tips"
            :key="idx"
          >
            {{ tip }}
          </li>
        </ul>
      </div>

      <div v-if="result.notes && result.notes.length > 0">
        <h4 class="text-subtitle-1 mb-2">
          {{ $t('recipe.notes') }}
        </h4>
        <ul class="text-body-2 pl-4">
          <li
            v-for="(note, idx) in result.notes"
            :key="idx"
          >
            {{ note }}
          </li>
        </ul>
      </div>
    </v-card-text>

    <v-card-actions v-if="result" class="justify-end">
      <BaseButton
        cancel
        @click="dialog = false"
      />
      <BaseButton
        color="primary"
        @click="applyChanges"
      >
        {{ $t('recipe.apply-changes') }}
      </BaseButton>
    </v-card-actions>
  </BaseDialog>
</template>

<script setup lang="ts">
import type { Recipe } from "~/lib/api/types/recipe";
import type { RecipeEnhanceRequest, RecipeEnhanceResponse } from "~/lib/api/types/openai";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";

interface Props {
  recipe: Recipe;
}
const props = defineProps<Props>();

const dialog = defineModel<boolean>({ default: false });
const emit = defineEmits<{
  (e: "enhanced", result: RecipeEnhanceResponse): void;
}>();

const { $globals } = useNuxtApp();
const i18n = useI18n();
const api = useUserApi();

// Form state
const targetServings = ref<number | null>(null);
const dietaryRestrictions = ref<string[]>([]);
const targetUnits = ref<string | null>(null);
const allergies = ref<string[]>([]);
const optimizeFor = ref<string | null>(null);

const isLoading = ref(false);
const result = ref<RecipeEnhanceResponse | null>(null);

// Options
const dietaryOptions = [
  { title: "Vegan", value: "vegan" },
  { title: "Vegetarian", value: "vegetarian" },
  { title: "Gluten-Free", value: "gluten-free" },
  { title: "Dairy-Free", value: "dairy-free" },
  { title: "Keto", value: "keto" },
  { title: "Low-Carb", value: "low-carb" },
  { title: "Paleo", value: "paleo" },
  { title: "Whole30", value: "whole30" },
];

const unitOptions = [
  { title: "Metric", value: "metric" },
  { title: "Imperial", value: "imperial" },
];

const commonAllergies = [
  "Nuts",
  "Peanuts",
  "Shellfish",
  "Fish",
  "Eggs",
  "Soy",
  "Wheat",
  "Sesame",
  "Milk",
];

const optimizationOptions = [
  { title: "Time", value: "time" },
  { title: "Cost", value: "cost" },
  { title: "Health", value: "health" },
  { title: "Taste", value: "taste" },
];

const hasModifications = computed(() => {
  return (
    targetServings.value !== null
    || dietaryRestrictions.value.length > 0
    || targetUnits.value !== null
    || allergies.value.length > 0
    || optimizeFor.value !== null
  );
});

// Reset form when dialog opens
watch(dialog, (isOpen) => {
  if (isOpen) {
    result.value = null;
  }
});

async function enhanceRecipe() {
  if (!hasModifications.value) return;

  isLoading.value = true;
  result.value = null;

  const request: RecipeEnhanceRequest = {
    target_servings: targetServings.value,
    dietary_restrictions: dietaryRestrictions.value.length > 0 ? dietaryRestrictions.value : null,
    target_units: targetUnits.value,
    allergies: allergies.value.length > 0 ? allergies.value : null,
    optimize_for: optimizeFor.value,
    substitutions_only: false,
  };

  try {
    const { data, error } = await api.recipes.enhanceRecipe(props.recipe.slug, request);
    if (error) {
      alert.error(i18n.t("recipe.enhance-error") as string);
      return;
    }
    if (data) {
      result.value = data;
    }
  }
  catch (e) {
    alert.error(i18n.t("recipe.enhance-error") as string);
  }
  finally {
    isLoading.value = false;
  }
}

function applyChanges() {
  if (result.value) {
    emit("enhanced", result.value);
    dialog.value = false;
    alert.success(i18n.t("recipe.enhance-applied") as string);
  }
}
</script>