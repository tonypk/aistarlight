<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Anomaly } from '../../types/transaction'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

const props = defineProps<{
  anomaly: Anomaly
}>()

const emit = defineEmits<{
  (e: 'resolve', id: string, status: string, note?: string): void
}>()

const showResolve = ref(false)
const resolveNote = ref('')

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
  high: { bg: '#fef2f2', text: '#991b1b', border: '#fecaca' },
  medium: { bg: '#fffbeb', text: '#92400e', border: '#fde68a' },
  low: { bg: '#f0fdf4', text: '#166534', border: '#bbf7d0' },
}

const typeLabels = computed<Record<string, string>>(() => ({
  duplicate: 'Duplicate Transaction',
  vat_mismatch: isSG.value ? 'GST Mismatch' : 'VAT Mismatch',
  incomplete_tin: isSG.value ? 'Missing UEN' : 'Missing TIN',
  unusual_amount: 'Unusual Amount',
  missing_invoice: 'Missing Invoice',
  unmatched_deposit: 'Unmatched Deposit',
  unmatched_payment: 'Unmatched Payment',
  period_mismatch: 'Period Mismatch',
}))

function resolve(status: string) {
  emit('resolve', props.anomaly.id, status, resolveNote.value || undefined)
  showResolve.value = false
  resolveNote.value = ''
}
</script>

<template>
  <div
    class="anomaly-card"
    :style="{
      background: severityColors[anomaly.severity]?.bg ?? '#f9fafb',
      borderColor: severityColors[anomaly.severity]?.border ?? '#e5e7eb',
    }"
  >
    <div class="header">
      <span
        class="severity-badge"
        :style="{ color: severityColors[anomaly.severity]?.text }"
      >
        {{ anomaly.severity.toUpperCase() }}
      </span>
      <span class="type">{{ typeLabels[anomaly.anomaly_type] ?? anomaly.anomaly_type }}</span>
      <span v-if="anomaly.status !== 'open'" class="status-badge">{{ anomaly.status }}</span>
    </div>
    <p class="desc">{{ anomaly.description }}</p>
    <div v-if="anomaly.details" class="details">
      <template v-for="(val, key) in anomaly.details" :key="key">
        <span
          v-if="typeof val !== 'object' && key !== 'ai_explanation' && key !== 'ai_resolution' && key !== 'bir_reference'"
          class="detail-item"
        >
          <strong>{{ key }}:</strong> {{ val }}
        </span>
      </template>
    </div>

    <!-- F5: AI Explanation -->
    <div v-if="anomaly.details?.ai_explanation" class="ai-section">
      <div class="ai-label">AI Analysis</div>
      <p class="ai-explanation">{{ anomaly.details.ai_explanation }}</p>
      <p v-if="anomaly.details.ai_resolution" class="ai-resolution">
        <strong>Suggested Action:</strong> {{ anomaly.details.ai_resolution }}
      </p>
      <p v-if="anomaly.details.bir_reference" class="ai-bir-ref">
        <strong>{{ isSG ? 'IRAS Reference:' : 'BIR Reference:' }}</strong> {{ anomaly.details.bir_reference }}
      </p>
    </div>

    <div v-if="anomaly.status === 'open'" class="actions">
      <template v-if="!showResolve">
        <button class="action-btn" @click="resolve('acknowledged')">Acknowledge</button>
        <button class="action-btn" @click="resolve('false_positive')">False Positive</button>
        <button class="action-btn primary" @click="showResolve = true">Resolve</button>
      </template>
      <template v-else>
        <input
          v-model="resolveNote"
          type="text"
          placeholder="Resolution note (optional)"
          class="resolve-input"
        />
        <button class="action-btn primary" @click="resolve('resolved')">Confirm Resolve</button>
        <button class="action-btn" @click="showResolve = false">Cancel</button>
      </template>
    </div>

    <div v-if="anomaly.resolution_note" class="resolution">
      Resolved: {{ anomaly.resolution_note }}
    </div>
  </div>
</template>

<style scoped>
.anomaly-card {
  border: 1px solid;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
}
.header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.severity-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.type { font-weight: 600; font-size: 14px; color: #111827; }
.status-badge {
  padding: 2px 8px;
  background: #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  color: #6b7280;
  text-transform: capitalize;
}
.desc { font-size: 14px; color: #374151; margin: 0 0 8px; }
.details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
}
.detail-item strong { color: #374151; }
.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.action-btn {
  padding: 6px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}
.action-btn:hover { background: #f3f4f6; }
.action-btn.primary {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
}
.action-btn.primary:hover { background: #4338ca; }
.resolve-input {
  flex: 1;
  min-width: 200px;
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
}
.resolution {
  margin-top: 8px;
  font-size: 12px;
  color: #059669;
  font-style: italic;
}

/* F5: AI Explanation */
.ai-section {
  margin-top: 10px;
  padding: 10px 14px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}
.ai-label {
  font-size: 11px;
  font-weight: 700;
  color: #0369a1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.ai-explanation {
  font-size: 13px;
  color: #0c4a6e;
  margin: 0 0 6px;
  line-height: 1.5;
}
.ai-resolution {
  font-size: 12px;
  color: #0e7490;
  margin: 0 0 4px;
}
.ai-resolution strong { color: #0c4a6e; }
.ai-bir-ref {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
  font-style: italic;
}
.ai-bir-ref strong { font-style: normal; color: #374151; }
</style>
