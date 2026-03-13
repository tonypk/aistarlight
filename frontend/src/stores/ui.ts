import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', () => {
  const sidebarOpen = ref(false)

  // Dark mode: check localStorage, then system preference
  const stored = localStorage.getItem('darkMode')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const isDarkMode = ref(stored !== null ? stored === 'true' : prefersDark)

  // Apply dark class on init
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  }

  watch(isDarkMode, (dark) => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', String(dark))
  })

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function closeSidebar() {
    sidebarOpen.value = false
  }

  function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value
  }

  return {
    sidebarOpen,
    isDarkMode,
    toggleSidebar,
    closeSidebar,
    toggleDarkMode,
  }
})
