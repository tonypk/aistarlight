<script setup lang="ts">
import { useAgentStore } from '../../stores/agent'

const agentStore = useAgentStore()

const agentIcons: Record<string, string> = {
  general: '\u{1F4AC}',
  filing: '\u{1F4CB}',
  recon: '\u{1F50D}',
  journal: '\u{1F4DD}',
  compliance: '\u2705',
  classifier: '\u{1F3F7}\uFE0F',
}
</script>

<template>
  <div class="agent-picker">
    <button
      v-for="a in agentStore.agents"
      :key="a.id"
      class="agent-tab"
      :class="{ active: agentStore.activeAgent === a.id }"
      :style="{
        '--agent-color': a.color || 'var(--brand-primary)',
        borderColor: agentStore.activeAgent === a.id ? (a.color || 'var(--brand-primary)') : undefined,
        background: agentStore.activeAgent === a.id ? (a.color || 'var(--brand-primary)') : undefined,
      }"
      :title="a.description"
      @click="agentStore.switchAgent(a.id)"
    >
      <span class="agent-icon">{{ agentIcons[a.id] || '\u{1F916}' }}</span>
      <span class="agent-name">{{ a.name }}</span>
      <span v-if="a.recommended && agentStore.activeAgent !== a.id" class="recommended-dot" :style="{ background: a.color || 'var(--brand-primary)' }"></span>
    </button>
  </div>
</template>

<style scoped>
.agent-picker {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  overflow-x: auto;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-surface-alt);
}
.agent-picker::-webkit-scrollbar { height: 3px; }
.agent-picker::-webkit-scrollbar-thumb { background: var(--border-input); border-radius: 2px; }

.agent-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: all 0.15s;
  color: var(--text-primary);
  position: relative;
}
.agent-tab:hover {
  border-color: var(--agent-color, var(--brand-primary));
  background: color-mix(in srgb, var(--agent-color, var(--brand-primary)) 8%, white);
}
.agent-tab.active {
  color: white;
}
.agent-icon { font-size: 14px; }
.agent-name { font-weight: 500; }
.recommended-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  border: 1px solid white;
}
</style>
