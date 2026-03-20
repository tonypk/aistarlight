import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)

  // Theme: match HR's pattern with data-theme attribute
  const mode = ref<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  )

  const isDark = computed(() => mode.value === 'dark')

  // Keep backward compat alias
  const isDarkMode = isDark

  function toggleDarkMode() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  watch(mode, (val) => {
    localStorage.setItem('theme', val)
    document.documentElement.setAttribute('data-theme', val)
    // Backward compat: keep html.dark class for existing scoped CSS
    if (val === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, { immediate: true })

  return {
    sidebarCollapsed,
    mode,
    isDark,
    isDarkMode,
    toggleDarkMode,
  }
})
