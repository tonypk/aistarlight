<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { correctionsApi } from '@/api/corrections'
import type { Correction } from '@/types/correction'

const props = defineProps<{
  entityType: string
  entityId: string
}>()

const corrections = ref<Correction[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await correctionsApi.entityHistory(props.entityType, props.entityId)
    corrections.value = res.data.data || []
  } catch {
    // silently fail — empty list shown
  } finally {
    loading.value = false
  }
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="correction-history" v-if="corrections.length > 0 || loading">
    <h4>Correction History</h4>
    <div v-if="loading" class="loading">Loading...</div>
    <table v-else-if="corrections.length > 0">
      <thead>
        <tr>
          <th>Field</th>
          <th>Old Value</th>
          <th>New Value</th>
          <th>Reason</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in corrections" :key="c.id">
          <td class="field-name">{{ c.field_name }}</td>
          <td class="old-val">{{ c.old_value || '—' }}</td>
          <td class="new-val">{{ c.new_value }}</td>
          <td class="reason">{{ c.reason || '—' }}</td>
          <td class="date">{{ formatDate(c.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.correction-history {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
}
.correction-history h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-primary);
}
.loading {
  color: var(--text-muted);
  font-size: 13px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  padding: 6px 8px;
  color: var(--text-secondary);
  font-size: 12px;
  border-bottom: 1px solid var(--border-default);
}
td {
  padding: 6px 8px;
  border-bottom: 1px solid #f3f4f6;
}
.field-name {
  font-family: monospace;
  color: var(--brand-primary);
}
.old-val {
  color: #ef4444;
  text-decoration: line-through;
}
.new-val {
  color: #22c55e;
  font-weight: 500;
}
.reason {
  color: var(--text-secondary);
  font-style: italic;
}
.date {
  color: var(--text-muted);
  white-space: nowrap;
  font-size: 12px;
}
</style>
