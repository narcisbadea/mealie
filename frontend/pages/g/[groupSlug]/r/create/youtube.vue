<template>
  <div>
    <v-card-title class="headline">
      {{ $t("recipe.ai-tab-youtube") }}
    </v-card-title>
    <v-card-text>
      <p>{{ $t("recipe.ai-youtube-description") }}</p>
    </v-card-text>

    <v-form
      ref="domYoutubeForm"
      class="mt-4"
      @submit.prevent="createFromYoutube"
    >
      <v-text-field
        v-model="youtubeUrl"
        :label="$t('recipe.ai-youtube-url-label')"
        :prepend-inner-icon="$globals.icons.link"
        validate-on="blur"
        variant="solo-filled"
        clearable
        class="rounded-lg mt-2"
        rounded
        :rules="[youtubeUrlValidator]"
        :hint="$t('recipe.ai-youtube-url-hint')"
        persistent-hint
        @blur="fetchYoutubePreview"
      />
      <v-card
        v-if="youtubeThumbnail"
        class="mt-4"
        variant="outlined"
      >
        <v-card-title class="text-subtitle-2">
          {{ $t("recipe.ai-youtube-preview-title") }}
        </v-card-title>
        <v-img
          :src="youtubeThumbnail"
          :alt="youtubeTitle ? youtubeTitle : ''"
          max-height="200"
          cover
        />
        <v-card-text v-if="youtubeTitle" class="text-body-2 pt-2">
          {{ youtubeTitle }}
        </v-card-text>
      </v-card>
      <v-select
        v-model="targetLanguage"
        :items="languageOptions"
        :label="$t('recipe.ai-target-language-label')"
        :hint="$t('recipe.ai-target-language-hint')"
        persistent-hint
        clearable
        class="mt-4"
        variant="outlined"
      />
      <v-checkbox
        v-model="correctGrammar"
        color="primary"
        hide-details
        :label="$t('recipe.ai-correct-grammar-label')"
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
            :disabled="!youtubeUrl || youtubeUrl === ''"
            rounded
            block
            type="submit"
            :loading="youtubeLoading"
          />
        </div>
      </v-card-actions>
      <p v-if="youtubeLoading" class="text-center mb-0">
        {{ $t("recipe.ai-please-wait-youtube-processing") }}
      </p>
      <v-alert
        v-if="importStarted"
        color="info"
        class="mt-4"
        variant="tonal"
      >
        <v-card-title class="ma-0 pa-0">
          <v-icon
            start
            size="x-large"
          >
            {{ $globals.icons.bell }}
          </v-icon>
          Import Started
        </v-card-title>
        <v-divider class="my-3 mx-2" />
        <p>Your YouTube recipe import has started in the background.</p>
        <p class="mb-0">
          You will receive a notification when it's complete. You can navigate away from this page.
        </p>
      </v-alert>
    </v-form>
    <v-expand-transition>
      <v-alert
        v-if="youtubeError"
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
        <p>{{ youtubeErrorMessage ? youtubeErrorMessage : $t("new-recipe.error-details") }}</p>
      </v-alert>
    </v-expand-transition>
  </div>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import type { VForm } from "~/types/auto-forms";

// Common languages for recipe translation
const LANGUAGE_OPTIONS = [
  { title: "English", value: "English" },
  { title: "Romanian", value: "Romanian" },
  { title: "French", value: "French" },
  { title: "German", value: "German" },
  { title: "Spanish", value: "Spanish" },
  { title: "Italian", value: "Italian" },
  { title: "Portuguese", value: "Portuguese" },
  { title: "Dutch", value: "Dutch" },
  { title: "Polish", value: "Polish" },
  { title: "Russian", value: "Russian" },
  { title: "Japanese", value: "Japanese" },
  { title: "Chinese", value: "Chinese" },
  { title: "Korean", value: "Korean" },
  { title: "Turkish", value: "Turkish" },
  { title: "Arabic", value: "Arabic" },
  { title: "Hindi", value: "Hindi" },
];

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      key: route => route.path,
    });

    const api = useUserApi();

    const { stayInEditMode, parseRecipe } = useNewRecipeOptions();

    const youtubeUrl = ref<string | null>(null);
    const youtubeLoading = ref(false);
    const youtubeError = ref(false);
    const youtubeErrorMessage = ref<string | null>(null);
    const youtubeThumbnail = ref<string | null>(null);
    const youtubeTitle = ref<string | null>(null);
    const domYoutubeForm = ref<VForm | null>(null);
    const targetLanguage = ref<string | null>(null);
    const correctGrammar = ref(true);
    const importStarted = ref(false);

    const languageOptions = LANGUAGE_OPTIONS;

    function youtubeUrlValidator(v: string) {
      return /^https?:\/\/(www\.)?(youtube\.com\/(watch\?v=|shorts\/|embed\/)|youtu\.be\/)/.test(v) || "Please enter a valid YouTube URL";
    }

    async function fetchYoutubePreview() {
      if (!youtubeUrl.value) return;
      try {
        const res = await fetch(
          `https://www.youtube.com/oembed?url=${encodeURIComponent(youtubeUrl.value)}&format=json`,
        );
        if (!res.ok) return;
        const data = await res.json();
        youtubeThumbnail.value = data.thumbnail_url ?? null;
        youtubeTitle.value = data.title ?? null;
      }
      catch {
        // Non-critical — silently ignore
      }
    }

    async function createFromYoutube() {
      if (!youtubeUrl.value) return;

      youtubeLoading.value = true;
      youtubeError.value = false;
      youtubeErrorMessage.value = null;
      importStarted.value = false;

      const { data, error } = await api.recipes.createOneFromYoutube(
        youtubeUrl.value,
        targetLanguage.value ?? undefined,
        correctGrammar.value,
      );

      youtubeLoading.value = false;

      if (error || !data) {
        youtubeError.value = true;
        youtubeErrorMessage.value = (error as any)?.response?.data?.detail?.message ?? null;
        return;
      }

      // Import started successfully - show info message
      importStarted.value = true;
    }

    return {
      youtubeUrl,
      youtubeLoading,
      youtubeError,
      youtubeErrorMessage,
      youtubeThumbnail,
      youtubeTitle,
      domYoutubeForm,
      stayInEditMode,
      parseRecipe,
      targetLanguage,
      correctGrammar,
      languageOptions,
      importStarted,
      youtubeUrlValidator,
      fetchYoutubePreview,
      createFromYoutube,
    };
  },
});
</script>
