import { defineStore } from "pinia";
import { ref } from "vue";
import {
  notificationsApi,
  type NotificationItem,
} from "../api/notifications";

export const useNotificationStore = defineStore("notification", () => {
  const notifications = ref<NotificationItem[]>([]);
  const unreadCount = ref(0);
  const total = ref(0);
  const loading = ref(false);

  async function fetchNotifications(page = 1) {
    loading.value = true;
    try {
      const res = await notificationsApi.list(page);
      notifications.value = [...(res.data.data || [])];
      total.value = res.data.meta?.total ?? res.data.data?.length ?? 0;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUnreadCount() {
    try {
      const res = await notificationsApi.unreadCount();
      unreadCount.value = res.data.data?.count ?? res.data.data ?? 0;
    } catch {
      // silent
    }
  }

  async function markRead(id: string) {
    await notificationsApi.markRead(id);
    notifications.value = notifications.value.map((n) =>
      n.id === id ? { ...n, is_read: true } : n
    );
    if (unreadCount.value > 0) unreadCount.value--;
  }

  async function markAllRead() {
    await notificationsApi.markAllRead();
    notifications.value = notifications.value.map((n) => ({
      ...n,
      is_read: true,
    }));
    unreadCount.value = 0;
  }

  return {
    notifications,
    unreadCount,
    total,
    loading,
    fetchNotifications,
    fetchUnreadCount,
    markRead,
    markAllRead,
  };
});
