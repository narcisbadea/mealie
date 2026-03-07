<template>
  <v-app dark>
    <TheSnackbar />

    <AppHeader>
      <v-btn
        icon
        @click.stop="sidebar = !sidebar"
      >
        <v-icon> {{ $globals.icons.menu }}</v-icon>
      </v-btn>
    </AppHeader>

    <AppSidebar
      v-model="sidebar"
      absolute
      :top-link="topLinks"
      :secondary-links="cookbookLinks || []"
    />

    <!-- Contextual FAB for recipe pages -->
    <RecipeCreateFab
      v-if="showCreateFab && groupSlug"
      :group-slug="groupSlug"
    />

    <v-main class="pt-12">
      <v-scroll-x-transition>
        <div>
          <NuxtPage />
        </div>
      </v-scroll-x-transition>
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { SideBarLink } from "~/types/application-types";
import { useCookbookPreferences } from "~/composables/use-users/preferences";
import { useCookbookStore, usePublicCookbookStore } from "~/composables/store/use-cookbook-store";
import type { ReadCookBook } from "~/lib/api/types/cookbook";
import RecipeCreateFab from "./LayoutParts/RecipeCreateFab.vue";

export default defineNuxtComponent({
  components: { RecipeCreateFab },
  setup() {
    const i18n = useI18n();
    const { $globals } = useNuxtApp();
    const display = useDisplay();
    const auth = useMealieAuth();
    const { isOwnGroup } = useLoggedInState();

    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

    // Show FAB only on recipe-related pages
    const showCreateFab = computed(() => {
      const path = route.path;
      // Show on main recipes page, recipe finder, categories, tags, tools, cookbooks
      const recipePages = [
        /^\/g\/[^/]+$/, // Main recipes page
        /^\/g\/[^/]+\/recipes/, // Recipe subpages (finder, categories, tags, tools, timeline)
        /^\/g\/[^/]+\/cookbooks/, // Cookbooks pages
      ];
      // Don't show on create pages themselves or recipe view pages
      const excludedPages = [
        /\/r\/create/, // Create pages
        /\/r\/[^/]+$/, // Recipe view page (slug only)
      ];

      const isRecipePage = recipePages.some(regex => regex.test(path));
      const isExcluded = excludedPages.some(regex => regex.test(path));

      return isOwnGroup.value && isRecipePage && !isExcluded;
    });

    const cookbookPreferences = useCookbookPreferences();
    const ownCookbookStore = useCookbookStore(i18n);
    const publicCookbookStoreCache = ref<Record<string, ReturnType<typeof usePublicCookbookStore>>>({});

    function getPublicCookbookStore(slug: string) {
      if (!publicCookbookStoreCache.value[slug]) {
        publicCookbookStoreCache.value[slug] = usePublicCookbookStore(slug, i18n);
      }
      return publicCookbookStoreCache.value[slug];
    }

    const cookbooks = computed(() => {
      if (isOwnGroup.value) {
        return ownCookbookStore.store.value;
      }
      else if (groupSlug.value) {
        const publicStore = getPublicCookbookStore(groupSlug.value);
        return unref(publicStore.store);
      }
      return [];
    });

    const sidebar = ref<boolean>(false);
    onMounted(() => {
      sidebar.value = display.lgAndUp.value;
    });

    function cookbookAsLink(cookbook: ReadCookBook): SideBarLink {
      return {
        key: cookbook.slug || "",
        icon: $globals.icons.pages,
        title: cookbook.name,
        to: `/g/${groupSlug.value}/cookbooks/${cookbook.slug || ""}`,
        restricted: false,
      };
    }

    const currentUserHouseholdId = computed(() => auth.user.value?.householdId);
    const cookbookLinks = computed<SideBarLink[]>(() => {
      if (!cookbooks.value?.length) {
        return [];
      }

      const sortedCookbooks = [...cookbooks.value].sort((a, b) => (a.position || 0) - (b.position || 0));

      const ownLinks: SideBarLink[] = [];
      const links: SideBarLink[] = [];
      const cookbooksByHousehold = sortedCookbooks.reduce((acc, cookbook) => {
        const householdName = cookbook.household?.name || "";
        (acc[householdName] ||= []).push(cookbook);
        return acc;
      }, {} as Record<string, ReadCookBook[]>);

      Object.entries(cookbooksByHousehold).forEach(([householdName, cookbooks]) => {
        if (!cookbooks.length) {
          return;
        }
        if (cookbooks[0].householdId === currentUserHouseholdId.value) {
          ownLinks.push(...cookbooks.map(cookbookAsLink));
        }
        else {
          links.push({
            key: householdName,
            icon: $globals.icons.book,
            title: householdName,
            children: cookbooks.map(cookbookAsLink),
            restricted: false,
          });
        }
      });

      links.sort((a, b) => a.title.localeCompare(b.title));
      if (auth.user.value && cookbookPreferences.value.hideOtherHouseholds) {
        return ownLinks;
      }
      else {
        return [...ownLinks, ...links];
      }
    });

    const topLinks = computed<SideBarLink[]>(() => [
      {
        icon: $globals.icons.silverwareForkKnife,
        to: `/g/${groupSlug.value}`,
        title: i18n.t("general.recipes"),
        restricted: false,
      },
      {
        icon: $globals.icons.search,
        to: `/g/${groupSlug.value}/recipes/finder`,
        title: i18n.t("recipe-finder.recipe-finder"),
        restricted: false,
      },
      {
        icon: $globals.icons.calendarMultiselect,
        title: i18n.t("meal-plan.meal-planner"),
        to: "/household/mealplan/planner/view",
        restricted: true,
      },
      {
        icon: $globals.icons.formatListCheck,
        title: i18n.t("shopping-list.shopping-lists"),
        to: "/shopping-lists",
        restricted: true,
      },
      {
        icon: $globals.icons.book,
        to: `/g/${groupSlug.value}/cookbooks`,
        title: i18n.t("cookbook.cookbooks"),
        restricted: true,
      },
      {
        icon: $globals.icons.folderOutline,
        title: i18n.t("general.organize"),
        restricted: true,
        childrenStartExpanded: false,
        children: [
          {
            icon: $globals.icons.timelineText,
            title: i18n.t("recipe.timeline"),
            to: `/g/${groupSlug.value}/recipes/timeline`,
            restricted: true,
          },
          {
            icon: $globals.icons.categories,
            to: `/g/${groupSlug.value}/recipes/categories`,
            title: i18n.t("sidebar.categories"),
            restricted: true,
          },
          {
            icon: $globals.icons.tags,
            to: `/g/${groupSlug.value}/recipes/tags`,
            title: i18n.t("sidebar.tags"),
            restricted: true,
          },
          {
            icon: $globals.icons.potSteam,
            to: `/g/${groupSlug.value}/recipes/tools`,
            title: i18n.t("tool.tools"),
            restricted: true,
          },
        ],
      },
    ]);

    return {
      groupSlug,
      cookbookLinks,
      topLinks,
      isOwnGroup,
      showCreateFab,
      sidebar,
    };
  },
});
</script>
