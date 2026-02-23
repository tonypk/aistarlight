<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTransactionStore } from '../stores/transaction'
import { useReportStore } from '../stores/report'
import VATSummarySheet from '../components/reconciliation/VATSummarySheet.vue'
import ReconciliationSummary from '../components/reconciliation/ReconciliationSummary.vue'
import AnomalyList from '../components/reconciliation/AnomalyList.vue'

const router = useRouter()
const route = useRoute()
const store = useTransactionStore()
const reportStore = useReportStore()

const selectedReportId = ref<string>('')
const reconError = ref('')
const reconRunning = ref(false)

const sessionId = computed(() => (route.query.session as string) || '')

onMounted(async () => {
  if (!sessionId.value) {
    router.push('/classification')
    return
  }
  await Promise.all([
    store.fetchSession(sessionId.value),
    store.fetchTransactions(sessionId.value, 1, 200),
    store.fetchAnomalies(sessionId.value),
    reportStore.fetchReports(),
  ])

  // Load cached results if session is completed
  if (store.currentSession?.reconciliation_result) {
    store.reconciliationResult = { ...store.currentSession.reconciliation_result }
  }
  if (store.currentSession?.summary) {
    store.summary = { ...store.currentSession.summary }
  }
  if (store.currentSession?.report_id) {
    selectedReportId.value = store.currentSession.report_id
  }
})

async function runDetectAnomalies() {
  if (!sessionId.value) return
  reconError.value = ''
  try {
    await store.detectAnomalies(sessionId.value)
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'Anomaly detection failed'
  }
}

async function runReconciliation() {
  if (!sessionId.value) return
  reconError.value = ''
  reconRunning.value = true
  try {
    await store.runReconciliation(
      sessionId.value,
      selectedReportId.value || undefined
    )
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'Reconciliation failed'
  } finally {
    reconRunning.value = false
  }
}

async function onResolveAnomaly(id: string, status: string, note?: string) {
  await store.resolveAnomaly(sessionId.value, id, status, note)
}

async function exportCsv() {
  await store.exportCsv(sessionId.value)
}

function goBack() {
  router.push({ path: '/classification', query: { session: sessionId.value } })
}

function goToReports() {
  router.push('/reports')
}

async function fetchSummary() {
  if (!sessionId.value) return
  await store.fetchSummary(sessionId.value)
}
</script>

<template>
  <div class="reconciliation-view">
    <div class="view-header">
      <div>
        <h2>VAT Reconciliation</h2>
        <p class="desc" v-if="store.currentSession">
          Period: {{ store.currentSession.period }}
          | Status: {{ store.currentSession.status }}
        </p>
      </div>
      <div class="header-actions">
        <button class="btn ghost" @click="goBack">Back to Classification</button>
        <button class="btn ghost" @click="exportCsv">Export CSV</button>
        <button class="btn" @click="goToReports">View Reports</button>
      </div>
    </div>

    <p v-if="reconError" class="error">{{ reconError }}</p>

    <!-- Control Panel -->
    <div class="control-panel">
      <div class="control-row">
        <label>Compare with Report:</label>
        <select v-model="selectedReportId">
          <option value="">-- No comparison --</option>
          <option
            v-for="r in reportStore.reports"
            :key="r.id"
            :value="r.id"
          >
            {{ r.report_type }} — {{ r.period }} ({{ r.status }})
          </option>
        </select>
      </div>
      <div class="control-actions">
        <button class="btn secondary" @click="fetchSummary" :disabled="store.loading">
          Generate Summary
        </button>
        <button class="btn secondary" @click="runDetectAnomalies" :disabled="store.loading">
          Detect Anomalies
        </button>
        <button class="btn primary" @click="runReconciliation" :disabled="reconRunning">
          {{ reconRunning ? 'Running...' : 'Run Reconciliation' }}
        </button>
      </div>
    </div>

    <!-- VAT Summary -->
    <VATSummarySheet v-if="store.summary" :summary="store.summary" />

    <!-- Reconciliation Results -->
    <ReconciliationSummary
      v-if="store.reconciliationResult?.comparison"
      :comparison="store.reconciliationResult.comparison"
      :match-stats="store.reconciliationResult.match_stats"
    />

    <!-- Match Stats (when no comparison) -->
    <div v-else-if="store.reconciliationResult" class="match-only">
      <h3>Transaction Matching</h3>
      <div class="match-grid">
        <div class="match-stat">
          <div class="val">{{ store.reconciliationResult.match_stats.matched_pairs }}</div>
          <div class="lbl">Matched</div>
        </div>
        <div class="match-stat">
          <div class="val">{{ store.reconciliationResult.match_stats.unmatched_records }}</div>
          <div class="lbl">Unmatched Records</div>
        </div>
        <div class="match-stat">
          <div class="val">{{ store.reconciliationResult.match_stats.unmatched_bank }}</div>
          <div class="lbl">Unmatched Bank</div>
        </div>
        <div class="match-stat">
          <div class="val">{{ (store.reconciliationResult.match_stats.match_rate * 100).toFixed(1) }}%</div>
          <div class="lbl">Match Rate</div>
        </div>
      </div>
    </div>

    <!-- Anomalies -->
    <AnomalyList
      :anomalies="store.anomalies"
      @resolve="onResolveAnomaly"
    />
  </div>
</template>

<style scoped>
.reconciliation-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.view-header h2 { margin: 0 0 4px; }
.desc { color: #6b7280; font-size: 14px; margin: 0; }
.header-actions { display: flex; gap: 8px; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

.control-panel {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}
.control-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.control-row label { font-size: 14px; font-weight: 500; white-space: nowrap; }
.control-row select {
  flex: 1;
  max-width: 400px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.control-actions { display: flex; gap: 8px; }

.btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn:hover { background: #f3f4f6; }
.btn.ghost { border: none; color: #6b7280; }
.btn.ghost:hover { background: #f3f4f6; }
.btn.secondary { background: #6b7280; color: #fff; border-color: #6b7280; }
.btn.secondary:hover { background: #4b5563; }
.btn.secondary:disabled { opacity: 0.6; cursor: default; }
.btn.primary { background: #4f46e5; color: #fff; border-color: #4f46e5; }
.btn.primary:hover { background: #4338ca; }
.btn.primary:disabled { opacity: 0.6; cursor: default; }

.match-only {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}
.match-only h3 { margin: 0 0 16px; font-size: 16px; }
.match-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.match-stat {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}
.match-stat .val { font-size: 24px; font-weight: 700; color: #111827; }
.match-stat .lbl { font-size: 12px; color: #6b7280; margin-top: 4px; }
</style>
