<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTransactionStore } from '../stores/transaction'
import { useReportStore } from '../stores/report'
import { useAccountingStore } from '../stores/accounting'
import { reconciliationApi } from '../api/transactions'
import { currencyLocale } from '@/utils/currency'
import { useAuthStore } from '../stores/auth'
import VATSummarySheet from '../components/reconciliation/VATSummarySheet.vue'
import ReconciliationSummary from '../components/reconciliation/ReconciliationSummary.vue'
import AnomalyList from '../components/reconciliation/AnomalyList.vue'

const router = useRouter()
const route = useRoute()
const store = useTransactionStore()
const reportStore = useReportStore()
const accounting = useAccountingStore()
const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

const selectedReportId = ref<string>('')
const reconError = ref('')
const reconRunning = ref(false)

// F2: Needs Review filter
const needsReviewOnly = ref(false)

// F3: Bulk update
const selectedTxnIds = ref<Set<string>>(new Set())
const bulkVatType = ref('')
const bulkCategory = ref('')
const bulkUpdating = ref(false)

// Transaction table page
const txnPage = ref(1)
const txnPageSize = 50

const displayedTransactions = computed(() => {
  if (!needsReviewOnly.value) return store.transactions
  return store.transactions.filter(
    (t) => t.classification_source !== 'auto_confirmed' &&
           t.classification_source !== 'user_override' &&
           t.confidence < 0.70
  )
})

const allSelected = computed(() => {
  if (displayedTransactions.value.length === 0) return false
  return displayedTransactions.value.every((t) => selectedTxnIds.value.has(t.id))
})

function toggleSelectAll() {
  if (allSelected.value) {
    selectedTxnIds.value = new Set()
  } else {
    selectedTxnIds.value = new Set(displayedTransactions.value.map((t) => t.id))
  }
}

