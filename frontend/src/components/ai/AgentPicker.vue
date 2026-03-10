<script setup lang="ts">
import { useAgentStore } from '../../stores/agent'

const agentStore = useAgentStore()

const agentIcons: Record<string, string> = {
  general: '💬',
  filing: '📋',
  recon: '🔍',
  journal: '📝',
  compliance: '✅',
  classifier: '🏷️',
}
</script>

<template>
  <div class="agent-picker">
    <button
      v-for="a in agentStore.agents"
      :key="a.id"
      class="agent-tab"
      :class="{ active: agentStore.activeAgent === a.id }"
      :title="a.description"
      @click="agentStore.switchAgent(a.id)"
    >
      <span class="agent-icon">{{ agentIcons[a.id] || '🤖' }}</span>
      <span class="agent-name">{{ a.name }}</span>
    </button>
  </div>
</template>

<style scoped>
.agent-picker {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  overflow-x: auto;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}
.agent-picker::-webkit-scrollbar { height: 3px; }
.agent-picker::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

.agent-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: all 0.15s;
  color: #374151;
}
.agent-tab:hover {
  border-color: #4f46e5;
  background: #eef2ff;
}
.agent-tab.active {
  border-color: #4f46e5;
  background: #4f46e5;
  color: white;
}
.agent-icon { font-size: 14px; }
.agent-name { font-weight: 500; }
</style>
