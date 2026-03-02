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

    const youtubeUrl = ref<string | null>(null);
    const youtubeLoading = ref(false);
    const youtubeError = ref(false);
    const youtubeErrorMessage = ref<string | null>(null);
    const youtubeThumbnail = ref<string | null>(null);
    const youtubeTitle = ref<string | null>(null);
    const domYoutubeForm = ref<VForm | null>(null);

    const createPagePath = computed(() => `/g/${groupSlug.value}/r/create/youtube`);

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
      } catch {
        // Non-critical — silently ignore
      }
    }

    async function createFromYoutube() {
      if (!youtubeUrl.value) return;

      youtubeLoading.value = true;
      youtubeError.value = false;
      youtubeErrorMessage.value = null;

      const { data, error } = await api.recipes.createOneFromYoutube(youtubeUrl.value);

      if (error || !data) {
        youtubeError.value = true;
        youtubeErrorMessage.value = (error as any)?.response?.data?.detail?.message ?? null;
        youtubeLoading.value = false;
        return;
      }

      navigateToRecipe(data, groupSlug.value, createPagePath.value);
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
      youtubeUrlValidator,
      fetchYoutubePreview,
      createFromYoutube,
    };
  },
});
</script>