function toggleSelect(id: string) {
  const next = new Set(selectedTxnIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedTxnIds.value = next
}

async function bulkUpdate() {
  if (!sessionId.value || selectedTxnIds.value.size === 0) return
  const items: Array<{ id: string; vat_type?: string; category?: string }> = []
  for (const id of selectedTxnIds.value) {
    const item: { id: string; vat_type?: string; category?: string } = { id }
    if (bulkVatType.value) item.vat_type = bulkVatType.value
    if (bulkCategory.value) item.category = bulkCategory.value
    items.push(item)
  }
  if (!bulkVatType.value && !bulkCategory.value) return

  bulkUpdating.value = true
  reconError.value = ''
  try {
    await store.bulkUpdateTransactions(sessionId.value, items)
    selectedTxnIds.value = new Set()
    bulkVatType.value = ''
    bulkCategory.value = ''
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? 'Bulk update failed'
  } finally {
    bulkUpdating.value = false
  }
}

async function loadTransactions() {
  if (!sessionId.value) return
  store.setFilters(needsReviewOnly.value ? { needs_review: true } : {})
  await store.fetchTransactions(sessionId.value, txnPage.value, txnPageSize)
  selectedTxnIds.value = new Set()
}

function confidenceClass(c: number) {
  if (c >= 0.8) return 'conf-high'
  if (c >= 0.5) return 'conf-med'
  return 'conf-low'
}

// F4: Excel export
async function exportExcel() {
  if (!sessionId.value) return
  await store.exportExcel(sessionId.value)
}

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
  // Fetch session + transactions first (critical), anomalies + reports are optional.
  store.setFilters(needsReviewOnly.value ? { needs_review: true } : {})
  await Promise.all([
    store.fetchSession(sid),
    store.fetchTransactions(sid, 1, txnPageSize),
  ])
  // Non-critical: don't let failures block page rendering.
  await Promise.allSettled([
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
    try {
      await loadSessionData(sessionId.value)
    } catch (e: any) {
      reconError.value = e?.response?.data?.error ?? 'Failed to load session data'
    }
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

const generateReportType = ref(isSG.value ? 'IRAS_GST_F5' : 'BIR_2550M')
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

// Watch needs_review toggle
watch(needsReviewOnly, () => {
  txnPage.value = 1
  loadTransactions()
})

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
        <h2>{{ isSG ? 'GST Reconciliation' : 'VAT Reconciliation' }}</h2>
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
          <h2>{{ isSG ? 'GST Reconciliation' : 'VAT Reconciliation' }}</h2>
          <p class="desc" v-if="store.currentSession" data-testid="recon-status">
            Period: {{ store.currentSession.period }}
            | Status: {{ store.currentSession.status }}
          </p>
        </div>
        <div class="header-actions">
          <button class="btn ghost" @click="listMode = true; store.reset()">All Sessions</button>
          <button class="btn ghost" @click="goBack">Back to Classification</button>
          <button class="btn ghost" @click="exportCsv">Export CSV</button>
          <button class="btn ghost" @click="exportExcel">Export Excel</button>
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
          <button class="btn secondary" @click="fetchSummary" :disabled="store.loading" data-testid="recon-summary-btn">
            Generate Summary
          </button>
          <button class="btn secondary" @click="runDetectAnomalies" :disabled="store.loading" data-testid="recon-detect-btn">
            Detect Anomalies
          </button>
          <button class="btn primary" @click="runReconciliation" :disabled="reconRunning" data-testid="recon-run-btn">
            {{ reconRunning ? 'Running...' : 'Run Reconciliation' }}
          </button>
        </div>
        <div class="control-row" v-if="store.currentSession?.status === 'completed'">
          <label>{{ isSG ? 'Generate IRAS Report:' : 'Generate BIR Report:' }}</label>
          <select v-model="generateReportType">
            <template v-if="isSG">
              <option value="IRAS_GST_F5">GST F5 (Quarterly)</option>
              <option value="IRAS_FORM_C">Form C (Annual)</option>
            </template>
            <template v-else>
              <option value="BIR_2550M">BIR 2550M (Monthly)</option>
              <option value="BIR_2550Q">BIR 2550Q (Quarterly)</option>
            </template>
          </select>
          <button
            class="btn primary"
            @click="generateReportFromSession"
            :disabled="generatingReport"
            data-testid="recon-generate-btn"
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
      <div v-else-if="store.reconciliationResult?.match_stats" class="match-only">
        <h3>Transaction Matching</h3>
        <div class="match-grid">
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.matched_pairs ?? 0 }}</div>
            <div class="lbl">Matched</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.unmatched_records ?? 0 }}</div>
            <div class="lbl">Unmatched Records</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.unmatched_bank ?? 0 }}</div>
            <div class="lbl">Unmatched Bank</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ ((store.reconciliationResult.match_stats.match_rate ?? 0) * 100).toFixed(1) }}%</div>
            <div class="lbl">Match Rate</div>
          </div>
        </div>
      </div>

      <!-- Transaction Table (F2: Needs Review filter, F3: Bulk Update) -->
      <div class="txn-section" v-if="store.transactions.length > 0 || needsReviewOnly">
        <div class="txn-header">
          <h3>Transactions <span class="txn-count">({{ store.transactionTotal }})</span></h3>
          <div class="txn-controls">
            <label class="review-toggle">
              <input type="checkbox" v-model="needsReviewOnly" />
              Needs Review Only
            </label>
          </div>
        </div>

        <!-- F3: Bulk action bar -->
        <div v-if="selectedTxnIds.size > 0" class="bulk-bar">
          <span class="bulk-count">{{ selectedTxnIds.size }} selected</span>
          <select v-model="bulkVatType" class="bulk-select">
            <option value="">Set VAT Type...</option>
            <option value="vatable">Vatable</option>
            <option value="exempt">Exempt</option>
            <option value="zero_rated">Zero Rated</option>
            <option value="government">Government</option>
          </select>
          <select v-model="bulkCategory" class="bulk-select">
            <option value="">Set Category...</option>
            <option value="goods">Goods</option>
            <option value="services">Services</option>
            <option value="capital">Capital</option>
            <option value="imports">Imports</option>
            <option value="sale">Sale</option>
          </select>
          <button
            class="btn primary btn-sm"
            @click="bulkUpdate"
            :disabled="bulkUpdating || (!bulkVatType && !bulkCategory)"
          >
            {{ bulkUpdating ? 'Updating...' : 'Apply' }}
          </button>
          <button class="btn ghost btn-sm" @click="selectedTxnIds = new Set()">Clear</button>
        </div>

        <div class="txn-table-wrap">
          <table class="txn-table">
            <thead>
              <tr>
                <th class="col-check"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
                <th class="col-date">Date</th>
                <th class="col-desc">Description</th>
                <th class="col-amount">Amount</th>
                <th class="col-vat">VAT Type</th>
                <th class="col-cat">Category</th>
                <th class="col-conf">Confidence</th>
                <th class="col-src">Source</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="t in displayedTransactions"
                :key="t.id"
                :class="{ 'low-conf': t.confidence < 0.5, 'selected-row': selectedTxnIds.has(t.id) }"
              >
                <td><input type="checkbox" :checked="selectedTxnIds.has(t.id)" @change="toggleSelect(t.id)" /></td>
                <td>{{ t.date ? new Date(t.date).toLocaleDateString() : '-' }}</td>
                <td class="desc-cell">{{ t.description || '-' }}</td>
                <td class="amount-cell">{{ t.amount.toLocaleString(currencyLocale(), { minimumFractionDigits: 2 }) }}</td>
                <td><span class="tag">{{ t.vat_type }}</span></td>
                <td><span class="tag">{{ t.category }}</span></td>
                <td>
                  <span class="conf-badge" :class="confidenceClass(t.confidence)">
                    {{ (t.confidence * 100).toFixed(0) }}%
                  </span>
                </td>
                <td>
                  <span class="src-badge" :class="{ 'auto-confirmed': t.classification_source === 'auto_confirmed' }">
                    {{ t.classification_source === 'auto_confirmed' ? 'Auto' : t.classification_source }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="txn-pagination" v-if="store.transactionTotal > txnPageSize">
          <button class="btn ghost btn-sm" :disabled="txnPage <= 1" @click="txnPage--; loadTransactions()">Prev</button>
          <span class="page-info">Page {{ txnPage }} of {{ Math.ceil(store.transactionTotal / txnPageSize) }}</span>
          <button class="btn ghost btn-sm" :disabled="txnPage >= Math.ceil(store.transactionTotal / txnPageSize)" @click="txnPage++; loadTransactions()">Next</button>
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

/* Transaction Section (F2/F3) */
.txn-section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}
.txn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.txn-header h3 { margin: 0; font-size: 16px; }
.txn-count { color: #6b7280; font-weight: 400; font-size: 14px; }
.txn-controls { display: flex; gap: 12px; align-items: center; }
.review-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
}
.review-toggle input { cursor: pointer; }

