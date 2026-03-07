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
        <p class="text-white">{{ tiktokErrorMessage || 'An error occurred during import.' }}</p>
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

    const tiktokUrl = ref<string | null>(null);
    const tiktokLoading = ref(false);
    const tiktokError = ref(false);
    const tiktokErrorMessage = ref<string | null>(null);
    const tiktokThumbnail = ref<string | null>(null);
    const tiktokTitle = ref<string | null>(null);
    const domTiktokForm = ref<VForm | null>(null);

    const createPagePath = computed(() => `/g/${groupSlug.value}/r/create/tiktok`);

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
      } catch (error) {
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

      try {
        const { data, error } = await api.recipes.createOneFromTiktok(tiktokUrl.value);

        if (error || !data) {
          tiktokError.value = true;
          tiktokErrorMessage.value = (error as any)?.response?.data?.detail?.message || null;
          tiktokLoading.value = false;
          return;
        }

        navigateToRecipe(data, groupSlug.value, createPagePath.value);
      } catch (err) {
        console.error("[TikTok] Unexpected error:", err);
        tiktokError.value = true;
        tiktokLoading.value = false;
      }
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
      fetchTiktokPreview,
      createFromTiktok,
      tiktokUrlValidator,
    };
  },
});
</script>