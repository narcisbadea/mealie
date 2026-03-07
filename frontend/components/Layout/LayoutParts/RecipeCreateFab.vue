<template>
  <v-menu
    v-model="isOpen"
    :close-on-content-click="false"
    location="top"
    origin="auto"
    transition="scale-transition"
  >
    <template #activator="{ props: menuProps }">
      <v-btn
        v-bind="menuProps"
        color="primary"
        icon
        size="large"
        class="create-fab"
        elevation="8"
      >
        <v-icon size="large">
          {{ $globals.icons.createAlt }}
        </v-icon>
      </v-btn>
    </template>

    <v-list
      density="comfortable"
      class="mb-0 mt-1 py-0"
      variant="flat"
      min-width="280"
    >
      <template v-for="(item, index) in createLinks" :key="item.title">
        <div v-if="!item.hide">
          <v-divider v-if="item.insertDivider" :key="index" class="mx-2" />
          <v-list-item
            v-if="!item.restricted || isOwnGroup"
            :key="item.title"
            :to="item.to"
            exact
            class="my-1"
            @click="isOpen = false"
          >
            <template #prepend>
              <v-icon
                size="40"
                :icon="item.icon"
              />
            </template>
            <v-list-item-title class="font-weight-medium" style="font-size: small;">
              {{ item.title }}
            </v-list-item-title>
            <v-list-item-subtitle class="font-weight-medium" style="font-size: small;">
              {{ item.subtitle }}
            </v-list-item-subtitle>
          </v-list-item>
        </div>
      </template>
    </v-list>
  </v-menu>
</template>

<script lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";

interface CreateLink {
  insertDivider: boolean;
  icon: string;
  title: string;
  subtitle: string;
  to: string;
  restricted: boolean;
  hide: boolean;
}

export default defineNuxtComponent({
  name: "RecipeCreateFab",
  props: {
    groupSlug: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const { $appInfo, $globals } = useNuxtApp();
    const i18n = useI18n();
    const { isOwnGroup } = useLoggedInState();

    const isOpen = ref(false);
    const showImageImport = computed(() => $appInfo.enableOpenaiImageServices);

    const createLinks = computed<CreateLink[]>(() => [
      {
        insertDivider: false,
        icon: $globals.icons.link,
        title: i18n.t("general.import"),
        subtitle: i18n.t("new-recipe.import-by-url"),
        to: `/g/${props.groupSlug}/r/create/url`,
        restricted: true,
        hide: false,
      },
      {
        insertDivider: false,
        icon: $globals.icons.robot,
        title: i18n.t("recipe.ai-tab-text"),
        subtitle: i18n.t("recipe.ai-text-description"),
        to: `/g/${props.groupSlug}/r/create/text`,
        restricted: true,
        hide: !$appInfo.enableOpenai,
      },
      {
        insertDivider: false,
        icon: $globals.icons.video,
        title: i18n.t("recipe.ai-tab-youtube"),
        subtitle: i18n.t("recipe.ai-youtube-description"),
        to: `/g/${props.groupSlug}/r/create/youtube`,
        restricted: true,
        hide: !$appInfo.enableOpenai,
      },
      {
        insertDivider: false,
        icon: $globals.icons.video,
        title: i18n.t("recipe.ai-tab-tiktok"),
        subtitle: i18n.t("recipe.ai-tiktok-description"),
        to: `/g/${props.groupSlug}/r/create/tiktok`,
        restricted: true,
        hide: !$appInfo.enableOpenai,
      },
      {
        insertDivider: false,
        icon: $globals.icons.fileImage,
        title: i18n.t("recipe.create-from-images"),
        subtitle: i18n.t("recipe.create-recipe-from-an-image"),
        to: `/g/${props.groupSlug}/r/create/image`,
        restricted: true,
        hide: !showImageImport.value,
      },
      {
        insertDivider: true,
        icon: $globals.icons.edit,
        title: i18n.t("general.create"),
        subtitle: i18n.t("new-recipe.create-manually"),
        to: `/g/${props.groupSlug}/r/create/new`,
        restricted: true,
        hide: false,
      },
    ]);

    return {
      isOpen,
      createLinks,
      isOwnGroup,
    };
  },
});
</script>

<style scoped>
.create-fab {
  position: fixed !important;
  bottom: 24px !important;
  right: 24px !important;
  z-index: 1000 !important;
}
</style>
