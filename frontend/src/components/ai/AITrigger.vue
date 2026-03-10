<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useAgentStore } from '../../stores/agent'
import { useRouteAgent } from '../../composables/useRouteAgent'

const agentStore = useAgentStore()
const { suggestedAgent } = useRouteAgent()

function handleClick() {
  agentStore.openPanel(suggestedAgent.value)
}

function handleKeyboard(e: KeyboardEvent) {
  // Cmd+K (Mac) or Ctrl+K
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    if (agentStore.panelOpen) {
      agentStore.closePanel()
    } else {
      agentStore.openPanel(suggestedAgent.value)
    }
  }
  // Escape to close
  if (e.key === 'Escape' && agentStore.panelOpen) {
    agentStore.closePanel()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyboard)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})
</script>

<template>
  <button
    v-if="!agentStore.panelOpen"
    class="ai-trigger"
    @click="handleClick"
    title="AI Assistant (⌘K)"
  >
    <span class="trigger-icon">🤖</span>
    <span class="trigger-label">AI</span>
  </button>
</template>

<style scoped>
.ai-trigger {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 250;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 28px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(79,70,229,0.4);
  transition: all 0.2s;
}
.ai-trigger:hover {
  background: #4338ca;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(79,70,229,0.5);
}
.trigger-icon { font-size: 18px; }

@media (max-width: 768px) {
  .ai-trigger {
    bottom: 16px;
    right: 16px;
    padding: 10px 14px;
  }
  .trigger-label { display: none; }
}
</style>
