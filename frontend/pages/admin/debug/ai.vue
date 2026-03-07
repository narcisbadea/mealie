<template>
  <v-container class="pa-0">
    <v-container>
      <BaseCardSectionTitle :title="$t('admin.debug-openai-services')">
        {{ $t('admin.debug-openai-services-description') }}
        <br>
        <DocLink
          class="mt-2"
          link="/documentation/getting-started/installation/open-ai"
        />
      </BaseCardSectionTitle>
    </v-container>
    <v-form
      ref="uploadForm"
      @submit.prevent="testAI"
    >
      <div>
        <v-card-text>
          <v-container class="pa-0">
            <v-row>
              <v-col
                cols="auto"
                align-self="center"
              >
                <AppButtonUpload
                  v-if="!uploadedImage"
                  class="ml-auto"
                  url="none"
                  file-name="image"
                  accept="image/*"
                  :text="$t('recipe.upload-image')"
                  :text-btn="false"
                  :post="false"
                  @uploaded="uploadImage"
                />
                <v-btn
                  v-if="!!uploadedImage"
                  color="error"
                  @click="clearImage"
                >
                  <v-icon start>
                    {{ $globals.icons.close }}
                  </v-icon>
                  {{ $t("recipe.remove-image") }}
                </v-btn>
              </v-col>
              <v-spacer />
            </v-row>
            <v-row
              v-if="uploadedImage && uploadedImagePreviewUrl"
              style="max-width: 25%;"
            >
              <v-spacer />
              <v-col cols="12">
                <v-img :src="uploadedImagePreviewUrl" />
              </v-col>
              <v-spacer />
            </v-row>
            <!-- Model Selection Dropdown -->
            <v-row v-if="$appInfo.enableOpenai">
              <v-col cols="12">
                <v-select
                  v-model="selectedModel"
                  :items="modelOptions"
                  :label="$t('admin.select-model')"
                  :loading="loadingModels"
                  :disabled="loadingModels || models.length === 0"
                  variant="outlined"
                  clearable
                  :hint="$t('admin.model-selection-hint')"
                  persistent-hint
                />
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <BaseButton
            type="submit"
            :text="$t('admin.run-test')"
            :icon="$globals.icons.check"
            :loading="loading"
            class="ml-auto"
          />
        </v-card-actions>
      </div>
    </v-form>
    <v-divider
      v-if="response"
      class="mt-4"
    />
    <v-container
      v-if="response"
      class="ma-0 pa-0"
    >
      <v-card-title> {{ $t('admin.test-results') }} </v-card-title>
      <v-card-text> {{ response }} </v-card-text>
    </v-container>
  </v-container>
</template>

<script lang="ts">
import { useAdminApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { LLMModel } from "~/lib/api/types/admin";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      layout: "admin",
    });

    const api = useAdminApi();
    const i18n = useI18n();

    // Set page title
    useSeoMeta({
      title: i18n.t("admin.debug-openai-services"),
    });

    const loading = ref(false);
    const response = ref("");

    const uploadForm = ref<VForm | null>(null);
    const uploadedImage = ref<Blob | File>();
    const uploadedImageName = ref<string>("");
    const uploadedImagePreviewUrl = ref<string>();

    // Model selection state
    const models = ref<LLMModel[]>([]);
    const selectedModel = ref<string | null>(null);
    const loadingModels = ref(false);

    // Fetch available models on mount
    onMounted(async () => {
      await fetchModels();
    });

    async function fetchModels() {
      loadingModels.value = true;
      try {
        const { data } = await api.about.getAvailableModels();
        if (data) {
          models.value = data.models;
          if (data.currentModel && !selectedModel.value) {
            selectedModel.value = data.currentModel;
          }
        }
      }
      catch (e) {
        console.error("Failed to fetch models:", e);
      }
      finally {
        loadingModels.value = false;
      }
    }

    const modelOptions = computed(() => {
      return models.value.map(model => ({
        title: model.name,
        value: model.id,
      }));
    });

    function uploadImage(fileObject: File) {
      uploadedImage.value = fileObject;
      uploadedImageName.value = fileObject.name;
      uploadedImagePreviewUrl.value = URL.createObjectURL(fileObject);
    }

    function clearImage() {
      uploadedImage.value = undefined;
      uploadedImageName.value = "";
      uploadedImagePreviewUrl.value = undefined;
    }

    async function testAI() {
      response.value = "";

      loading.value = true;
      const { data } = await api.debug.debugAI(
        uploadedImage.value,
        uploadedImageName.value,
        selectedModel.value || undefined,
      );
      loading.value = false;

      if (!data) {
        alert.error("Unable to test AI services");
      }
      else {
        response.value = data.response || (data.success ? "Test Successful" : "Test Failed");
      }
    }

    return {
      loading,
      response,
      uploadForm,
      uploadedImage,
      uploadedImagePreviewUrl,
      models,
      selectedModel,
      loadingModels,
      modelOptions,
      uploadImage,
      clearImage,
      testAI,
    };
  },
});
</script>