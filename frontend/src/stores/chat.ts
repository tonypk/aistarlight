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
  }

  return { messages, loading, sendMessage, clearMessages }
})
