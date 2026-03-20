<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAgentStore } from '../../stores/agent'
import { useRouteAgent } from '../../composables/useRouteAgent'
import AgentPicker from './AgentPicker.vue'
import AgentMessage from './AgentMessage.vue'
import ActionPlanCard from './ActionPlanCard.vue'

const agentStore = useAgentStore()
const route = useRoute()
const { suggestedAgent } = useRouteAgent()
const input = ref('')
const messagesEl = ref<HTMLElement | null>(null)

const agentIcons: Record<string, string> = {
  general: '\u{1F4AC}',
  filing: '\u{1F4CB}',
  recon: '\u{1F50D}',
  journal: '\u{1F4DD}',
  compliance: '\u2705',
  classifier: '\u{1F3F7}\uFE0F',
}

function handleSampleQuestion(q: string) {
  input.value = q
  handleSend()
}

function handleRetry(msgIndex: number) {
  // Find the user message before this assistant message
  for (let i = msgIndex - 1; i >= 0; i--) {
    if (agentStore.messages[i].role === 'user') {
      const content = agentStore.messages[i].content
      // Remove the failed assistant message
      agentStore.messages = agentStore.messages.filter((_, idx) => idx !== msgIndex)
      const ctx = getRouteContext()
      agentStore.sendMessage(content, ctx)
      break
    }
  }
}

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
          <div class="empty-icon" :style="{ color: agentStore.activeAgentInfo?.color || 'var(--brand-primary)' }">
            {{ agentIcons[agentStore.activeAgent] || '&#129302;' }}
          </div>
          <h4 class="empty-title">{{ agentStore.activeAgentInfo?.name || 'AI Assistant' }}</h4>
          <p class="empty-hint">{{ agentStore.activeAgentInfo?.hint || 'Ask me anything...' }}</p>
          <div class="sample-questions" v-if="agentStore.activeAgentInfo?.sample_questions?.length">
            <button
              v-for="(q, qi) in agentStore.activeAgentInfo.sample_questions"
              :key="qi"
              class="sample-chip"
              :style="{ '--agent-color': agentStore.activeAgentInfo?.color || 'var(--brand-primary)' }"
              @click="handleSampleQuestion(q)"
            >
              {{ q }}
            </button>
          </div>
          <p class="empty-context" v-if="getRouteContext().current_page">
            Context: <code>{{ getRouteContext().current_page }}</code>
          </p>
        </div>
        <template v-for="(msg, i) in agentStore.messages" :key="i">
          <ActionPlanCard
            v-if="msg.isActionPlan && msg.actionPlan"
            :plan-id="msg.actionPlan.plan_id"
            :tool-name="msg.actionPlan.tool_name"
            :summary="msg.actionPlan.summary"
            :impact="msg.actionPlan.impact"
            :status="(msg.actionPlan.status || 'pending') as any"
            :result="msg.actionPlan.result"
            :error="msg.actionPlan.error"
          />
          <AgentMessage
            v-else
            :message="msg"
            @retry="handleRetry(i)"
          />
        </template>
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
      <div class="shortcut-hint">Press <kbd>Esc</kbd> to close &middot; <kbd>&#8984;K</kbd> to toggle</div>
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
  background: var(--bg-surface);
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
  border-bottom: 1px solid var(--border-default);
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
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
  position: relative;
}
.header-btn:hover { background: var(--bg-surface-hover); }
.header-btn.active { background: #eef2ff; border-color: #c7d2fe; color: var(--brand-primary); }
.thread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--brand-primary);
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
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
}
.close-btn:hover { background: var(--bg-surface-hover); }

.panel-agent-info {
  padding: 6px 16px;
  border-bottom: 1px solid #f3f4f6;
}
.agent-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

/* Thread list */
.thread-list {
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid var(--border-default);
  background: #fafafa;
}
.thread-empty {
  padding: 12px 16px;
  text-align: center;
  color: var(--text-muted);
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
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.thread-date {
  color: var(--text-muted);
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
.messages::-webkit-scrollbar-thumb { background: var(--border-input); border-radius: 2px; }

.empty-state {
  text-align: center;
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-icon {
  font-size: 36px;
  line-height: 1;
}
.empty-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.empty-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}
.sample-questions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  width: 100%;
}
.sample-chip {
  display: block;
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-surface-alt);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
  text-align: left;
  font-family: inherit;
  transition: all 0.15s;
  line-height: 1.4;
}
.sample-chip:hover {
  background: color-mix(in srgb, var(--agent-color, var(--brand-primary)) 8%, white);
  border-color: var(--agent-color, var(--brand-primary));
  color: var(--agent-color, var(--brand-primary));
}
.empty-context {
  font-size: 12px;
  margin-top: 4px;
  color: var(--text-muted);
}
.empty-context code {
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 3px;
  color: var(--brand-primary);
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-default);
  background: #fafafa;
}
.input-area textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.input-area textarea:focus {
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 2px rgba(79,70,229,0.1);
}
.send-btn {
  padding: 8px 14px;
  background: var(--brand-primary);
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
  background: var(--brand-primary-hover);
}

.shortcut-hint {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 16px 8px;
}
.shortcut-hint kbd {
  background: var(--bg-surface-hover);
  border: 1px solid var(--border-input);
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 10px;
  font-family: inherit;
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
