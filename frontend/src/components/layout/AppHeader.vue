<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotificationStore } from '../../stores/notification'

const auth = useAuthStore()
const notifStore = useNotificationStore()
const route = useRoute()
const showNotifPanel = ref(false)

const pageTitle = computed(() => {
  return (route.meta.title as string) || 'AIStarlight'
})

onMounted(() => {
  notifStore.fetchUnreadCount()
  // Poll every 60s
  setInterval(() => notifStore.fetchUnreadCount(), 60000)
})

function toggleNotifPanel() {
  showNotifPanel.value = !showNotifPanel.value
  if (showNotifPanel.value) {
    notifStore.fetchNotifications()
  }
}

function handleMarkAllRead() {
  notifStore.markAllRead()
}

function handleMarkRead(id: string) {
  notifStore.markRead(id)
}
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>
    <div class="header-right">
      <!-- Notification bell -->
      <div class="notif-wrapper">
        <button class="notif-bell" @click="toggleNotifPanel" title="Notifications">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <span v-if="notifStore.unreadCount > 0" class="notif-badge">{{ notifStore.unreadCount > 99 ? '99+' : notifStore.unreadCount }}</span>
        </button>
        <div v-if="showNotifPanel" class="notif-panel">
          <div class="notif-header">
            <strong>Notifications</strong>
            <button v-if="notifStore.unreadCount > 0" class="mark-all-btn" @click="handleMarkAllRead">Mark all read</button>
          </div>
          <div class="notif-list" v-if="notifStore.notifications.length">
            <div
              v-for="n in notifStore.notifications"
              :key="n.id"
              class="notif-item"
              :class="{ unread: !n.is_read }"
              @click="handleMarkRead(n.id)"
            >
              <div class="notif-title">{{ n.title }}</div>
              <div class="notif-msg">{{ n.message }}</div>
              <div class="notif-time">{{ new Date(n.created_at).toLocaleDateString() }}</div>
            </div>
          </div>
          <div v-else class="notif-empty">No notifications</div>
        </div>
      </div>
      <span class="user-info" v-if="auth.user">
        {{ auth.user.full_name || auth.user.email }}
      </span>
    </div>
  </header>
</template>

<style scoped>
.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #111;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info {
  font-size: 14px;
  color: #555;
}
/* Notification bell */
.notif-wrapper {
  position: relative;
}
.notif-bell {
  background: none;
  border: none;
  cursor: pointer;
  color: #555;
  position: relative;
  padding: 4px;
}
.notif-bell:hover { color: #111; }
.notif-badge {
  position: absolute;
  top: -4px;
  right: -6px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 5px;
  min-width: 16px;
  text-align: center;
  line-height: 14px;
}
.notif-panel {
  position: absolute;
  top: 36px;
  right: 0;
  width: 360px;
  max-height: 400px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 100;
  overflow-y: auto;
}
.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}
.mark-all-btn {
  background: none;
  border: none;
  color: #4f46e5;
  font-size: 12px;
  cursor: pointer;
}
.notif-item {
  padding: 10px 16px;
  border-bottom: 1px solid #f9fafb;
  cursor: pointer;
}
.notif-item:hover { background: #f9fafb; }
.notif-item.unread { background: #eef2ff; }
.notif-title { font-size: 13px; font-weight: 600; color: #111; }
.notif-msg { font-size: 12px; color: #6b7280; margin-top: 2px; }
.notif-time { font-size: 11px; color: #9ca3af; margin-top: 4px; }
.notif-empty { padding: 24px; text-align: center; color: #9ca3af; font-size: 13px; }
</style>
