import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '../api/chat'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const historyLoaded = ref(false)

  async function loadHistory() {
    if (historyLoaded.value) return
    try {
      const res = await chatApi.history(1, 50)
      const data = res.data.data
      if (Array.isArray(data) && data.length > 0) {
        messages.value = data.map((m: { role: string; content: string }) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }))
      }
      historyLoaded.value = true
    } catch {
      // Silently fail — empty history is fine
    }
  }

  async function sendMessage(content: string) {
    messages.value = [...messages.value, { role: 'user', content }]
    loading.value = true
    try {
      const res = await chatApi.send({ content })
      const reply = res.data.data
      messages.value = [...messages.value, { role: 'assistant', content: reply.content }]
    } catch {
      messages.value = [
        ...messages.value,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ]
    } finally {
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    historyLoaded.value = false
  }

  return { messages, loading, historyLoaded, loadHistory, sendMessage, clearMessages }
})
