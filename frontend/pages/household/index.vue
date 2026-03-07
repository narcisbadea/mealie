<template>
  <v-container
    v-if="household"
    class="narrow-container"
  >
    <BasePageTitle class="mb-5">
      <template #header>
        <v-img
          width="100%"
          max-height="100"
          max-width="100"
          src="/svgs/manage-group-settings.svg"
        />
      </template>
      <template #title>
        {{ $t("profile.household-settings") }}
      </template>
      {{ $t("profile.household-description") }}
    </BasePageTitle>

    <!-- Tabbed Interface for Household Settings -->
    <v-card variant="outlined" style="border-color: lightgray;">
      <v-tabs v-model="activeTab" color="primary" class="border-b">
        <v-tab value="general">
          {{ $t('general.general') }}
        </v-tab>
        <v-tab value="members">
          {{ $t('profile.members') }}
        </v-tab>
        <v-tab value="notifications">
          {{ $t('profile.notifiers') }}
        </v-tab>
      </v-tabs>

      <v-card-text>
        <v-window v-model="activeTab">
          <!-- General Tab -->
          <v-window-item value="general">
            <v-form ref="refHouseholdEditForm" @submit.prevent="handleSubmit">
              <HouseholdPreferencesEditor v-if="household.preferences" v-model="household.preferences" />
              <div class="d-flex pa-2">
                <BaseButton type="submit" edit class="ml-auto">
                  {{ $t("general.update") }}
                </BaseButton>
              </div>
            </v-form>
          </v-window-item>

          <!-- Members Tab -->
          <v-window-item value="members">
            <HouseholdMembersTab />
          </v-window-item>

          <!-- Notifications Tab -->
          <v-window-item value="notifications">
            <HouseholdNotificationsTab />
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script lang="ts">
import HouseholdPreferencesEditor from "~/components/Domain/Household/HouseholdPreferencesEditor.vue";
import HouseholdMembersTab from "./members-tab.vue";
import HouseholdNotificationsTab from "./notifications-tab.vue";
import { useHouseholdSelf } from "~/composables/use-households";
import { alert } from "~/composables/use-toast";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  components: {
    HouseholdPreferencesEditor,
    HouseholdMembersTab,
    HouseholdNotificationsTab,
  },
  middleware: ["can-manage-household-only"],
  setup() {
    const { household, actions: householdActions } = useHouseholdSelf();
    const i18n = useI18n();

    useSeoMeta({
      title: i18n.t("household.household"),
    });

    const refHouseholdEditForm = ref<VForm | null>(null);
    const activeTab = ref("general");

    async function handleSubmit() {
      if (!refHouseholdEditForm.value?.validate() || !household.value?.preferences) {
        return;
      }

      const data = await householdActions.updatePreferences();
      if (data) {
        alert.success(i18n.t("settings.settings-updated"));
      }
      else {
        alert.error(i18n.t("settings.settings-update-failed"));
      }
    }

    return {
      household,
      householdActions,
      refHouseholdEditForm,
      handleSubmit,
      activeTab,
    };
  },
});
</script>

<style lang="css">
.preference-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 600px;
}
</style>
