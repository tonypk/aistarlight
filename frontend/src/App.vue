<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NMessageProvider, NDialogProvider, darkTheme, type GlobalThemeOverrides } from 'naive-ui'
import ToastContainer from './components/layout/ToastContainer.vue'
import { useUIStore } from './stores/ui'

const ui = useUIStore()
const theme = computed(() => ui.isDark ? darkTheme : null)

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2563eb',
    primaryColorHover: '#3b82f6',
    primaryColorPressed: '#1d4ed8',
    primaryColorSuppl: '#60a5fa',
  },
}
</script>

<template>
  <NConfigProvider :theme="theme" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <NDialogProvider>
        <router-view />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
  <ToastContainer />
</template>

<style>
:root,
[data-theme="light"] {
  --bg-app: #f8fafc;
  --bg-surface: #ffffff;
  --bg-surface-alt: #f9fafb;
  --bg-surface-hover: #f3f4f6;
  --bg-input: #ffffff;
  --text-primary: #111111;
  --text-secondary: #555555;
  --text-muted: #9ca3af;
  --border-default: #e5e7eb;
  --border-input: #d1d5db;
  --bg-accent: #eff6ff;
  --brand-primary: #2563eb;
  --brand-primary-hover: #1d4ed8;
}

html.dark,
[data-theme="dark"] {
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
  --bg-accent: #1e2a4a;
  --brand-primary: #3b82f6;
  --brand-primary-hover: #60a5fa;
}

body {
  margin: 0;
  background: var(--bg-app);
  color: var(--text-primary);
}
</style>
