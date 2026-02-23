<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Anomaly } from '../../types/transaction'
import AnomalyCard from './AnomalyCard.vue'

const props = defineProps<{
  anomalies: Anomaly[]
}>()

const emit = defineEmits<{
  (e: 'resolve', id: string, status: string, note?: string): void
}>()

const activeTab = ref<string>('all')

const tabs = [
  { key: 'all', label: 'All' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
  { key: 'open', label: 'Open' },
  { key: 'resolved', label: 'Resolved' },
]

const filtered = computed(() => {
  const tab = activeTab.value
  if (tab === 'all') return props.anomalies
  if (tab === 'open') return props.anomalies.filter((a) => a.status === 'open')
  if (tab === 'resolved') return props.anomalies.filter((a) => a.status !== 'open')
  return props.anomalies.filter((a) => a.severity === tab)
})

const openCount = computed(() => props.anomalies.filter((a) => a.status === 'open').length)
</script>

<template>
  <div class="anomaly-list">
    <div class="list-header">
      <h3>Anomalies <span v-if="openCount" class="open-count">({{ openCount }} open)</span></h3>
    </div>
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>
    <div v-if="filtered.length === 0" class="empty">No anomalies in this category.</div>
    <AnomalyCard
      v-for="anomaly in filtered"
      :key="anomaly.id"
      :anomaly="anomaly"
      @resolve="(id, status, note) => emit('resolve', id, status, note)"
    />
  </div>
</template>

<style scoped>
.anomaly-list { margin-top: 24px; }
.list-header { margin-bottom: 12px; }
.list-header h3 { margin: 0; font-size: 18px; }
.open-count { color: #dc2626; font-size: 14px; font-weight: 400; }
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}
.tab {
  padding: 6px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  border-radius: 6px;
}
.tab:hover { background: #f3f4f6; }
.tab.active {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}
.empty { text-align: center; padding: 24px; color: #9ca3af; font-size: 14px; }
</style>
