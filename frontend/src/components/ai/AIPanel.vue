<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAgentStore } from '../../stores/agent'
import { useRouteAgent } from '../../composables/useRouteAgent'
import AgentPicker from './AgentPicker.vue'
import AgentMessage from './AgentMessage.vue'

const agentStore = useAgentStore()
const route = useRoute()
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

function getRouteContext(): Record<string, unknown> {
  const ctx: Record<string, unknown> = {}
  const path = route.path
  if (path && path !== '/') ctx.current_page = path
  if (route.params.id) ctx.entity_id = route.params.id
  // Map route to workflow type
  const workflowMap: Record<string, string> = {
    '/reports': 'reports', '/reconciliation': 'reconciliation',
    '/bank-reconciliation': 'bank-reconciliation', '/classification': 'classification',
    '/journal-entries': 'journal-entries', '/general-ledger': 'general-ledger',
    '/statements': 'statements', '/tax-bridge': 'tax-bridge',
    '/calendar': 'calendar', '/form-router': 'form-router',
  }
  for (const [prefix, wf] of Object.entries(workflowMap)) {
    if (path.startsWith(prefix)) { ctx.workflow_type = wf; break }
  }
  return ctx
}

async function handleSend() {
  const msg = input.value.trim()
  if (!msg || agentStore.loading) return
  input.value = ''
  const ctx = getRouteContext()
  await agentStore.sendMessage(msg, ctx)
  await nextTick()
  scrollToBottom()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function toggleThreadList() {
  agentStore.showThreadList = !agentStore.showThreadList
  if (agentStore.showThreadList) {
    agentStore.loadThreads()
  }
}

function startNewChat() {
  agentStore.clearMessages()
  agentStore.showThreadList = false
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
          <span class="header-icon">&#129302;</span>
          AI Agents
        </h3>
        <div class="header-actions">
          <button class="header-btn" @click="startNewChat" title="New Chat">+</button>
          <button class="header-btn" @click="toggleThreadList" title="Chat History" :class="{ active: agentStore.showThreadList }">
            &#128203;
            <span v-if="agentStore.threads.length" class="thread-badge">{{ agentStore.threads.length }}</span>
          </button>
          <button class="close-btn" @click="agentStore.closePanel" title="Close (Esc)">&#10005;</button>
        </div>
      </div>

      <AgentPicker />

      <div class="panel-agent-info" v-if="agentStore.activeAgentInfo">
        <span class="agent-desc">{{ agentStore.activeAgentInfo.description }}</span>
      </div>

      <!-- Thread History List -->
      <Transition name="thread-slide">
        <div v-if="agentStore.showThreadList" class="thread-list">
          <div v-if="!agentStore.threads.length" class="thread-empty">No previous conversations</div>
          <button
            v-for="t in agentStore.threads"
            :key="t.id"
            class="thread-item"
            :class="{ active: agentStore.activeThreadId === t.id }"
            @click="agentStore.loadThreadMessages(t.id)"
          >
            <span class="thread-title">{{ t.title || t.workflow_type || 'Conversation' }}</span>
            <span class="thread-date">{{ new Date(t.created_at).toLocaleDateString() }}</span>
          </button>
        </div>
      </Transition>

      <div class="messages" ref="messagesEl">
        <div v-if="!agentStore.messages.length" class="empty-state">
          <p>Ask {{ agentStore.activeAgentInfo?.name || 'the AI' }} anything...</p>
          <p class="empty-context" v-if="getRouteContext().current_page">
            Context: <code>{{ getRouteContext().current_page }}</code>
          </p>
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
          {{ agentStore.loading ? '...' : '&#9654;' }}
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
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-btn {
  background: none;
  border: 1px solid transparent;
  font-size: 14px;
  cursor: pointer;
  color: #6b7280;
  padding: 4px 8px;
  border-radius: 4px;
  position: relative;
}
.header-btn:hover { background: #f3f4f6; }
.header-btn.active { background: #eef2ff; border-color: #c7d2fe; color: #4f46e5; }
.thread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #4f46e5;
  color: white;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 8px;
  min-width: 14px;
  text-align: center;
}
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

/* Thread list */
.thread-list {
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
}
.thread-empty {
  padding: 12px 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
.thread-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 16px;
  background: none;
  border: none;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  font-size: 13px;
}
.thread-item:hover { background: #eef2ff; }
.thread-item.active { background: #e0e7ff; }
.thread-title {
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.thread-date {
  color: #9ca3af;
  font-size: 11px;
  margin-left: 8px;
  flex-shrink: 0;
}
.thread-slide-enter-active, .thread-slide-leave-active {
  transition: max-height 0.2s ease, opacity 0.2s ease;
  overflow: hidden;
}
.thread-slide-enter-from, .thread-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.thread-slide-enter-to, .thread-slide-leave-from {
  max-height: 200px;
  opacity: 1;
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
.empty-context {
  font-size: 12px;
  margin-top: 8px;
}
.empty-context code {
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 3px;
  color: #4f46e5;
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
