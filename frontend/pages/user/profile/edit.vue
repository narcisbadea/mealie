<template>
  <v-container class="pa-0">
    <div class="d-flex flex-column align-center justify-center mb-4">
      <UserAvatar
        :tooltip="false"
        size="96"
        :user-id="userCopy.id!"
      />
      <AppButtonUpload
        class="my-1"
        file-name="profile"
        accept="image/*"
        :url="`/api/users/${userCopy.id}/image`"
        @uploaded="auth.refresh()"
      />
    </div>

    <ToggleState tag="article">
      <template #activator="{ toggle, state }">
        <v-btn
          v-if="!state && $appInfo.allowPasswordLogin"
          color="info"
          class="mb-n3"
          variant="outlined"
          @click="toggle"
        >
          <v-icon start>
            {{ $globals.icons.lock }}
          </v-icon>
          {{ $t("settings.change-password") }}
        </v-btn>
        <v-btn
          v-else-if="$appInfo.allowPasswordLogin"
          color="info"
          class="mb-n3"
          variant="outlined"
          @click="toggle"
        >
          <v-icon start>
            {{ $globals.icons.user }}
          </v-icon>
          {{ $t("settings.profile") }}
        </v-btn>
      </template>
      <template #default="{ state }">
        <v-slide-x-transition
          leave-absolute
          hide-on-leave
        >
          <div
            v-if="!state"
            key="personal-info"
          >
            <BaseCardSectionTitle
              class="mt-4"
              :title="$t('profile.personal-information')"
            />
            <v-card
              tag="article"
              variant="outlined"
              style="border-color: lightgrey;"
            >
              <v-card-text class="pb-0">
                <v-form ref="userUpdate">
                  <v-text-field
                    v-model="userCopy.username"
                    :label="$t('user.username')"
                    required
                    validate-on="blur"
                    density="comfortable"
                    variant="underlined"
                  />
                  <v-text-field
                    v-model="userCopy.fullName"
                    :label="$t('user.full-name')"
                    required
                    validate-on="blur"
                    density="comfortable"
                    variant="underlined"
                  />
                  <v-text-field
                    v-model="userCopy.email"
                    :label="$t('user.email')"
                    validate-on="blur"
                    required
                    density="comfortable"
                    variant="underlined"
                  />
                </v-form>
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <BaseButton
                  update
                  @click="updateUser"
                />
              </v-card-actions>
            </v-card>
          </div>
          <div
            v-else
            key="change-password"
          >
            <BaseCardSectionTitle
              class="mt-4"
              :title="$t('settings.change-password')"
            />
            <v-card variant="outlined" style="border-color: lightgrey;">
              <v-card-text class="pb-0">
                <v-form ref="passChange">
                  <v-text-field
                    v-model="password.current"
                    :prepend-icon="$globals.icons.lock"
                    :label="$t('user.current-password')"
                    validate-on="blur"
                    :type="showPassword ? 'text' : 'password'"
                    :append-icon="showPassword ? $globals.icons.eye : $globals.icons.eyeOff"
                    :rules="[validators.minLength(1)]"
                    density="comfortable"
                    variant="underlined"
                    @click:append="showPassword = !showPassword"
                  />
                  <v-text-field
                    v-model="password.newOne"
                    :prepend-icon="$globals.icons.lock"
                    :label="$t('user.new-password')"
                    :type="showPassword ? 'text' : 'password'"
                    :append-icon="showPassword ? $globals.icons.eye : $globals.icons.eyeOff"
                    :rules="[validators.minLength(8)]"
                    density="comfortable"
                    variant="underlined"
                    @click:append="showPassword = !showPassword"
                  />
                  <v-text-field
                    v-model="password.newTwo"
                    :prepend-icon="$globals.icons.lock"
                    :label="$t('user.confirm-password')"
                    :rules="[password.newOne === password.newTwo || $t('user.password-must-match')]"
                    validate-on="blur"
                    :type="showPassword ? 'text' : 'password'"
                    :append-icon="showPassword ? $globals.icons.eye : $globals.icons.eyeOff"
                    density="comfortable"
                    variant="underlined"
                    @click:append="showPassword = !showPassword"
                  />
                  <UserPasswordStrength v-model="password.newOne" />
                </v-form>
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <BaseButton
                  update
                  :disabled="!passwordsMatch || password.current.length < 0"
                  @click="updatePassword"
                />
              </v-card-actions>
            </v-card>
          </div>
        </v-slide-x-transition>
      </template>
    </ToggleState>
  </v-container>
</template>

<script lang="ts">
import { useUserApi } from "~/composables/api";
import UserAvatar from "~/components/Domain/User/UserAvatar.vue";
import UserPasswordStrength from "~/components/Domain/User/UserPasswordStrength.vue";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  name: "UserProfileEdit",
  components: {
    UserAvatar,
    UserPasswordStrength,
  },
  setup() {
    const auth = useMealieAuth();
    const user = computed(() => auth.user.value);

    watch(user, () => {
      userCopy.value = { ...user.value };
    });

    const userCopy = ref({ ...user.value });

    const api = useUserApi();

    const domUpdatePassword = ref<VForm | null>(null);
    const password = reactive({
      current: "",
      newOne: "",
      newTwo: "",
    });

    const passwordsMatch = computed(() => password.newOne === password.newTwo && password.newOne.length > 0);

    async function updateUser() {
      if (!userCopy.value?.id) return;
      const { response } = await api.users.updateOne(userCopy.value.id, userCopy.value);
      if (response?.status === 200) {
        auth.refresh();
      }
    }

    async function updatePassword() {
      if (!userCopy.value?.id) {
        return;
      }
      const { response } = await api.users.changePassword({
        currentPassword: password.current,
        newPassword: password.newOne,
      });

      if (response?.status === 200) {
        console.log("Password Changed");
      }
    }

    const state = reactive({
      hideImage: false,
      passwordLoading: false,
      showPassword: false,
      loading: false,
    });

    return {
      ...toRefs(state),
      updateUser,
      updatePassword,
      userCopy,
      password,
      domUpdatePassword,
      passwordsMatch,
      validators,
      auth,
    };
  },
});
</script>
