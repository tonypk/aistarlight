<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotificationStore } from '../../stores/notification'
import { useUIStore } from '../../stores/ui'

const auth = useAuthStore()
const notifStore = useNotificationStore()
const ui = useUIStore()
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
      <button class="hamburger-btn" @click="ui.toggleSidebar()" aria-label="Toggle sidebar">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>
    <div class="header-right">
      <!-- Dark mode toggle -->
      <button class="theme-toggle" @click="ui.toggleDarkMode()" :title="ui.isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'">
        <svg v-if="ui.isDarkMode" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
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
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.hamburger-btn {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
}
.hamburger-btn:hover { color: var(--text-primary); }
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info {
  font-size: 14px;
  color: var(--text-secondary);
}
/* Theme toggle */
.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
  display: flex;
  align-items: center;
}
.theme-toggle:hover { color: var(--text-primary); }
/* Notification bell */
.notif-wrapper {
  position: relative;
}
.notif-bell {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  position: relative;
  padding: 4px;
}
.notif-bell:hover { color: var(--text-primary); }
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
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
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
  border-bottom: 1px solid var(--border-default);
  color: var(--text-primary);
}
.mark-all-btn {
  background: none;
  border: none;
  color: var(--brand-primary);
  font-size: 12px;
  cursor: pointer;
}
.notif-item {
  padding: 10px 16px;
  border-bottom: 1px solid var(--bg-surface-alt);
  cursor: pointer;
}
.notif-item:hover { background: var(--bg-surface-alt); }
.notif-item.unread { background: #eef2ff; }
html.dark .notif-item.unread { background: rgba(99, 102, 241, 0.15); }
.notif-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.notif-msg { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.notif-time { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.notif-empty { padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px; }

@media (max-width: 768px) {
  .hamburger-btn {
    display: flex;
  }
  .header {
    padding: 0 12px;
  }
}
</style>
