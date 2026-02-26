<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import ChatMessage from '../components/chat/ChatMessage.vue'
import { useChatStore } from '../stores/chat'
import { healthApi } from '../api/health'

const chat = useChatStore()
const input = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const aiAvailable = ref(true)

onMounted(async () => {
  try {
    const res = await healthApi.getAIHealth()
    aiAvailable.value = res.data.data?.ai_enabled ?? true
  } catch {
    // Assume available if health check fails
  }
  await chat.loadHistory()
  await nextTick()
  scrollToBottom()
})

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function handleSend() {
  const msg = input.value.trim()
  if (!msg) return
  input.value = ''
  await chat.sendMessage(msg)
  await nextTick()
  scrollToBottom()
}
</script>

<template>
  <div class="chat-view">
    <h2>AI Tax Assistant</h2>

    <div v-if="!aiAvailable" class="ai-offline-banner">
      AI features are currently offline. The OPENAI_API_KEY has not been configured on the server.
      Basic functionality is still available.
    </div>

    <div class="chat-container">
      <div class="messages" ref="messagesEl">
        <div v-if="!chat.messages.length" class="welcome">
          <p>Ask me anything about Philippine tax filing!</p>
          <div class="suggestions">
            <button @click="input = 'How do I file BIR 2550M?'">How to file BIR 2550M?</button>
            <button @click="input = 'What is the VAT rate in the Philippines?'">PH VAT rate?</button>
            <button @click="input = 'Help me generate this month\'s VAT report'">Generate VAT report</button>
          </div>
        </div>
        <ChatMessage
          v-for="(msg, i) in chat.messages"
          :key="i"
          :role="msg.role"
          :content="msg.content"
          :sources="msg.sources"
        />
        <div v-if="chat.loading && !chat.messages.some(m => m.streaming)" class="typing">AI is thinking...</div>
      </div>

      <form class="input-area" @submit.prevent="handleSend">
        <input
          v-model="input"
          :placeholder="aiAvailable ? 'Type your message...' : 'AI is offline — messages may not get responses'"
          :disabled="chat.loading || !aiAvailable"
        />
        <button type="submit" :disabled="chat.loading || !input.trim() || !aiAvailable">Send</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.chat-view h2 { margin-bottom: 16px; }
.ai-offline-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}
.chat-container {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.welcome { text-align: center; padding: 48px 0; color: #888; }
.suggestions { display: flex; gap: 8px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.suggestions button {
  padding: 8px 16px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 20px;
  cursor: pointer;
  color: #4f46e5;
  font-size: 13px;
}
.typing { color: #888; font-style: italic; padding: 12px; }
.input-area {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}
.input-area input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}
.input-area button {
  padding: 12px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.input-area button:disabled { opacity: 0.6; }
</style>
