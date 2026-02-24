<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTransactionStore } from '../stores/transaction'
import { useReportStore } from '../stores/report'
import { useAccountingStore } from '../stores/accounting'
import { reconciliationApi } from '../api/transactions'
import VATSummarySheet from '../components/reconciliation/VATSummarySheet.vue'
import ReconciliationSummary from '../components/reconciliation/ReconciliationSummary.vue'
import AnomalyList from '../components/reconciliation/AnomalyList.vue'

const router = useRouter()
const route = useRoute()
const store = useTransactionStore()
const reportStore = useReportStore()
const accounting = useAccountingStore()

const selectedReportId = ref<string>('')
const reconError = ref('')
const reconRunning = ref(false)

const sessionId = computed(() => (route.query.session as string) || '')

const listMode = ref(false)

// Watch for query changes
watch(sessionId, async (newId) => {
  if (newId) {
    listMode.value = false
    await loadSessionData(newId)
  }
})

async function loadSessionData(sid: string) {
  await Promise.all([
    store.fetchSession(sid),
    store.fetchTransactions(sid, 1, 200),
    store.fetchAnomalies(sid),
    reportStore.fetchReports(),
  ])

  if (store.currentSession?.reconciliation_result) {
    store.reconciliationResult = { ...store.currentSession.reconciliation_result }
  }
  if (store.currentSession?.summary) {
    store.summary = { ...store.currentSession.summary }
  }
  if (store.currentSession?.report_id) {
    selectedReportId.value = store.currentSession.report_id
  }
}

onMounted(async () => {
  if (!sessionId.value) {
    listMode.value = true
    await store.fetchSessions()
  } else {
    await loadSessionData(sessionId.value)
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

const generateReportType = ref('BIR_2550M')
const generatingReport = ref(false)
const exportingPdf = ref(false)

async function generateReportFromSession() {
  if (!sessionId.value) return
  generatingReport.value = true
  reconError.value = ''
  try {
    const res = await reconciliationApi.generateReport(sessionId.value, generateReportType.value)
    const report = res.data.data
    if (report?.id) {
      router.push(`/reports/${report.id}/edit`)
    }
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'Report generation failed'
  } finally {
    generatingReport.value = false
  }
}

async function exportPdf() {
  if (!sessionId.value) return
  exportingPdf.value = true
  try {
    const res = await reconciliationApi.exportPdf(sessionId.value)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `reconciliation_${store.currentSession?.period || 'report'}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'PDF export failed'
  } finally {
    exportingPdf.value = false
  }
}

async function exportCsv() {
  await store.exportCsv(sessionId.value)
}

const generatingJournals = ref(false)
async function generateJournalEntries() {
  if (!sessionId.value) return
  generatingJournals.value = true
  reconError.value = ''
  try {
    await accounting.generateJournalsFromSession(sessionId.value)
    router.push('/journal-entries')
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'Journal entry generation failed'
  } finally {
    generatingJournals.value = false
  }
}

function goBack() {
  router.push({ path: '/classification', query: { session: sessionId.value } })
}

function goToReports() {
  router.push('/reports')
}

function openSession(id: string) {
  router.push({ query: { session: id } })
}

function goToClassification() {
  router.push('/classification')
}

async function fetchSummary() {
  if (!sessionId.value) return
  await store.fetchSummary(sessionId.value)
}

const statusColors: Record<string, string> = {
  draft: '#fef3c7',
  classifying: '#dbeafe',
  reviewing: '#ede9fe',
  completed: '#d1fae5',
}
const statusTextColors: Record<string, string> = {
  draft: '#92400e',
  classifying: '#1e40af',
  reviewing: '#5b21b6',
  completed: '#065f46',
}
</script>

<template>
  <div class="reconciliation-view">
    <!-- Session List Mode -->
    <template v-if="listMode">
      <div class="view-header">
        <h2>VAT Reconciliation</h2>
        <button class="btn primary" @click="goToClassification">Go to Classification</button>
      </div>

      <div v-if="store.loading" class="loading-msg">Loading sessions...</div>

      <div v-else-if="store.sessions.length === 0" class="empty-state">
        <p>No reconciliation sessions yet.</p>
        <p class="hint">Upload and classify transactions first, then run reconciliation.</p>
        <button class="btn primary" @click="goToClassification">Start Classification</button>
      </div>

      <div v-else class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.id"
          class="session-card"
          @click="openSession(s.id)"
        >
          <div class="session-info">
            <div class="session-period">{{ s.period }}</div>
            <span
              class="status-badge"
              :style="{
                background: statusColors[s.status] ?? '#f3f4f6',
                color: statusTextColors[s.status] ?? '#374151',
              }"
            >
              {{ s.status }}
            </span>
          </div>
          <div class="session-meta">
            <span>{{ s.source_files?.length ?? 0 }} files</span>
            <span v-if="s.completed_at">Completed {{ new Date(s.completed_at).toLocaleDateString() }}</span>
            <span v-else>Created {{ new Date(s.created_at).toLocaleDateString() }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Session Detail Mode -->
    <template v-else>
      <div class="view-header">
        <div>
          <h2>VAT Reconciliation</h2>
          <p class="desc" v-if="store.currentSession">
            Period: {{ store.currentSession.period }}
            | Status: {{ store.currentSession.status }}
          </p>
        </div>
        <div class="header-actions">
          <button class="btn ghost" @click="listMode = true; store.reset()">All Sessions</button>
          <button class="btn ghost" @click="goBack">Back to Classification</button>
          <button class="btn ghost" @click="exportCsv">Export CSV</button>
          <button
            class="btn secondary"
            @click="exportPdf"
            :disabled="exportingPdf || !store.summary"
          >
            {{ exportingPdf ? 'Exporting...' : 'Export PDF' }}
          </button>
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
        <div class="control-row" v-if="store.currentSession?.status === 'completed'">
          <label>Generate BIR Report:</label>
          <select v-model="generateReportType">
            <option value="BIR_2550M">BIR 2550M (Monthly)</option>
            <option value="BIR_2550Q">BIR 2550Q (Quarterly)</option>
          </select>
          <button
            class="btn primary"
            @click="generateReportFromSession"
            :disabled="generatingReport"
          >
            {{ generatingReport ? 'Generating...' : 'Generate Report' }}
          </button>
        </div>
        <div class="control-row" v-if="store.currentSession?.status === 'completed'">
          <label>Accounting Pipeline:</label>
          <button
            class="btn bridge"
            @click="generateJournalEntries"
            :disabled="generatingJournals"
          >
            {{ generatingJournals ? 'Generating...' : 'Generate Journal Entries' }}
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
    </template>
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
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

/* Session List */
.loading-msg { color: #6b7280; text-align: center; padding: 40px 0; }
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}
.empty-state p { margin: 0 0 8px; color: #374151; }
.empty-state .hint { color: #9ca3af; font-size: 14px; margin-bottom: 20px; }
.session-list { display: flex; flex-direction: column; gap: 12px; }
.session-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.session-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.session-info { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.session-period { font-size: 18px; font-weight: 600; color: #111827; }
.status-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.session-meta { font-size: 13px; color: #9ca3af; display: flex; gap: 16px; }

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
.btn.bridge { background: #059669; color: #fff; border-color: #059669; }
.btn.bridge:hover { background: #047857; }
.btn.bridge:disabled { opacity: 0.6; cursor: default; }

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
