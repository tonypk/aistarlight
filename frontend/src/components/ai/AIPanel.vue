<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useAgentStore } from '../../stores/agent'
import { useRouteAgent } from '../../composables/useRouteAgent'
import AgentPicker from './AgentPicker.vue'
import AgentMessage from './AgentMessage.vue'

const agentStore = useAgentStore()
const { suggestedAgent } = useRouteAgent()
const input = ref('')
const messagesEl = ref<HTMLElement | null>(null)

onMounted(() => {
  agentStore.loadAgents()
})

// Auto-select agent based on route
watch(suggestedAgent, (newAgent) => {
  if (agentStore.panelOpen && agentStore.activeAgent === 'general' && newAgent !== 'general') {
    agentStore.switchAgent(newAgent)
  }
}, { immediate: true })

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function handleSend() {
  const msg = input.value.trim()
  if (!msg || agentStore.loading) return
  input.value = ''
  await agentStore.sendMessage(msg)
  await nextTick()
  scrollToBottom()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

watch(() => agentStore.messages.length, async () => {
  await nextTick()
  scrollToBottom()
})
</script>

<template>
  <Transition name="slide">
    <aside v-if="agentStore.panelOpen" class="ai-panel">
      <div class="panel-header">
        <h3>
          <span class="header-icon">🤖</span>
          AI Agents
        </h3>
        <button class="close-btn" @click="agentStore.closePanel" title="Close (Esc)">✕</button>
      </div>

      <AgentPicker />

      <div class="panel-agent-info" v-if="agentStore.activeAgentInfo">
        <span class="agent-desc">{{ agentStore.activeAgentInfo.description }}</span>
      </div>

      <div class="messages" ref="messagesEl">
        <div v-if="!agentStore.messages.length" class="empty-state">
          <p>Ask {{ agentStore.activeAgentInfo?.name || 'the AI' }} anything...</p>
        </div>
        <AgentMessage
          v-for="(msg, i) in agentStore.messages"
          :key="i"
          :message="msg"
        />
      </div>

      <div class="input-area">
        <textarea
          v-model="input"
          :placeholder="'Ask ' + (agentStore.activeAgentInfo?.name || 'AI') + '...'"
          @keydown="handleKeydown"
          rows="2"
          :disabled="agentStore.loading"
        ></textarea>
        <button
          class="send-btn"
          @click="handleSend"
          :disabled="!input.trim() || agentStore.loading"
        >
          {{ agentStore.loading ? '...' : '▶' }}
        </button>
      </div>
    </aside>
  </Transition>
</template>

<style scoped>
.ai-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -4px 0 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 300;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
}
.panel-header h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.header-icon { font-size: 18px; }
.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #6b7280;
  padding: 4px 8px;
  border-radius: 4px;
}
.close-btn:hover { background: #f3f4f6; }

.panel-agent-info {
  padding: 6px 16px;
  border-bottom: 1px solid #f3f4f6;
}
.agent-desc {
  font-size: 11px;
  color: #6b7280;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.messages::-webkit-scrollbar { width: 4px; }
.messages::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

.empty-state {
  text-align: center;
  color: #9ca3af;
  padding: 40px 20px;
  font-size: 14px;
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
}
.input-area textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.input-area textarea:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79,70,229,0.1);
}
.send-btn {
  padding: 8px 14px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  align-self: flex-end;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.send-btn:hover:not(:disabled) {
  background: #4338ca;
}

/* Slide animation */
.slide-enter-active, .slide-leave-active {
  transition: transform 0.25s ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}

@media (max-width: 768px) {
  .ai-panel {
    width: 100%;
  }
}
</style>
