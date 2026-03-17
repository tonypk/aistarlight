<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { casApi } from '../api/cas'
import type { ComplianceResult, ComplianceCheckSummary, SubsidiaryLedgerEntry } from '../api/cas'

// State
const latestCheck = ref<ComplianceResult | null>(null)
const checkHistory = ref<ComplianceCheckSummary[]>([])
const ledgerEntries = ref<SubsidiaryLedgerEntry[]>([])
const loading = ref(false)
const runningCheck = ref(false)
const error = ref('')
const activeTab = ref<'overview' | 'ledger' | 'history'>('overview')

// Subsidiary ledger filters
const selectedBook = ref('general_journal')
const dateFrom = ref('')
const dateTo = ref('')
const ledgerLoading = ref(false)

const journalBooks = [
  { value: 'general_journal', label: 'General Journal' },
  { value: 'sales_journal', label: 'Sales Journal' },
  { value: 'purchases_journal', label: 'Purchases Journal' },
  { value: 'cash_receipts', label: 'Cash Receipts Journal' },
  { value: 'cash_disbursements', label: 'Cash Disbursements Journal' },
]

// Load data
async function loadLatest() {
  loading.value = true
  error.value = ''
  try {
    const res = await casApi.getLatest()
    latestCheck.value = res.data.data
  } catch {
    // No checks yet — that's fine
    latestCheck.value = null
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  try {
    const res = await casApi.listChecks({ limit: 20, offset: 0 })
    checkHistory.value = res.data.data || []
  } catch {
    checkHistory.value = []
  }
}

async function runComplianceCheck() {
  runningCheck.value = true
  error.value = ''
  try {
    const res = await casApi.runCheck()
    latestCheck.value = res.data.data
    await loadHistory()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to run compliance check'
  } finally {
    runningCheck.value = false
  }
}

async function loadSubsidiaryLedger() {
  ledgerLoading.value = true
  try {
    const params: { book: string; from?: string; to?: string } = {
      book: selectedBook.value,
    }
    if (dateFrom.value) params.from = dateFrom.value
    if (dateTo.value) params.to = dateTo.value
    const res = await casApi.getSubsidiaryLedger(params)
    ledgerEntries.value = res.data.data || []
  } catch {
    ledgerEntries.value = []
  } finally {
    ledgerLoading.value = false
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

function formatAmount(val: string) {
  const n = parseFloat(val)
  return isNaN(n) || n === 0 ? '-' : n.toLocaleString('en-PH', { minimumFractionDigits: 2 })
}

onMounted(async () => {
  await Promise.all([loadLatest(), loadHistory()])
})
</script>

<template>
  <div class="cas-compliance-view">
    <div class="page-header">
      <h1>BIR CAS Compliance</h1>
      <p class="subtitle">Computerized Accounting System certification readiness</p>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in [
          { key: 'overview', label: 'Compliance Overview' },
          { key: 'ledger', label: 'Subsidiary Ledgers' },
          { key: 'history', label: 'Check History' },
        ]"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key as typeof activeTab"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Overview Tab -->
    <div v-if="activeTab === 'overview'" class="tab-content">
      <div class="action-bar">
        <button class="btn btn-primary" :disabled="runningCheck" @click="runComplianceCheck">
          {{ runningCheck ? 'Running check...' : 'Run Compliance Check' }}
        </button>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-if="loading" class="loading">Loading...</div>

      <div v-else-if="latestCheck" class="compliance-overview">
        <!-- Overall Status -->
        <div :class="['overall-status', latestCheck.overall_pass ? 'pass' : 'fail']">
          <span class="status-icon">{{ latestCheck.overall_pass ? '&#10003;' : '&#10007;' }}</span>
          <span class="status-text">
            {{ latestCheck.overall_pass ? 'CAS Compliant' : 'Not Compliant' }}
          </span>
        </div>

        <!-- Check Items Grid -->
        <div class="check-grid">
          <div
            v-for="item in [
              { key: 'sequential_numbering_ok', label: 'Sequential Numbering', desc: 'Gap-free company-wide document numbering' },
              { key: 'hash_chain_intact', label: 'Hash Chain Integrity', desc: 'SHA-256 tamper-proof audit chain' },
              { key: 'double_entry_balanced', label: 'Double-Entry Balance', desc: 'All debits equal credits' },
              { key: 'periods_properly_closed', label: 'Accounting Periods', desc: 'Prior periods properly closed' },
              { key: 'audit_trail_complete', label: 'Audit Trail', desc: 'Complete audit log with hash chain' },
              { key: 'subsidiary_ledgers_ok', label: 'Subsidiary Ledgers', desc: 'BIR journal book classifications' },
            ]"
            :key="item.key"
            :class="['check-card', (latestCheck as Record<string, unknown>)[item.key] ? 'pass' : 'fail']"
          >
            <div class="check-icon">
              {{ (latestCheck as Record<string, unknown>)[item.key] ? '&#10003;' : '&#10007;' }}
            </div>
            <div class="check-info">
              <h3>{{ item.label }}</h3>
              <p>{{ item.desc }}</p>
            </div>
          </div>
        </div>

        <!-- Details -->
        <div v-if="latestCheck.details" class="details-section">
          <h3>Check Details</h3>
          <div class="detail-items">
            <div v-if="latestCheck.details.unposted_drafts !== undefined" class="detail-item">
              <span class="detail-label">Unposted Draft Entries:</span>
              <span class="detail-value">{{ latestCheck.details.unposted_drafts }}</span>
            </div>
            <div v-if="latestCheck.details.journal_books" class="detail-item">
              <span class="detail-label">Journal Book Entries:</span>
              <div class="book-counts">
                <span
                  v-for="(count, book) in (latestCheck.details.journal_books as Record<string, number>)"
                  :key="String(book)"
                  class="book-badge"
                >
                  {{ String(book).replace(/_/g, ' ') }}: {{ count }}
                </span>
              </div>
            </div>
            <div v-if="latestCheck.details.sequence_gaps" class="detail-item warning">
              <span class="detail-label">Sequence Gaps Found:</span>
              <span class="detail-value">
                {{ (latestCheck.details.sequence_gaps as unknown[]).length }} gap(s) detected
              </span>
            </div>
            <div v-if="latestCheck.details.hash_chain_breaks" class="detail-item warning">
              <span class="detail-label">Hash Chain Breaks:</span>
              <span class="detail-value">
                {{ (latestCheck.details.hash_chain_breaks as unknown[]).length }} break(s) detected
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>No compliance checks have been run yet.</p>
        <p>Click "Run Compliance Check" to verify your CAS readiness.</p>
      </div>
    </div>

    <!-- Subsidiary Ledger Tab -->
    <div v-if="activeTab === 'ledger'" class="tab-content">
      <div class="ledger-filters">
        <div class="filter-group">
          <label>Journal Book</label>
          <select v-model="selectedBook">
            <option v-for="book in journalBooks" :key="book.value" :value="book.value">
              {{ book.label }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label>From</label>
          <input type="date" v-model="dateFrom" />
        </div>
        <div class="filter-group">
          <label>To</label>
          <input type="date" v-model="dateTo" />
        </div>
        <button class="btn btn-primary" :disabled="ledgerLoading" @click="loadSubsidiaryLedger">
          {{ ledgerLoading ? 'Loading...' : 'Load Ledger' }}
        </button>
      </div>

      <div v-if="ledgerEntries.length > 0" class="ledger-table-wrapper">
        <table class="ledger-table">
          <thead>
            <tr>
              <th>Seq #</th>
              <th>Date</th>
              <th>Entry #</th>
              <th>Description</th>
              <th>Account</th>
              <th class="text-right">Debit</th>
              <th class="text-right">Credit</th>
              <th>Tax Code</th>
              <th class="text-right">Tax Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in ledgerEntries" :key="entry.line_id">
              <td>{{ entry.company_seq_no || '-' }}</td>
              <td>{{ entry.entry_date }}</td>
              <td>{{ entry.entry_number || '-' }}</td>
              <td>{{ entry.entry_description || entry.line_description || '-' }}</td>
              <td>{{ entry.account_code }} - {{ entry.account_name }}</td>
              <td class="text-right">{{ formatAmount(entry.debit) }}</td>
              <td class="text-right">{{ formatAmount(entry.credit) }}</td>
              <td>{{ entry.tax_code || '-' }}</td>
              <td class="text-right">{{ formatAmount(entry.tax_amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>Select a journal book type and click "Load Ledger" to view entries.</p>
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="tab-content">
      <div v-if="checkHistory.length > 0">
        <table class="history-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Overall</th>
              <th>Seq #</th>
              <th>Hash Chain</th>
              <th>Double Entry</th>
              <th>Periods</th>
              <th>Audit Trail</th>
              <th>Sub Ledgers</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="check in checkHistory" :key="check.id">
              <td>{{ formatDate(check.check_date) }}</td>
              <td><span :class="['status-badge', check.overall_pass ? 'pass' : 'fail']">
                {{ check.overall_pass ? 'PASS' : 'FAIL' }}
              </span></td>
              <td><span :class="['status-dot', check.sequential_numbering_ok ? 'pass' : 'fail']"></span></td>
              <td><span :class="['status-dot', check.hash_chain_intact ? 'pass' : 'fail']"></span></td>
              <td><span :class="['status-dot', check.double_entry_balanced ? 'pass' : 'fail']"></span></td>
              <td><span :class="['status-dot', check.periods_properly_closed ? 'pass' : 'fail']"></span></td>
              <td><span :class="['status-dot', check.audit_trail_complete ? 'pass' : 'fail']"></span></td>
              <td><span :class="['status-dot', check.subsidiary_ledgers_ok ? 'pass' : 'fail']"></span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>No compliance check history available.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cas-compliance-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.subtitle {
  color: #6b7280;
  margin-top: 4px;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #e5e7eb;
  margin: 24px 0 16px;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  font-weight: 600;
}

.tab-btn:hover {
  color: #1d4ed8;
}

.action-bar {
  margin-bottom: 16px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.error-message {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-bottom: 16px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

/* Overall Status */
.overall-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 20px;
  font-weight: 700;
}

.overall-status.pass {
  background: #ecfdf5;
  border: 2px solid #6ee7b7;
  color: #065f46;
}

.overall-status.fail {
  background: #fef2f2;
  border: 2px solid #fca5a5;
  color: #991b1b;
}

.status-icon {
  font-size: 28px;
}

/* Check Grid */
.check-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.check-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.check-card.pass {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.check-card.fail {
  background: #fef2f2;
  border-color: #fecaca;
}

.check-icon {
  font-size: 20px;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.check-card.pass .check-icon {
  color: #16a34a;
  background: #dcfce7;
}

.check-card.fail .check-icon {
  color: #dc2626;
  background: #fee2e2;
}

.check-info h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.check-info p {
  font-size: 12px;
  color: #6b7280;
  margin: 4px 0 0;
}

/* Details */
.details-section {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px 20px;
}

.details-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}

.detail-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.detail-item.warning {
  color: #b45309;
}

.detail-label {
  font-weight: 500;
  min-width: 180px;
}

.book-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.book-badge {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: capitalize;
}

/* Ledger */
.ledger-filters {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.filter-group select,
.filter-group input {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.ledger-table-wrapper {
  overflow-x: auto;
}

.ledger-table,
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.ledger-table th,
.ledger-table td,
.history-table th,
.history-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}

.ledger-table th,
.history-table th {
  background: #f9fafb;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #6b7280;
}

.text-right {
  text-align: right;
}

/* History */
.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.pass {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.fail {
  background: #fee2e2;
  color: #dc2626;
}

.status-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-dot.pass {
  background: #16a34a;
}

.status-dot.fail {
  background: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.empty-state p {
  margin: 4px 0;
}

@media (max-width: 768px) {
  .cas-compliance-view { padding: 12px; max-width: 100%; }
  .check-grid { grid-template-columns: 1fr; }
  .detail-item { flex-direction: column; }
  .detail-label { min-width: 0; }
  .overall-status { padding: 14px 16px; font-size: 16px; }
  .history-table { min-width: 600px; }
  .tab-content { overflow-x: auto; }
}
</style>
