<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import ToastContainer from './components/layout/ToastContainer.vue'
import AIPanel from './components/ai/AIPanel.vue'
import AITrigger from './components/ai/AITrigger.vue'
import { useAuthStore } from './stores/auth'
import { useUIStore } from './stores/ui'
import { useSwipeGesture } from './composables/useSwipeGesture'

const auth = useAuthStore()
const ui = useUIStore()
const route = useRoute()
const showLayout = computed(() => auth.isAuthenticated && route.name !== 'login')

const { cleanup } = useSwipeGesture({
  onSwipeRight: () => { ui.sidebarOpen = true },
  onSwipeLeft: () => { ui.closeSidebar() },
  edgeOnly: true,
})

onMounted(() => {
  auth.initUser()
})

onUnmounted(() => {
  cleanup()
})
</script>

<template>
  <div class="app">
    <template v-if="showLayout">
      <AppSidebar />
      <div
        v-if="ui.sidebarOpen"
        class="sidebar-overlay"
        @click="ui.closeSidebar()"
      />
      <div class="main-area">
        <AppHeader />
        <main class="content">
          <router-view />
        </main>
      </div>
    </template>
    <template v-else>
      <router-view />
    </template>
    <ToastContainer />
    <!-- Global AI Layer -->
    <template v-if="showLayout">
      <AITrigger />
      <AIPanel />
    </template>
  </div>
</template>

<style>
:root {
  --bg-app: #f5f7fa;
  --bg-surface: #ffffff;
  --bg-surface-alt: #f9fafb;
  --bg-surface-hover: #f3f4f6;
  --bg-input: #ffffff;
  --text-primary: #111111;
  --text-secondary: #555555;
  --text-muted: #9ca3af;
  --border-default: #e5e7eb;
  --border-input: #d1d5db;
  --brand-primary: #4f46e5;
  --brand-primary-hover: #4338ca;
}

html.dark {
  --bg-app: #0f1117;
  --bg-surface: #1c1c27;
  --bg-surface-alt: #252535;
  --bg-surface-hover: #2e2e42;
  --bg-input: #252535;
  --text-primary: #f0f0f5;
  --text-secondary: #a0a0b8;
  --text-muted: #6b7280;
  --border-default: #2e2e42;
  --border-input: #3a3a54;
  --brand-primary: #6366f1;
  --brand-primary-hover: #818cf8;
}

*, *::before, *::after {
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}

body {
  margin: 0;
  background: var(--bg-app);
  color: var(--text-primary);
}

.app {
  display: flex;
  min-height: 100vh;
  background: var(--bg-app);
}
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
  min-width: 0;
}
.content {
  padding: 24px;
  flex: 1;
  overflow-x: auto;
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 768px) {
  .main-area {
    margin-left: 0;
  }
  .content {
    padding: 12px;
  }
  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}
</style>
