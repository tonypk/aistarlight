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
.count { font-weight: 600; color: #4f46e5; font-size: 14px; }
.bulk-btn {
  padding: 6px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
}
.bulk-btn:hover { background: #f3f4f6; }
.bulk-btn.ghost { border: none; color: #6b7280; }
.bulk-btn.accent {
  background: #7c3aed;
  color: #fff;
  border-color: #7c3aed;
}
.bulk-btn.accent:hover { background: #6d28d9; }
.bulk-btn.primary {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
}
.bulk-btn.primary:hover { background: #4338ca; }
</style>
