<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { AgentMessage } from '../../stores/agent'
import { renderMarkdown } from '../../utils/markdown'

const props = defineProps<{ message: AgentMessage }>()
const emit = defineEmits<{ retry: [content: string] }>()
const router = useRouter()
const copied = ref(false)

const renderedContent = computed(() => {
  if (props.message.role === 'user') return props.message.content
  return renderMarkdown(props.message.content)
})

function copyMessage() {
  navigator.clipboard.writeText(props.message.content).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 1500)
  })
}

function handleRetry() {
  // Find the previous user message in parent
  emit('retry', '')
}

function handleAction(route: string) {
  router.push(route)
}
</script>

<template>
  <div class="agent-msg" :class="message.role">
    <div class="msg-bubble">
      <!-- Tool calls indicator -->
      <div v-if="message.toolCalls?.length" class="tool-calls">
        <details>
          <summary class="tool-summary">
            <span class="tool-icon">&#9881;&#65039;</span>
            Used {{ message.toolCalls.length }} tool{{ message.toolCalls.length > 1 ? 's' : '' }}
          </summary>
          <div v-for="(tc, i) in message.toolCalls" :key="i" class="tool-call-item">
            <span class="tool-name">{{ tc.tool_name }}</span>
            <pre v-if="tc.result" class="tool-result">{{ tc.result?.substring(0, 200) }}{{ (tc.result?.length || 0) > 200 ? '...' : '' }}</pre>
          </div>
        </details>
      </div>

      <!-- Message content -->
      <div v-if="message.role === 'user'" class="msg-content user-text">{{ message.content }}</div>
      <div v-else class="msg-content markdown-body" v-html="renderedContent"></div>

      <!-- Typing indicator -->
      <div v-if="message.streaming && !message.content" class="typing-indicator">
        <span></span><span></span><span></span>
      </div>

      <!-- Tool execution in progress -->
      <div v-if="message.streaming && message.executingTool" class="tool-executing">
        <span class="tool-spinner"></span>
        Executing {{ message.executingTool }}...
      </div>

      <!-- Action buttons -->
      <div v-if="message.actions?.length" class="msg-actions">
        <button
          v-for="(action, i) in message.actions"
          :key="i"
          class="action-btn"
          @click="handleAction(action.route)"
        >
          {{ action.label }} &rarr;
        </button>
      </div>

      <!-- Sources / Citations -->
      <div v-if="message.sources?.length" class="msg-sources">
        <span v-for="(src, i) in message.sources" :key="i" class="source-badge" :title="src.text">
          {{ src.section || src.law || src.category || 'Source' }}
        </span>
      </div>

      <!-- Copy button (assistant only, on hover) -->
      <button
        v-if="message.role === 'assistant' && message.content && !message.streaming"
        class="msg-copy-btn"
        :class="{ copied }"
        @click="copyMessage"
        :title="copied ? 'Copied!' : 'Copy message'"
      >
        {{ copied ? '&#10003;' : '&#128203;' }}
      </button>

      <!-- Retry button for errors -->
      <button
        v-if="message.error"
        class="retry-btn"
        @click="handleRetry"
      >
        &#8635; Retry
      </button>
    </div>
  </div>
</template>

<style scoped>
.agent-msg {
  display: flex;
  margin-bottom: 12px;
}
.agent-msg.user {
  justify-content: flex-end;
}
.agent-msg.assistant {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  position: relative;
}
.user .msg-bubble {
  background: var(--brand-primary);
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .msg-bubble {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}
.user-text { white-space: pre-wrap; }

/* Copy button */
.msg-copy-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--border-input);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  color: var(--text-secondary);
}
.msg-bubble:hover .msg-copy-btn { opacity: 1; }
.msg-copy-btn:hover { background: white; border-color: var(--brand-primary); color: var(--brand-primary); }
.msg-copy-btn.copied { color: #059669; border-color: #059669; opacity: 1; }

/* Retry button */
.retry-btn {
  margin-top: 8px;
  padding: 4px 12px;
  background: white;
  border: 1px solid #dc2626;
  color: #dc2626;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}
.retry-btn:hover { background: #fef2f2; }

/* Action buttons */
.msg-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.action-btn {
  padding: 6px 14px;
  background: var(--brand-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  font-weight: 500;
  transition: background 0.15s;
}
.action-btn:hover { background: var(--brand-primary-hover); }

/* Markdown body styles */
.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: 4px 0; padding-left: 20px; }
.markdown-body :deep(li) { margin: 2px 0; }
.markdown-body :deep(code) {
  background: rgba(0,0,0,0.06);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, monospace;
}
.markdown-body :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 10px 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 12px;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--brand-primary);
  padding-left: 10px;
  margin: 8px 0;
  color: var(--text-secondary);
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
  width: 100%;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid var(--border-input);
  padding: 4px 8px;
  text-align: left;
}
.markdown-body :deep(th) { background: var(--bg-surface-alt); font-weight: 600; }
.markdown-body :deep(a) { color: var(--brand-primary); text-decoration: underline; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3), .markdown-body :deep(h4) {
  margin: 12px 0 4px;
  font-weight: 600;
}
.markdown-body :deep(h1) { font-size: 18px; }
.markdown-body :deep(h2) { font-size: 16px; }
.markdown-body :deep(h3) { font-size: 15px; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid var(--border-input); margin: 8px 0; }

/* Tool calls */
.tool-calls {
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
  padding-bottom: 6px;
}
.tool-summary {
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  user-select: none;
}
.tool-summary:hover { color: var(--brand-primary); }
.tool-icon { font-size: 14px; }
.tool-call-item {
  margin-top: 6px;
  padding: 4px 8px;
  background: rgba(0,0,0,0.03);
  border-radius: 4px;
}
.tool-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-primary);
  font-family: 'SF Mono', Monaco, monospace;
}
.tool-result {
  font-size: 11px;
  color: var(--text-secondary);
  margin: 4px 0 0;
  white-space: pre-wrap;
  max-height: 100px;
  overflow-y: auto;
}

/* Tool executing spinner */
.tool-executing {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 0;
}
.tool-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid var(--border-input);
  border-top-color: var(--brand-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Sources */
.msg-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.source-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(79, 70, 229, 0.1);
  color: var(--brand-primary);
  cursor: help;
}

/* Typing */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typing 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}
</style>
