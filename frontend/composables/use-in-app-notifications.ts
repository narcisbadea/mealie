/**
 * Composable for managing in-app notifications.
 * Provides reactive state for notifications and methods to interact with them.
 */
import type { InAppNotificationOut, InAppNotificationSummary } from "~/lib/api/user/notifications";

const POLLING_INTERVAL = 30000; // 30 seconds

// Global state for notifications
const notifications = ref<InAppNotificationOut[]>([]);
const summary = ref<InAppNotificationSummary>({ unread_count: 0, has_unread: false });
const isLoading = ref(false);
let pollingTimer: ReturnType<typeof setInterval> | null = null;

export function useInAppNotifications() {
  const api = useUserApi();

  async function fetchSummary() {
    const { data } = await api.notifications.getSummary();
    if (data) {
      summary.value = data;
    }
  }

  async function fetchNotifications(includeRead = false) {
    isLoading.value = true;
    try {
      const { data } = await api.notifications.getAll(includeRead);
      if (data) {
        notifications.value = data;
      }
    }
    finally {
      isLoading.value = false;
    }
  }

  async function markAsRead(notificationIds?: string[]) {
    await api.notifications.markAsRead({ notification_ids: notificationIds });
    await fetchSummary();
    await fetchNotifications();
  }

  async function markAllAsRead() {
    await api.notifications.markAsRead({});
    await fetchSummary();
    await fetchNotifications();
  }

  async function deleteNotification(id: string) {
    await api.notifications.deleteOne(id);
    await fetchSummary();
    await fetchNotifications();
  }

  async function deleteAllRead() {
    await api.notifications.deleteAllRead();
    await fetchNotifications();
  }

  function startPolling() {
    if (pollingTimer) return;

    // Fetch immediately
    fetchSummary();

    // Then poll
    pollingTimer = setInterval(() => {
      fetchSummary();
    }, POLLING_INTERVAL);
  }

  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  }

  return {
    // State
    notifications,
    summary,
    isLoading,

    // Actions
    fetchSummary,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    deleteAllRead,
    startPolling,
    stopPolling,
  };
}
