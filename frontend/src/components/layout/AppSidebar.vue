<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const menuItems = [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Upload Data', path: '/upload', icon: '📤' },
  { name: 'Receipt Scanner', path: '/receipts', icon: '🧾' },
  { name: 'Classification', path: '/classification', icon: '🏷️' },
  { name: 'Reconciliation', path: '/reconciliation', icon: '🔍' },
  { name: 'Bank Recon', path: '/bank-reconciliation', icon: '🏦' },
  { name: 'Reports', path: '/reports', icon: '📋' },
  { name: 'Suppliers', path: '/suppliers', icon: '🏢' },
  { name: 'Withholding Tax', path: '/withholding', icon: '📑' },
  { name: 'Learning Insights', path: '/learning', icon: '🎓' },
  { name: 'AI Chat', path: '/chat', icon: '💬' },
  { name: 'Knowledge', path: '/knowledge', icon: '📚' },
  { name: 'Memory', path: '/memory', icon: '🧠' },
  { name: 'User Guide', path: '/guide', icon: '📖' },
  { name: 'Settings', path: '/settings', icon: '⚙️' },
]

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <h2>AIStarlight</h2>
      <p class="tagline">Tax Filing Assistant</p>
    </div>
    <nav>
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <span class="icon">{{ item.icon }}</span>
        {{ item.name }}
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <button class="logout-btn" @click="handleLogout">Logout</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}
.logo {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo h2 { font-size: 20px; }
.tagline { font-size: 12px; color: #888; margin-top: 4px; }
nav {
  flex: 1;
  padding: 12px 0;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #ccc;
  text-decoration: none;
  transition: background 0.2s;
}
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active {
  background: rgba(255,255,255,0.1);
  color: #fff;
  border-right: 3px solid #4f46e5;
}
.icon { font-size: 18px; }
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.logout-btn {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  color: #ccc;
  border-radius: 6px;
  cursor: pointer;
}
.logout-btn:hover { background: rgba(255,255,255,0.1); }
</style>
