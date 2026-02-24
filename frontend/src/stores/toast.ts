import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

let nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function add(message: string, type: Toast['type'] = 'info', duration = 5000) {
    const id = nextId++
    toasts.value = [...toasts.value, { id, message, type }]
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
  }

  function remove(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function success(message: string) { add(message, 'success', 3000) }
  function error(message: string) { add(message, 'error', 6000) }
  function warning(message: string) { add(message, 'warning', 5000) }
  function info(message: string) { add(message, 'info', 4000) }

  return { toasts, add, remove, success, error, warning, info }
})
