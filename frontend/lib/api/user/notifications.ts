import { BaseAPI } from "../base/base-clients";

export interface InAppNotificationOut {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  data: Record<string, unknown> | null;
  created_at: string;
  read_at: string | null;
}

export interface InAppNotificationSummary {
  unread_count: number;
  has_unread: boolean;
}

export interface InAppNotificationMarkRead {
  notification_ids?: string[] | null;
}

const prefix = "/api";

const routes = {
  notifications: `${prefix}/users/notifications`,
  notificationsSummary: `${prefix}/users/notifications/summary`,
  notificationsMarkRead: `${prefix}/users/notifications/mark-read`,
  notificationItem: (id: string) => `${prefix}/users/notifications/${id}`,
};

export class NotificationsAPI extends BaseAPI {
  async getAll(includeRead = false, limit = 50) {
    return await this.requests.get<InAppNotificationOut[]>(
      routes.notifications,
      { include_read: includeRead, limit },
    );
  }

  async getSummary() {
    return await this.requests.get<InAppNotificationSummary>(routes.notificationsSummary);
  }

  async markAsRead(data: InAppNotificationMarkRead) {
    return await this.requests.post(routes.notificationsMarkRead, data);
  }

  async deleteOne(id: string) {
    return await this.requests.delete(routes.notificationItem(id));
  }

  async deleteAllRead() {
    return await this.requests.delete(routes.notifications);
  }
}
