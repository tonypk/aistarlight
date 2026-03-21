<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../stores/transaction'
import { useReportStore } from '../stores/report'
import { useAccountingStore } from '../stores/accounting'
import { reconciliationApi } from '../api/transactions'
import { currencyLocale } from '@/utils/currency'
import { useAuthStore } from '../stores/auth'
import VATSummarySheet from '../components/reconciliation/VATSummarySheet.vue'
import ReconciliationSummary from '../components/reconciliation/ReconciliationSummary.vue'
import AnomalyList from '../components/reconciliation/AnomalyList.vue'
import InlineAIHint from '../components/ai/InlineAIHint.vue'

const { t } = useI18n()

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
    reconError.value = e?.response?.data?.error ?? t('recon.bulkUpdateFailed')
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
  // Always regenerate summary from fresh DB data (not stale cached session.summary)
  // This ensures user edits to vat_type/category are reflected immediately
  await store.fetchSummary(sid)
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
      reconError.value = e?.response?.data?.error ?? t('recon.loadSessionFailed')
    }
  }
})

async function runDetectAnomalies() {
  if (!sessionId.value) return
  reconError.value = ''
  try {
    await store.detectAnomalies(sessionId.value)
  } catch (e: any) {
    reconError.value = e?.response?.data?.error ?? t('recon.anomalyDetectionFailed')
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
    reconError.value = e?.response?.data?.error ?? t('recon.reconciliationFailed')
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
    reconError.value = e?.response?.data?.error ?? t('recon.reportGenerationFailed')
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
    reconError.value = e?.response?.data?.error ?? t('recon.pdfExportFailed')
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
    reconError.value = e?.response?.data?.error ?? t('recon.journalGenerationFailed')
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
        <h2>{{ isSG ? t('recon.titleGST') : t('recon.titleVAT') }}</h2>
        <InlineAIHint agent="recon" :message="t('recon.aiHint')" :action-label="t('recon.askReconAgent')" />
        <button class="btn primary" @click="goToClassification">{{ t('recon.goToClassification') }}</button>
      </div>

      <div v-if="store.loading" class="loading-msg">{{ t('recon.loadingSessions') }}</div>

      <div v-else-if="store.sessions.length === 0" class="empty-state">
        <p>{{ t('recon.noSessions') }}</p>
        <p class="hint">{{ t('recon.noSessionsHint') }}</p>
        <button class="btn primary" @click="goToClassification">{{ t('recon.startClassification') }}</button>
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
            <span>{{ t('recon.files', { count: s.source_files?.length ?? 0 }) }}</span>
            <span v-if="s.completed_at">{{ t('recon.completed', { date: new Date(s.completed_at).toLocaleDateString() }) }}</span>
            <span v-else>{{ t('recon.created', { date: new Date(s.created_at).toLocaleDateString() }) }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Session Detail Mode -->
    <template v-else>
      <div class="view-header">
        <div>
          <h2>{{ isSG ? t('recon.titleGST') : t('recon.titleVAT') }}</h2>
          <p class="desc" v-if="store.currentSession" data-testid="recon-status">
            {{ t('recon.period', { period: store.currentSession.period }) }}
            | {{ t('recon.status', { status: store.currentSession.status }) }}
          </p>
        </div>
        <div class="header-actions">
          <button class="btn ghost" @click="listMode = true; store.reset()">{{ t('recon.allSessions') }}</button>
          <button class="btn ghost" @click="goBack">{{ t('recon.backToClassification') }}</button>
          <button class="btn ghost" @click="exportCsv">{{ t('recon.exportCsv') }}</button>
          <button class="btn ghost" @click="exportExcel">{{ t('recon.exportExcel') }}</button>
          <button
            class="btn secondary"
            @click="exportPdf"
            :disabled="exportingPdf || !store.summary"
          >
            {{ exportingPdf ? t('recon.exporting') : t('recon.exportPdf') }}
          </button>
          <button class="btn" @click="goToReports">{{ t('recon.viewReports') }}</button>
        </div>
      </div>

      <p v-if="reconError" class="error">{{ reconError }}</p>

      <!-- Control Panel -->
      <div class="control-panel">
        <div class="control-row">
          <label>{{ t('recon.compareWithReport') }}</label>
          <select v-model="selectedReportId">
            <option value="">{{ t('recon.noComparison') }}</option>
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
            {{ t('recon.generateSummary') }}
          </button>
          <button class="btn secondary" @click="runDetectAnomalies" :disabled="store.loading" data-testid="recon-detect-btn">
            {{ t('recon.detectAnomalies') }}
          </button>
          <button class="btn primary" @click="runReconciliation" :disabled="reconRunning" data-testid="recon-run-btn">
            {{ reconRunning ? t('recon.running') : t('recon.runReconciliation') }}
          </button>
        </div>
        <div class="control-row" v-if="store.currentSession?.status === 'completed'">
          <label>{{ isSG ? t('recon.generateIRASReport') : t('recon.generateBIRReport') }}</label>
          <select v-model="generateReportType">
            <template v-if="isSG">
              <option value="IRAS_GST_F5">{{ t('recon.gstF5Quarterly') }}</option>
              <option value="IRAS_FORM_C">{{ t('recon.formCAnnual') }}</option>
            </template>
            <template v-else>
              <option value="BIR_2550M">{{ t('recon.bir2550mMonthly') }}</option>
              <option value="BIR_2550Q">{{ t('recon.bir2550qQuarterly') }}</option>
            </template>
          </select>
          <button
            class="btn primary"
            @click="generateReportFromSession"
            :disabled="generatingReport"
            data-testid="recon-generate-btn"
          >
            {{ generatingReport ? t('recon.generating') : t('recon.generateReport') }}
          </button>
        </div>
        <div class="control-row" v-if="store.currentSession?.status === 'completed'">
          <label>{{ t('recon.accountingPipeline') }}</label>
          <button
            class="btn bridge"
            @click="generateJournalEntries"
            :disabled="generatingJournals"
          >
            {{ generatingJournals ? t('recon.generating') : t('recon.generateJournalEntries') }}
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
        <h3>{{ t('recon.transactionMatching') }}</h3>
        <div class="match-grid">
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.matched_pairs ?? 0 }}</div>
            <div class="lbl">{{ t('recon.matched') }}</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.unmatched_records ?? 0 }}</div>
            <div class="lbl">{{ t('recon.unmatchedRecords') }}</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ store.reconciliationResult.match_stats.unmatched_bank ?? 0 }}</div>
            <div class="lbl">{{ t('recon.unmatchedBank') }}</div>
          </div>
          <div class="match-stat">
            <div class="val">{{ ((store.reconciliationResult.match_stats.match_rate ?? 0) * 100).toFixed(1) }}%</div>
            <div class="lbl">{{ t('recon.matchRate') }}</div>
          </div>
        </div>
      </div>

      <!-- Transaction Table (F2: Needs Review filter, F3: Bulk Update) -->
      <div class="txn-section" v-if="store.transactions.length > 0 || needsReviewOnly">
        <div class="txn-header">
          <h3>{{ t('recon.transactions') }} <span class="txn-count">({{ store.transactionTotal }})</span></h3>
          <div class="txn-controls">
            <label class="review-toggle">
              <input type="checkbox" v-model="needsReviewOnly" />
              {{ t('recon.needsReviewOnly') }}
            </label>
          </div>
        </div>

        <!-- F3: Bulk action bar -->
        <div v-if="selectedTxnIds.size > 0" class="bulk-bar">
          <span class="bulk-count">{{ t('recon.selected', { count: selectedTxnIds.size }) }}</span>
          <select v-model="bulkVatType" class="bulk-select">
            <option value="">{{ t('recon.setVatType') }}</option>
            <option value="vatable">{{ t('recon.vatable') }}</option>
            <option value="exempt">{{ t('recon.exempt') }}</option>
            <option value="zero_rated">{{ t('recon.zeroRated') }}</option>
            <option value="government">{{ t('recon.government') }}</option>
          </select>
          <select v-model="bulkCategory" class="bulk-select">
            <option value="">{{ t('recon.setCategory') }}</option>
            <option value="goods">{{ t('recon.goods') }}</option>
            <option value="services">{{ t('recon.services') }}</option>
            <option value="capital">{{ t('recon.capital') }}</option>
            <option value="imports">{{ t('recon.imports') }}</option>
            <option value="sale">{{ t('recon.sale') }}</option>
          </select>
          <button
            class="btn primary btn-sm"
            @click="bulkUpdate"
            :disabled="bulkUpdating || (!bulkVatType && !bulkCategory)"
          >
            {{ bulkUpdating ? t('recon.updating') : t('recon.apply') }}
          </button>
          <button class="btn ghost btn-sm" @click="selectedTxnIds = new Set()">{{ t('common.clear') }}</button>
        </div>

        <div class="txn-table-wrap">
          <table class="txn-table">
            <thead>
              <tr>
                <th class="col-check"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
                <th class="col-date">{{ t('recon.thDate') }}</th>
                <th class="col-desc">{{ t('recon.thDescription') }}</th>
                <th class="col-amount">{{ t('recon.thAmount') }}</th>
                <th class="col-vat">{{ t('recon.thVatType') }}</th>
                <th class="col-cat">{{ t('recon.thCategory') }}</th>
                <th class="col-conf">{{ t('recon.thConfidence') }}</th>
                <th class="col-src">{{ t('recon.thSource') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="txn in displayedTransactions"
                :key="txn.id"
                :class="{ 'low-conf': txn.confidence < 0.5, 'selected-row': selectedTxnIds.has(txn.id) }"
              >
                <td><input type="checkbox" :checked="selectedTxnIds.has(txn.id)" @change="toggleSelect(txn.id)" /></td>
                <td>{{ txn.date ? new Date(txn.date).toLocaleDateString() : '-' }}</td>
                <td class="desc-cell">{{ txn.description || '-' }}</td>
                <td class="amount-cell">{{ txn.amount.toLocaleString(currencyLocale(), { minimumFractionDigits: 2 }) }}</td>
                <td><span class="tag">{{ txn.vat_type }}</span></td>
                <td><span class="tag">{{ txn.category }}</span></td>
                <td>
                  <span class="conf-badge" :class="confidenceClass(txn.confidence)">
                    {{ (txn.confidence * 100).toFixed(0) }}%
                  </span>
                </td>
                <td>
                  <span class="src-badge" :class="{ 'auto-confirmed': txn.classification_source === 'auto_confirmed' }">
                    {{ txn.classification_source === 'auto_confirmed' ? t('recon.auto') : txn.classification_source }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="txn-pagination" v-if="store.transactionTotal > txnPageSize">
          <button class="btn ghost btn-sm" :disabled="txnPage <= 1" @click="txnPage--; loadTransactions()">{{ t('common.prev') }}</button>
          <span class="page-info">{{ t('common.page', { page: txnPage, total: Math.ceil(store.transactionTotal / txnPageSize) }) }}</span>
          <button class="btn ghost btn-sm" :disabled="txnPage >= Math.ceil(store.transactionTotal / txnPageSize)" @click="txnPage++; loadTransactions()">{{ t('common.next') }}</button>
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
.desc { color: var(--text-secondary); font-size: 14px; margin: 0; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

/* Session List */
.loading-msg { color: var(--text-secondary); text-align: center; padding: 40px 0; }
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
}
.empty-state p { margin: 0 0 8px; color: var(--text-primary); }
.empty-state .hint { color: var(--text-muted); font-size: 14px; margin-bottom: 20px; }
.session-list { display: flex; flex-direction: column; gap: 12px; }
.session-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.session-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.session-info { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.session-period { font-size: 18px; font-weight: 600; color: var(--text-primary); }
.status-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.session-meta { font-size: 13px; color: var(--text-muted); display: flex; gap: 16px; }

.control-panel {
  background: var(--bg-surface-alt);
  border: 1px solid var(--border-default);
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
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
}
.control-actions { display: flex; gap: 8px; }

.btn {
  padding: 8px 20px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 14px;
}
.btn:hover { background: var(--bg-surface-hover); }
.btn.ghost { border: none; color: var(--text-secondary); }
.btn.ghost:hover { background: var(--bg-surface-hover); }
.btn.secondary { background: #6b7280; color: #fff; border-color: var(--text-secondary); }
.btn.secondary:hover { background: #4b5563; }
.btn.secondary:disabled { opacity: 0.6; cursor: default; }
.btn.primary { background: var(--brand-primary); color: #fff; border-color: var(--brand-primary); }
.btn.primary:hover { background: var(--brand-primary-hover); }
.btn.primary:disabled { opacity: 0.6; cursor: default; }
.btn.bridge { background: #059669; color: #fff; border-color: #059669; }
.btn.bridge:hover { background: #047857; }
.btn.bridge:disabled { opacity: 0.6; cursor: default; }

.match-only {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
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
  background: var(--bg-surface-alt);
  border-radius: 8px;
}
.match-stat .val { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.match-stat .lbl { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* Transaction Section (F2/F3) */
.txn-section {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
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
.txn-count { color: var(--text-secondary); font-weight: 400; font-size: 14px; }
.txn-controls { display: flex; gap: 12px; align-items: center; }
.review-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary);
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
.bulk-count { font-size: 13px; font-weight: 600; color: var(--brand-primary-hover); }
.bulk-select {
  padding: 5px 10px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-surface);
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
  background: var(--bg-surface-alt);
  border-bottom: 2px solid var(--border-default);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}
.txn-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f3f4f6;
  color: var(--text-primary);
}
.txn-table tr:hover { background: var(--bg-surface-alt); }
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
  background: var(--bg-surface-hover);
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
  color: var(--text-secondary);
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
.page-info { font-size: 13px; color: var(--text-secondary); }

@media (max-width: 768px) {
  .reconciliation-view { max-width: 100%; }
  .view-header { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; }
  .control-panel { padding: 12px; }
  .control-row { flex-direction: column; align-items: stretch; }
  .control-row select { max-width: 100%; }
  .control-actions { flex-wrap: wrap; }
  .match-grid { grid-template-columns: repeat(2, 1fr); }
  .txn-section { padding: 12px; }
  .txn-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .desc-cell { max-width: 140px; }
}
</style>
