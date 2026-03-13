<script setup lang="ts">
import { useAgentStore } from '../../stores/agent'

const props = defineProps<{
  agent: string
  message: string
  actionLabel?: string
}>()

const agentStore = useAgentStore()

function handleAction() {
  agentStore.openPanel(props.agent)
}
</script>

<template>
  <div class="ai-hint">
    <span class="hint-icon">🤖</span>
    <span class="hint-message">{{ message }}</span>
    <button class="hint-action" @click="handleAction">
      {{ actionLabel || 'Ask AI' }}
    </button>
  </div>
</template>

<style scoped>
.ai-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}
.hint-icon { font-size: 16px; }
.hint-message {
  flex: 1;
  color: var(--brand-primary-hover);
}
.hint-action {
  padding: 4px 12px;
  background: var(--brand-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}
.hint-action:hover { background: var(--brand-primary-hover); }
</style>
