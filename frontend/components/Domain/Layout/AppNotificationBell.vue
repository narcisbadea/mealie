<template>
  <BaseDialog
    v-model="deleteDialog"
    :title="$t('general.confirm')"
    color="error"
    :icon="$globals.icons.alertCircle"
    can-confirm
    @confirm="executeDelete"
    @cancel="cancelDelete"
  >
    <v-card-text>
      {{ $t('general.delete-confirmation') }}
    </v-card-text>
  </BaseDialog>
  <v-menu
    v-model="menuOpen"
    :close-on-content-click="false"
    location="bottom end"
    max-width="400"
  >
    <template #activator="{ props: menuProps }">
      <v-btn
        icon
        v-bind="menuProps"
        :color="hasUnread ? 'warning' : undefined"
      >
        <v-badge
          :model-value="hasUnread"
          color="error"
          dot
          floating
        >
          <v-icon>{{ $globals.icons.bell }}</v-icon>
        </v-badge>
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center justify-space-between pa-3">
        <span>Notifications</span>
        <div class="d-flex ga-1">
          <v-btn
            v-if="hasReadNotifications"
            variant="text"
            size="small"
            color="grey"
            @click="deleteAllRead"
          >
            Clear read
          </v-btn>
          <v-btn
            v-if="hasUnread"
            variant="text"
            size="small"
            color="primary"
            @click="markAllAsRead"
          >
            Mark all read
          </v-btn>
        </div>
      </v-card-title>

      <v-divider />

      <v-list
        v-if="notifications.length > 0"
        density="compact"
        max-height="400"
        class="overflow-y-auto"
      >
        <template
          v-for="notification in notifications"
          :key="notification.id"
        >
          <v-list-item
            :class="{ 'bg-grey-lighten-4': !notification.read_at }"
            @click="handleNotificationClick(notification)"
          >
            <template #prepend>
              <v-icon
                :color="getNotificationColor(notification)"
                start
              >
                {{ getNotificationIcon(notification) }}
              </v-icon>
            </template>

            <v-list-item-title>{{ notification.title }}</v-list-item-title>
            <v-list-item-subtitle>{{ notification.message }}</v-list-item-subtitle>
            <v-list-item-subtitle class="text-caption text-grey">
              {{ formatTimeAgo(notification.created_at) }}
            </v-list-item-subtitle>

            <template #append>
              <v-btn
                icon
                variant="text"
                size="small"
                color="grey"
                @click.stop="confirmDelete(notification)"
              >
                <v-icon size="18">
                  {{ $globals.icons.delete }}
                </v-icon>
              </v-btn>
            </template>
          </v-list-item>
          <v-divider />
        </template>
      </v-list>

      <v-card-text
        v-else-if="!isLoading"
        class="text-center text-grey py-8"
      >
        <v-icon
          size="48"
          color="grey-lighten-1"
        >
          {{ $globals.icons.bellOutline }}
        </v-icon>
        <p class="mt-2 mb-0">
          No notifications
        </p>
      </v-card-text>

      <v-card-text
        v-else
        class="text-center py-8"
      >
        <v-progress-circular
          indeterminate
          color="primary"
        />
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script lang="ts">
import type { InAppNotificationOut } from "~/lib/api/user/notifications";
import { useInAppNotifications } from "~/composables/use-in-app-notifications";
import BaseDialog from "~/components/global/BaseDialog.vue";

export default defineNuxtComponent({
  name: "AppNotificationBell",
  components: { BaseDialog },

  setup() {
    const { $globals } = useNuxtApp();
    const router = useRouter();
    const route = useRoute();
    const auth = useMealieAuth();

    const {
      notifications,
      summary,
      isLoading,
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      deleteAllRead,
      startPolling,
      stopPolling,
    } = useInAppNotifications();

    const menuOpen = ref(false);
    const deleteDialog = ref(false);
    const notificationToDelete = ref<InAppNotificationOut | null>(null);

    const hasUnread = computed(() => summary.value.has_unread);
    const hasReadNotifications = computed(() =>
      notifications.value.some(n => n.read_at),
    );

    // Fetch notifications when menu opens
    watch(menuOpen, async (isOpen) => {
      if (isOpen) {
        await fetchNotifications();
      }
    });

    // Start polling on mount, stop on unmount
    onMounted(() => {
      startPolling();
    });

    onUnmounted(() => {
      stopPolling();
    });

    function getNotificationIcon(notification: InAppNotificationOut): string {
      if (notification.notification_type === "video_import_success") {
        return $globals.icons.checkCircle;
      }
      if (notification.notification_type === "video_import_failure") {
        return $globals.icons.alertCircle;
      }
      return $globals.icons.bell;
    }

    function getNotificationColor(notification: InAppNotificationOut): string {
      if (notification.notification_type === "video_import_success") {
        return "success";
      }
      if (notification.notification_type === "video_import_failure") {
        return "error";
      }
      return "primary";
    }

    function formatTimeAgo(dateString: string): string {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    }

    async function handleNotificationClick(notification: InAppNotificationOut) {
      // Mark as read
      if (!notification.read_at) {
        await markAsRead([notification.id]);
      }

      // Navigate if it's a video import success with recipe data
      if (
        notification.notification_type === "video_import_success"
        && notification.data?.recipe_slug
      ) {
        const groupSlug = route.params.groupSlug as string || auth.user.value?.groupSlug || "";
        const recipeSlug = notification.data.recipe_slug as string;
        router.push(`/g/${groupSlug}/r/${recipeSlug}`);
      }

      menuOpen.value = false;
    }

    function confirmDelete(notification: InAppNotificationOut) {
      notificationToDelete.value = notification;
      deleteDialog.value = true;
    }

    async function executeDelete() {
      if (notificationToDelete.value) {
        await deleteNotification(notificationToDelete.value.id);
        notificationToDelete.value = null;
      }
      deleteDialog.value = false;
    }

    function cancelDelete() {
      notificationToDelete.value = null;
      deleteDialog.value = false;
    }

    return {
      menuOpen,
      notifications,
      isLoading,
      hasUnread,
      hasReadNotifications,
      deleteDialog,
      markAllAsRead,
      deleteAllRead,
      getNotificationIcon,
      getNotificationColor,
      formatTimeAgo,
      handleNotificationClick,
      confirmDelete,
      executeDelete,
      cancelDelete,
    };
  },
});
</script>
