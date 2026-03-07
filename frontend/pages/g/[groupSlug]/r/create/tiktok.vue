<template>
  <div>
    <v-card-title class="headline">
      TikTok Import
    </v-card-title>
    <v-card-text>
      <p>Import a recipe from a TikTok video. The video must have captions enabled.</p>
    </v-card-text>

    <v-form
      ref="domTiktokForm"
      class="mt-4"
      @submit.prevent="createFromTiktok"
    >
      <v-text-field
        v-model="tiktokUrl"
        label="TikTok Video URL"
        :prepend-inner-icon="$globals.icons.link"
        :rules="[tiktokUrlValidator]"
        validate-on="blur"
        variant="solo-filled"
        clearable
        class="rounded-lg mt-2"
        rounded
        hint="e.g. https://www.tiktok.com/@user/video/..."
        persistent-hint
        @blur="fetchTiktokPreview"
      />
      <v-card
        v-if="tiktokThumbnail"
        class="mt-4"
        variant="outlined"
      >
        <v-card-title class="text-subtitle-2">
          Video Preview
        </v-card-title>
        <v-img
          :src="tiktokThumbnail"
          :alt="tiktokTitle || ''"
          max-height="200"
          cover
        />
        <v-card-text v-if="tiktokTitle" class="text-body-2 pt-2">
          {{ tiktokTitle }}
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
        label="Stay in Edit mode"
      />
      <v-checkbox
        v-model="parseRecipe"
        color="primary"
        hide-details
        label="Parse recipe ingredients after import"
      />
      <v-card-actions class="justify-center">
        <div style="width: 250px">
          <BaseButton
            :disabled="!tiktokUrl"
            rounded
            block
            type="submit"
            :loading="tiktokLoading"
          />
        </div>
      </v-card-actions>
      <p v-if="tiktokLoading" class="text-center mb-0">
        Please wait, the TikTok video is being processed...
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
        <p>Your TikTok recipe import has started in the background.</p>
        <p class="mb-0">
          You will receive a notification when it's complete. You can navigate away from this page.
        </p>
      </v-alert>
    </v-form>
    <v-expand-transition>
      <v-alert
        v-if="tiktokError"
        color="error"
        class="mt-6"
      >
        <v-card-title class="ma-0 pa-0 text-white">
          Import Error
        </v-card-title>
        <v-divider class="my-3 mx-2" />
        <p class="text-white">
          {{ tiktokErrorMessage || 'An error occurred during import.' }}
        </p>
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

    const tiktokUrl = ref<string | null>(null);
    const tiktokLoading = ref(false);
    const tiktokError = ref(false);
    const tiktokErrorMessage = ref<string | null>(null);
    const tiktokThumbnail = ref<string | null>(null);
    const tiktokTitle = ref<string | null>(null);
    const domTiktokForm = ref<VForm | null>(null);
    const targetLanguage = ref<string | null>(null);
    const correctGrammar = ref(true);
    const importStarted = ref(false);

    const languageOptions = LANGUAGE_OPTIONS;

    function tiktokUrlValidator(v: string | null): boolean | string {
      if (!v) return true; // Required handled separately
      const pattern = /^https?:\/\/(www\.)?(tiktok\.com\/|vm\.tiktok\.com\/|vt\.tiktok\.com\/|m\.tiktok\.com\/)/i;
      return pattern.test(v) || "Please enter a valid TikTok URL";
    }

    async function fetchTiktokPreview() {
      if (!tiktokUrl.value) {
        return;
      }
      try {
        const oembedUrl = `https://www.tiktok.com/oembed?url=${encodeURIComponent(tiktokUrl.value)}`;
        const res = await fetch(oembedUrl);
        if (!res.ok) {
          return;
        }
        const data = await res.json();
        tiktokThumbnail.value = data.thumbnail_url || null;
        tiktokTitle.value = data.title || null;
      }
      catch (error) {
        console.error("[TikTok] Error fetching preview:", error);
      }
    }

    async function createFromTiktok() {
      if (!tiktokUrl.value) {
        return;
      }

      tiktokLoading.value = true;
      tiktokError.value = false;
      tiktokErrorMessage.value = null;
      importStarted.value = false;

      const { data, error } = await api.recipes.createOneFromTiktok(
        tiktokUrl.value,
        targetLanguage.value ?? undefined,
        correctGrammar.value,
      );

      tiktokLoading.value = false;

      if (error || !data) {
        tiktokError.value = true;
        tiktokErrorMessage.value = (error as any)?.response?.data?.detail?.message || null;
        return;
      }

      // Import started successfully - show info message
      importStarted.value = true;
    }

    return {
      tiktokUrl,
      tiktokLoading,
      tiktokError,
      tiktokErrorMessage,
      tiktokThumbnail,
      tiktokTitle,
      domTiktokForm,
      stayInEditMode,
      parseRecipe,
      targetLanguage,
      correctGrammar,
      languageOptions,
      importStarted,
      fetchTiktokPreview,
      createFromTiktok,
      tiktokUrlValidator,
    };
  },
});
</script>
