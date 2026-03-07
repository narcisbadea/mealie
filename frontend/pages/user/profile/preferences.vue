<template>
  <v-container class="pa-0">
    <BaseCardSectionTitle
      :title="$t('profile.preferences')"
    />
    <v-card variant="outlined" style="border-color: lightgrey;">
      <v-card-text>
        <v-combobox
          v-model="selectedDefaultActivity"
          :label="$t('user.default-activity')"
          :items="activityOptions"
          :hint="$t('user.default-activity-hint')"
          density="comfortable"
          variant="underlined"
          validate-on="blur"
          persistent-hint
        />
        <v-checkbox
          v-model="userCopy.advanced"
          :label="$t('profile.show-advanced-description')"
          color="primary"
          @change="updateUser"
        />
      </v-card-text>
    </v-card>
    <nuxt-link
      class="mt-5 d-flex flex-column justify-center text-center"
      :to="`/group`"
    >
      {{ $t('profile.looking-for-privacy-settings') }}
    </nuxt-link>
  </v-container>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import { useUserActivityPreferences } from "~/composables/use-users/preferences";
import useDefaultActivity from "~/composables/use-default-activity";
import { ActivityKey } from "~/lib/api/types/activity";

export default defineNuxtComponent({
  name: "UserPreferences",
  setup() {
    const i18n = useI18n();
    const auth = useMealieAuth();
    const { getDefaultActivityLabels, getActivityLabel, getActivityKey } = useDefaultActivity();
    const user = computed(() => auth.user.value);

    const activityPreferences = useUserActivityPreferences();
    const activityOptions = getDefaultActivityLabels(i18n);
    const selectedDefaultActivity = ref(getActivityLabel(i18n, activityPreferences.value.defaultActivity));
    watch(selectedDefaultActivity, () => {
      activityPreferences.value.defaultActivity = getActivityKey(i18n, selectedDefaultActivity.value) ?? ActivityKey.RECIPES;
    });

    const userCopy = ref({ ...user.value });

    watch(user, () => {
      userCopy.value = { ...user.value };
    });

    const api = useUserApi();

    async function updateUser() {
      if (!userCopy.value?.id) return;
      const { response } = await api.users.updateOne(userCopy.value.id, userCopy.value);
      if (response?.status === 200) {
        auth.refresh();
      }
    }

    return {
      userCopy,
      selectedDefaultActivity,
      activityOptions,
      updateUser,
    };
  },
});
</script>
