<template>
  <v-container v-if="user" class="mb-8">
    <section class="d-flex flex-column align-center mt-4">
      <UserAvatar
        :tooltip="false"
        size="96"
        :user-id="user.id"
      />

      <h2 class="text-h4 text-center">
        {{ $t('profile.welcome-user', [user.fullName]) }}
      </h2>
      <p class="subtitle-1 mb-0 text-center">
        {{ $t('profile.description') }}
      </p>
      <v-card
        flat
        color="transparent"
        width="100%"
        max-width="600px"
      >
        <v-card-actions class="d-flex justify-center my-4">
          <v-btn
            v-if="user.canInvite"
            variant="outlined"
            rounded
            :prepend-icon="$globals.icons.createAlt"
            :text="$t('profile.get-invite-link')"
            @click="inviteDialog = true"
          />
        </v-card-actions>
        <UserInviteDialog v-model="inviteDialog" />
      </v-card>
    </section>

    <!-- Tabbed Interface for User Settings -->
    <v-card variant="outlined" style="border-color: lightgray;" class="mt-4">
      <v-tabs v-model="activeTab" color="primary" class="border-b">
        <v-tab value="profile">
          {{ $t('settings.profile') }}
        </v-tab>
        <v-tab value="preferences">
          {{ $t('profile.preferences') }}
        </v-tab>
        <v-tab value="api-tokens">
          {{ $t('settings.token.api-tokens') }}
        </v-tab>
      </v-tabs>

      <v-card-text>
        <v-window v-model="activeTab">
          <v-window-item value="profile">
            <UserProfileEdit />
          </v-window-item>

          <v-window-item value="preferences">
            <UserPreferences />
          </v-window-item>

          <v-window-item value="api-tokens">
            <UserApiTokens />
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>

    <v-divider class="my-7" />

    <!-- Household Section -->
    <section>
      <div>
        <h3 class="text-h6">
          {{ $t('household.household') }}
        </h3>
        <p>{{ $t('profile.household-description') }}</p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManageHousehold"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.household-settings'), to: `/household` }"
            image="/svgs/manage-group-settings.svg"
          >
            <template #title>
              {{ $t('profile.household-settings') }}
            </template>
            {{ $t('profile.household-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-cookbooks'), to: `/g/${groupSlug}/cookbooks` }"
            image="/svgs/manage-cookbooks.svg"
          >
            <template #title>
              {{ $t('sidebar.cookbooks') }}
            </template>
            {{ $t('profile.cookbooks-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-members'), to: `/household/members` }"
            image="/svgs/manage-members.svg"
          >
            <template #title>
              {{ $t('profile.members') }}
            </template>
            {{ $t('profile.members-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            v-if="user.advanced"
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-webhooks'), to: `/household/webhooks` }"
              image="/svgs/manage-webhooks.svg"
            >
              <template #title>
                {{ $t('settings.webhooks.webhooks') }}
              </template>
              {{ $t('profile.webhooks-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-notifiers'), to: `/household/notifiers` }"
              image="/svgs/manage-notifiers.svg"
            >
              <template #title>
                {{ $t('profile.notifiers') }}
              </template>
              {{ $t('profile.notifiers-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
    <v-divider class="my-7" />
    <section v-if="user.canManage || user.canOrganize || user.advanced">
      <div>
        <h3 class="text-h6">
          {{ $t('group.group') }}
        </h3>
        <p>{{ $t('profile.group-description') }}</p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.group-settings'), to: `/group` }"
            image="/svgs/manage-group-settings.svg"
          >
            <template #title>
              {{ $t('profile.group-settings') }}
            </template>
            {{ $t('profile.group-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canOrganize"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :link="{ text: $t('profile.manage-data'), to: `/group/data/foods` }"
            image="/svgs/manage-recipes.svg"
          >
            <template #title>
              {{ $t('profile.manage-data') }}
            </template>
            {{ $t('profile.manage-data-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :link="{ text: $t('profile.manage-data-migrations'), to: `/group/migrations` }"
              image="/svgs/manage-data-migrations.svg"
            >
              <template #title>
                {{ $t('profile.data-migrations') }}
              </template>
              {{ $t('profile.data-migrations-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
  </v-container>
</template>

<script lang="ts">
import UserProfileLinkCard from "@/components/Domain/User/UserProfileLinkCard.vue";
import UserAvatar from "@/components/Domain/User/UserAvatar.vue";
import type { UserOut } from "~/lib/api/types/user";
import UserInviteDialog from "~/components/Domain/User/UserInviteDialog.vue";
import UserProfileEdit from "./edit.vue";
import UserApiTokens from "./api-tokens.vue";
import UserPreferences from "./preferences.vue";

export default defineNuxtComponent({
  name: "UserProfile",
  components: {
    UserInviteDialog,
    UserProfileLinkCard,
    UserAvatar,
    UserProfileEdit,
    UserApiTokens,
    UserPreferences,
  },
  scrollToTop: true,
  setup() {
    const i18n = useI18n();
    const auth = useMealieAuth();
    const { $appInfo } = useNuxtApp();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug || auth.user.value?.groupSlug || "");

    useSeoMeta({
      title: i18n.t("settings.profile"),
    });

    const user = computed<UserOut | null>(() => {
      const authUser = auth.user.value;
      if (!authUser) return null;

      // Override canInvite if password login is disabled
      const canInvite = !$appInfo.allowPasswordLogin ? false : authUser.canInvite;

      return {
        ...authUser,
        canInvite,
      };
    });

    const inviteDialog = ref(false);
    const activeTab = ref("profile");

    return {
      groupSlug,
      inviteDialog,
      user,
      activeTab,
    };
  },
});
</script>