/* Bulk Action Bar (F3) */
.bulk-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.bulk-count { font-size: 13px; font-weight: 600; color: #4338ca; }
.bulk-select {
  padding: 5px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}
.btn-sm { padding: 5px 14px; font-size: 13px; }

/* Transaction Table */
.txn-table-wrap { overflow-x: auto; }
.txn-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.txn-table th {
  text-align: left;
  padding: 8px 10px;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}
.txn-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
}
.txn-table tr:hover { background: #f9fafb; }
.txn-table tr.low-conf { background: #fef2f2; }
.txn-table tr.selected-row { background: #eef2ff; }
.col-check { width: 36px; }
.col-date { width: 100px; }
.col-amount { width: 110px; }
.col-vat, .col-cat, .col-conf, .col-src { width: 90px; }
.desc-cell { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.amount-cell { text-align: right; font-variant-numeric: tabular-nums; }
.tag {
  display: inline-block;
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 11px;
  text-transform: capitalize;
}
.conf-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.conf-high { background: #d1fae5; color: #065f46; }
.conf-med { background: #fef3c7; color: #92400e; }
.conf-low { background: #fecaca; color: #991b1b; }
.src-badge {
  font-size: 11px;
  color: #6b7280;
  text-transform: capitalize;
}
.src-badge.auto-confirmed { color: #059669; font-weight: 600; }

/* Pagination */
.txn-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
.page-info { font-size: 13px; color: #6b7280; }
</style>
