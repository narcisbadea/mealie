<template>
  <div>
    <v-card-title class="headline">
      {{ $t("recipe.ai-tab-text") }}
    </v-card-title>
    <v-card-text>
      <p>{{ $t("recipe.ai-text-description") }}</p>
    </v-card-text>

    <v-form
      ref="domTextForm"
      class="mt-4"
      @submit.prevent="createByText"
    >
      <v-textarea
        v-model="recipeText"
        :placeholder="$t('recipe.ai-text-placeholder')"
        rows="10"
        variant="solo-filled"
        class="rounded-lg"
        rounded
      />
      <v-checkbox
        v-model="stayInEditMode"
        color="primary"
        hide-details
        :label="$t('recipe.stay-in-edit-mode')"
      />
      <v-checkbox
        v-model="parseRecipe"
        color="primary"
        hide-details
        :label="$t('recipe.parse-recipe-ingredients-after-import')"
      />
      <v-card-actions class="justify-center">
        <div style="width: 250px">
          <BaseButton
            :disabled="!recipeText || recipeText.trim() === ''"
            rounded
            block
            type="submit"
            :loading="textLoading"
          />
        </div>
      </v-card-actions>
      <p v-if="textLoading" class="text-center mb-0">
        {{ $t("recipe.ai-please-wait-text-processing") }}
      </p>
    </v-form>
    <v-expand-transition>
      <v-alert
        v-if="textError"
        color="error"
        class="mt-6 white--text"
      >
        <v-card-title class="ma-0 pa-0">
          <v-icon
            start
            color="white"
            size="x-large"
          >
            {{ $globals.icons.robot }}
          </v-icon>
          {{ $t("new-recipe.error-title") }}
        </v-card-title>
        <v-divider class="my-3 mx-2" />
        <p>{{ $t("new-recipe.error-details") }}</p>
      </v-alert>
    </v-expand-transition>
  </div>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      key: route => route.path,
    });

    const api = useUserApi();
    const route = useRoute();
    const auth = useMealieAuth();
    const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

    const { stayInEditMode, parseRecipe, navigateToRecipe } = useNewRecipeOptions();

    const recipeText = ref("");
    const textLoading = ref(false);
    const textError = ref(false);
    const domTextForm = ref<VForm | null>(null);

    const createPagePath = computed(() => `/g/${groupSlug.value}/r/create/text`);

    async function createByText() {
      if (!recipeText.value || recipeText.value.trim() === "") {
        return;
      }

      textLoading.value = true;
      textError.value = false;
      const { data, error } = await api.recipes.createOneFromText(recipeText.value);

      if (error || !data) {
        textError.value = true;
        textLoading.value = false;
        return;
      }

      navigateToRecipe(data, groupSlug.value, createPagePath.value);
    }

    return {
      recipeText,
      textLoading,
      textError,
      domTextForm,
      stayInEditMode,
      parseRecipe,
      createByText,
    };
  },
});
</script>
