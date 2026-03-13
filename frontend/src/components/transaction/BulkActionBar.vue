<script setup lang="ts">
defineProps<{
  selectedCount: number
  totalCount: number
}>()

const emit = defineEmits<{
  (e: 'acceptSelected'): void
  (e: 'acceptHighConfidence'): void
  (e: 'acceptAll'): void
  (e: 'clearSelection'): void
}>()
</script>

<template>
  <div v-if="selectedCount > 0 || totalCount > 0" class="bulk-bar">
    <div class="left">
      <span v-if="selectedCount > 0" class="count">{{ selectedCount }} selected</span>
      <button v-if="selectedCount > 0" class="bulk-btn" @click="emit('acceptSelected')">
        Accept Selected
      </button>
      <button v-if="selectedCount > 0" class="bulk-btn ghost" @click="emit('clearSelection')">
        Clear
      </button>
    </div>
    <div class="right">
      <button class="bulk-btn accent" @click="emit('acceptHighConfidence')">
        Accept High Confidence
      </button>
      <button class="bulk-btn primary" @click="emit('acceptAll')">
        Accept All
      </button>
    </div>
  </div>
</template>

<style scoped>
.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
}
.left, .right { display: flex; gap: 8px; align-items: center; }
.count { font-weight: 600; color: var(--brand-primary); font-size: 14px; }
.bulk-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}
.bulk-btn:hover { background: var(--bg-surface-hover); }
.bulk-btn.ghost { border: none; color: var(--text-secondary); }
.bulk-btn.accent {
  background: #7c3aed;
  color: #fff;
  border-color: #7c3aed;
}
.bulk-btn.accent:hover { background: #6d28d9; }
.bulk-btn.primary {
  background: var(--brand-primary);
  color: #fff;
  border-color: var(--brand-primary);
}
.bulk-btn.primary:hover { background: var(--brand-primary-hover); }
</style>
