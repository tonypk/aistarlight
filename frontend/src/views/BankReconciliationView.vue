<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  bankReconApi,
  type BankReconBatch,
  type BankReconBatchListItem,
} from '@/api/bankRecon'

// Wizard steps
const STEPS = ['Upload', 'Parsing', 'Matching', 'AI Analysis', 'Summary']
const currentStep = ref(0)

// Upload state
const files = ref<File[]>([])
const dragOver = ref(false)
const period = ref('')
const sessionId = ref('')
const amountTolerance = ref(0.01)
const dateTolerance = ref(3)
const runAI = ref(true)

// Processing state
const processing = ref(false)
const error = ref('')
const batch = ref<BankReconBatch | null>(null)

// History
const batches = ref<BankReconBatchListItem[]>([])
const showHistory = ref(false)
const historyLoading = ref(false)

// Default period
const now = new Date()
period.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls', 'pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp']

const canProcess = computed(() =>
  files.value.length > 0 && period.value && !processing.value
)

const matchRate = computed(() => {
  const mr = batch.value?.match_result?.match_rate
  return mr != null ? (mr * 100).toFixed(1) : '—'
})

const matchedCount = computed(() =>
  batch.value?.match_result?.matched_pairs?.length ?? 0
)
const unmatchedBankCount = computed(() =>
  batch.value?.match_result?.unmatched_bank?.length ?? 0
)
const unmatchedRecordCount = computed(() =>
  batch.value?.match_result?.unmatched_records?.length ?? 0
)

const pendingSuggestions = computed(() =>
  (batch.value?.ai_suggestions ?? []).filter(s => s.status === 'pending')
)
const acceptedSuggestions = computed(() =>
  (batch.value?.ai_suggestions ?? []).filter(s => s.status === 'accepted')
)

// --- File handling ---
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}
function handleDragLeave() {
  dragOver.value = false
}
function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  if (e.dataTransfer?.files) addFiles(Array.from(e.dataTransfer.files))
}
function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) addFiles(Array.from(input.files))
  input.value = ''
}

function addFiles(newFiles: File[]) {
  const valid = newFiles.filter(f => {
    const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
    return ALLOWED_EXTENSIONS.includes(ext)
  })
  files.value = [...files.value, ...valid]
}

function removeFile(index: number) {
  files.value = files.value.filter((_, i) => i !== index)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function fileTypeIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (ext === 'pdf') return '📄'
  if (['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp'].includes(ext)) return '🖼️'
  if (['xlsx', 'xls'].includes(ext)) return '📊'
  return '📃'
}

// --- Process ---
async function startProcess() {
  if (!canProcess.value) return
  processing.value = true
  error.value = ''
  batch.value = null
  currentStep.value = 1 // Parsing

  const formData = new FormData()
  for (const f of files.value) formData.append('files', f)
  formData.append('period', period.value)
  if (sessionId.value) formData.append('session_id', sessionId.value)
  formData.append('amount_tolerance', String(amountTolerance.value))
  formData.append('date_tolerance_days', String(dateTolerance.value))
  formData.append('run_ai_analysis', String(runAI.value))

  try {
    const resp = await bankReconApi.process(formData)
    if (resp.success) {
      batch.value = resp.data
      // Jump to appropriate final step
      if (batch.value?.ai_suggestions?.length || batch.value?.ai_explanations?.length) {
        currentStep.value = 3 // AI Analysis
      } else {
        currentStep.value = 2 // Matching
      }
    } else {
      error.value = resp.error || 'Processing failed'
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Processing failed'
  } finally {
    processing.value = false
  }
}

// --- Suggestion actions ---
async function acceptSuggestion(index: number) {
  if (!batch.value) return
  try {
    const resp = await bankReconApi.acceptSuggestion(batch.value.id, index)
    if (resp.success && batch.value.ai_suggestions) {
      batch.value = {
        ...batch.value,
        ai_suggestions: batch.value.ai_suggestions.map((s, i) =>
          i === index ? { ...s, status: 'accepted' } : s
        ),
      }
    }
  } catch (e: any) {
    error.value = e.message
  }
}

async function rejectSuggestion(index: number) {
  if (!batch.value) return
  try {
    const resp = await bankReconApi.rejectSuggestion(batch.value.id, index)
    if (resp.success && batch.value.ai_suggestions) {
      batch.value = {
        ...batch.value,
        ai_suggestions: batch.value.ai_suggestions.map((s, i) =>
          i === index ? { ...s, status: 'rejected' } : s
        ),
      }
    }
  } catch (e: any) {
    error.value = e.message
  }
}

async function rerunAnalysis() {
  if (!batch.value) return
  processing.value = true
  try {
    const resp = await bankReconApi.rerunAnalysis(batch.value.id)
    if (resp.success) batch.value = resp.data
  } catch (e: any) {
    error.value = e.message
  } finally {
    processing.value = false
  }
}

// --- History ---
async function loadHistory() {
  historyLoading.value = true
  try {
    const resp = await bankReconApi.listBatches()
    if (resp.success) batches.value = resp.data
  } catch { /* ignore */ } finally {
    historyLoading.value = false
  }
}

async function loadBatch(id: string) {
  processing.value = true
  try {
    const resp = await bankReconApi.getBatch(id)
    if (resp.success) {
      batch.value = resp.data
      showHistory.value = false
      currentStep.value = batch.value?.ai_suggestions?.length ? 3 : 2
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    processing.value = false
  }
}

function goToSummary() {
  currentStep.value = 4
}

function reset() {
  files.value = []
  batch.value = null
  error.value = ''
  currentStep.value = 0
}

function categoryColor(cat: string): string {
  const map: Record<string, string> = {
    likely_match: '#22c55e',
    possible_match: '#eab308',
    no_match: '#ef4444',
    internal_transfer: '#3b82f6',
    bank_fee: '#8b5cf6',
  }
  return map[cat] || '#6b7280'
}

function actionColor(action: string): string {
  const map: Record<string, string> = {
    review: '#eab308',
    create_receipt: '#3b82f6',
    ignore: '#6b7280',
    investigate: '#ef4444',
  }
  return map[action] || '#6b7280'
}

function exportCSV() {
  if (!batch.value?.match_result) return
  const mr = batch.value.match_result
  const rows = [['Type', 'ID', 'Amount', 'Date', 'Description', 'Match Status']]

  for (const p of mr.matched_pairs) {
    rows.push(['Matched Record', p.record_id, String(p.record_amount), '', '', 'matched'])
    rows.push(['Matched Bank', p.bank_id, String(p.bank_amount), '', '', 'matched'])
  }
  for (const u of mr.unmatched_records) {
    rows.push(['Record', u.id, String(u.amount), u.date || '', u.description || '', 'unmatched'])
  }
  for (const u of mr.unmatched_bank) {
    rows.push(['Bank', u.id, String(u.amount), u.date || '', u.description || '', 'unmatched'])
  }

  const csv = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `bank-recon-${batch.value.period}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="bank-recon">
    <div class="header">
      <h1>Bank & Billing Reconciliation</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="showHistory = !showHistory; if (showHistory) loadHistory()">
          {{ showHistory ? 'Hide' : 'Show' }} History
        </button>
        <button v-if="batch" class="btn btn-outline" @click="reset">New Reconciliation</button>
      </div>
    </div>

    <!-- Stepper -->
    <div class="stepper">
      <div
        v-for="(step, i) in STEPS"
        :key="step"
        class="step"
        :class="{ active: i === currentStep, done: i < currentStep }"
      >
        <div class="step-circle">{{ i < currentStep ? '✓' : i + 1 }}</div>
        <span class="step-label">{{ step }}</span>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = ''">✕</button>
    </div>

    <!-- History panel -->
    <div v-if="showHistory" class="history-panel">
      <h3>Batch History</h3>
      <div v-if="historyLoading" class="loading">Loading...</div>
      <div v-else-if="batches.length === 0" class="empty">No batches yet.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Period</th>
            <th>Status</th>
            <th>Entries</th>
            <th>Match Rate</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in batches" :key="b.id">
            <td>{{ b.period }}</td>
            <td><span class="status-badge" :class="b.status">{{ b.status }}</span></td>
            <td>{{ b.total_entries }}</td>
            <td>{{ b.match_rate != null ? (b.match_rate * 100).toFixed(1) + '%' : '—' }}</td>
            <td>{{ new Date(b.created_at).toLocaleString() }}</td>
            <td><button class="btn btn-sm" @click="loadBatch(b.id)">View</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Step 0: Upload -->
    <div v-if="currentStep === 0" class="step-content">
      <div
        class="drop-zone"
        :class="{ 'drag-over': dragOver }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @click="($refs.fileInput as HTMLInputElement)?.click()"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".csv,.xlsx,.xls,.pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp"
          style="display:none"
          @change="handleFileInput"
        />
        <div class="drop-icon">📂</div>
        <p>Drop bank statements, billing exports, or POS files here</p>
        <p class="hint">Supports CSV, Excel, PDF, Images (JPG/PNG)</p>
      </div>

      <div v-if="files.length" class="file-list">
        <div v-for="(f, i) in files" :key="i" class="file-item">
          <span class="file-icon">{{ fileTypeIcon(f.name) }}</span>
          <span class="file-name">{{ f.name }}</span>
          <span class="file-size">{{ formatSize(f.size) }}</span>
          <button class="remove-btn" @click="removeFile(i)">✕</button>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Period</label>
          <input v-model="period" type="month" />
        </div>
        <div class="form-group">
          <label>Recon Session ID (optional)</label>
          <input v-model="sessionId" placeholder="Link to existing session" />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Amount Tolerance (PHP)</label>
          <input v-model.number="amountTolerance" type="number" step="0.01" min="0" />
        </div>
        <div class="form-group">
          <label>Date Tolerance (days)</label>
          <input v-model.number="dateTolerance" type="number" min="0" max="30" />
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input v-model="runAI" type="checkbox" />
            Run AI Analysis
          </label>
        </div>
      </div>

      <button class="btn btn-primary" :disabled="!canProcess" @click="startProcess">
        Start Reconciliation
      </button>
    </div>

    <!-- Step 1: Parsing -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Parsing {{ files.length }} file(s)... This may take a moment for PDF/image files.</p>
      </div>
    </div>

    <!-- Step 2: Matching Results -->
    <div v-if="currentStep === 2 && batch" class="step-content">
      <h2>Matching Results</h2>

      <!-- Parse summary -->
      <div class="cards-row">
        <div v-for="sf in (batch.source_files ?? [])" :key="sf.filename" class="info-card">
          <div class="card-header">
            <span>{{ sf.filename }}</span>
            <span class="badge" :class="sf.format_detected ? 'success' : 'warn'">
              {{ sf.format_detected ? sf.bank_name : 'Generic' }}
            </span>
          </div>
          <div class="card-body">
            <span>{{ sf.row_count }} entries</span>
            <span class="muted">{{ sf.file_type.toUpperCase() }}</span>
          </div>
        </div>
      </div>

      <!-- Match stats grid -->
      <div class="stats-grid">
        <div class="stat-card matched">
          <div class="stat-value">{{ matchedCount }}</div>
          <div class="stat-label">Matched Pairs</div>
        </div>
        <div class="stat-card unmatched">
          <div class="stat-value">{{ unmatchedBankCount }}</div>
          <div class="stat-label">Unmatched Bank</div>
        </div>
        <div class="stat-card unmatched">
          <div class="stat-value">{{ unmatchedRecordCount }}</div>
          <div class="stat-label">Unmatched Records</div>
        </div>
        <div class="stat-card rate">
          <div class="stat-value">{{ matchRate }}%</div>
          <div class="stat-label">Match Rate</div>
        </div>
      </div>

      <!-- Matched pairs table -->
      <div v-if="matchedCount > 0" class="section">
        <h3>Matched Pairs</h3>
        <table class="data-table">
          <thead>
            <tr><th>Record</th><th>Bank Entry</th><th>Record Amt</th><th>Bank Amt</th><th>Date Diff</th></tr>
          </thead>
          <tbody>
            <tr v-for="p in batch.match_result!.matched_pairs.slice(0, 50)" :key="p.match_group_id">
              <td>{{ p.record_id }}</td>
              <td>{{ p.bank_id }}</td>
              <td class="amount">{{ p.record_amount.toFixed(2) }}</td>
              <td class="amount">{{ p.bank_amount.toFixed(2) }}</td>
              <td>{{ p.date_diff_days != null ? p.date_diff_days + 'd' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Unmatched bank -->
      <div v-if="unmatchedBankCount > 0" class="section">
        <h3>Unmatched Bank Entries</h3>
        <table class="data-table">
          <thead><tr><th>ID</th><th>Date</th><th>Amount</th><th>Description</th></tr></thead>
          <tbody>
            <tr v-for="u in batch.match_result!.unmatched_bank.slice(0, 50)" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.date || '—' }}</td>
              <td class="amount">{{ u.amount.toFixed(2) }}</td>
              <td>{{ u.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Unmatched records -->
      <div v-if="unmatchedRecordCount > 0" class="section">
        <h3>Unmatched Records</h3>
        <table class="data-table">
          <thead><tr><th>ID</th><th>Date</th><th>Amount</th><th>Description</th></tr></thead>
          <tbody>
            <tr v-for="u in batch.match_result!.unmatched_records.slice(0, 50)" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.date || '—' }}</td>
              <td class="amount">{{ u.amount.toFixed(2) }}</td>
              <td>{{ u.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button v-if="batch.ai_suggestions?.length || batch.ai_explanations?.length"
          class="btn btn-primary" @click="currentStep = 3">
          View AI Analysis
        </button>
        <button class="btn btn-outline" @click="goToSummary">Go to Summary</button>
      </div>
    </div>

    <!-- Step 3: AI Analysis -->
    <div v-if="currentStep === 3 && batch" class="step-content">
      <h2>AI Analysis</h2>

      <!-- Suggestions -->
      <div v-if="batch.ai_suggestions?.length" class="section">
        <h3>Match Suggestions ({{ pendingSuggestions.length }} pending)</h3>
        <div class="suggestion-cards">
          <div v-for="(s, i) in batch.ai_suggestions" :key="i"
            class="suggestion-card" :class="s.status">
            <div class="suggestion-header">
              <span class="category-badge" :style="{ background: categoryColor(s.category) }">
                {{ s.category.replace('_', ' ') }}
              </span>
              <span class="confidence">{{ (s.confidence * 100).toFixed(0) }}%</span>
              <span v-if="s.status !== 'pending'" class="status-tag" :class="s.status">
                {{ s.status }}
              </span>
            </div>
            <p class="explanation">{{ s.explanation }}</p>
            <div v-if="s.status === 'pending'" class="suggestion-actions">
              <button class="btn btn-sm btn-success" @click="acceptSuggestion(i)">Accept</button>
              <button class="btn btn-sm btn-danger" @click="rejectSuggestion(i)">Reject</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Mismatch explanations -->
      <div v-if="batch.ai_explanations?.length" class="section">
        <h3>Mismatch Explanations</h3>
        <div class="explanation-cards">
          <div v-for="(e, i) in batch.ai_explanations" :key="i" class="explanation-card">
            <div class="explanation-header">
              <span class="type-badge">{{ e.entry_type }}</span>
              <span class="mismatch-badge">{{ e.mismatch_type.replace('_', ' ') }}</span>
              <span class="action-badge" :style="{ background: actionColor(e.recommended_action) }">
                {{ e.recommended_action }}
              </span>
            </div>
            <p>{{ e.explanation }}</p>
          </div>
        </div>
      </div>

      <div v-if="!batch.ai_suggestions?.length && !batch.ai_explanations?.length" class="empty">
        No AI analysis results available.
        <button class="btn btn-outline" @click="rerunAnalysis" :disabled="processing">
          Run AI Analysis
        </button>
      </div>

      <div class="actions">
        <button class="btn btn-outline" @click="currentStep = 2">Back to Matching</button>
        <button class="btn btn-primary" @click="goToSummary">Go to Summary</button>
      </div>
    </div>

    <!-- Step 4: Summary -->
    <div v-if="currentStep === 4 && batch" class="step-content">
      <h2>Reconciliation Summary</h2>

      <div class="summary-grid">
        <div class="summary-card">
          <h4>Files Processed</h4>
          <p>{{ batch.source_files?.length ?? 0 }} files, {{ batch.total_entries }} entries</p>
        </div>
        <div class="summary-card">
          <h4>Match Rate</h4>
          <p class="big-number">{{ matchRate }}%</p>
        </div>
        <div class="summary-card">
          <h4>Matched / Unmatched</h4>
          <p>{{ matchedCount }} matched, {{ unmatchedBankCount + unmatchedRecordCount }} unmatched</p>
        </div>
        <div class="summary-card">
          <h4>AI Suggestions</h4>
          <p>{{ acceptedSuggestions.length }} accepted, {{ pendingSuggestions.length }} pending</p>
        </div>
      </div>

      <div class="summary-details">
        <h3>Source Files</h3>
        <table class="data-table">
          <thead><tr><th>File</th><th>Type</th><th>Format</th><th>Entries</th></tr></thead>
          <tbody>
            <tr v-for="sf in (batch.source_files ?? [])" :key="sf.filename">
              <td>{{ sf.filename }}</td>
              <td>{{ sf.file_type.toUpperCase() }}</td>
              <td>{{ sf.bank_name || 'Generic' }}</td>
              <td>{{ sf.row_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button class="btn btn-outline" @click="currentStep = 2">View Matching</button>
        <button v-if="batch.ai_suggestions?.length" class="btn btn-outline" @click="currentStep = 3">
          View AI Analysis
        </button>
        <button class="btn btn-primary" @click="exportCSV">Export CSV</button>
        <button class="btn btn-outline" @click="reset">New Reconciliation</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bank-recon {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header h1 { font-size: 24px; }
.header-actions { display: flex; gap: 8px; }

/* Stepper */
.stepper {
  display: flex;
  gap: 4px;
  margin-bottom: 32px;
}
.step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 13px;
  color: #64748b;
  transition: all 0.2s;
}
.step.active { background: #4f46e5; color: #fff; }
.step.done { background: #e0e7ff; color: #4f46e5; }
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.1);
  font-weight: 600;
  font-size: 12px;
}
.step.active .step-circle { background: rgba(255,255,255,0.2); }
.step.done .step-circle { background: #4f46e5; color: #fff; }

/* Error */
.error-banner {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-banner button {
  background: none;
  border: none;
  color: #dc2626;
  cursor: pointer;
  font-size: 16px;
}

/* Drop zone */
.drop-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: #4f46e5;
  background: #f5f3ff;
}
.drop-icon { font-size: 48px; margin-bottom: 12px; }
.drop-zone p { margin: 4px 0; color: #475569; }
.hint { font-size: 13px; color: #94a3b8; }

/* File list */
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
}
.file-icon { font-size: 20px; }
.file-name { flex: 1; font-size: 14px; }
.file-size { color: #94a3b8; font-size: 13px; }
.remove-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 16px;
}
.remove-btn:hover { color: #ef4444; }

/* Form */
.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.form-group {
  flex: 1;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  color: #475569;
}
.form-group input[type="month"],
.form-group input[type="text"],
.form-group input[type="number"],
.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}
.checkbox-group {
  display: flex;
  align-items: flex-end;
}
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #4338ca; }
.btn-outline { background: #fff; border: 1px solid #e2e8f0; color: #475569; }
.btn-outline:hover:not(:disabled) { background: #f8fafc; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.btn-success { background: #22c55e; color: #fff; }
.btn-danger { background: #ef4444; color: #fff; }

/* Loading */
.loading-state {
  text-align: center;
  padding: 64px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.stat-card {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.stat-card.matched { border-left: 4px solid #22c55e; }
.stat-card.unmatched { border-left: 4px solid #ef4444; }
.stat-card.rate { border-left: 4px solid #4f46e5; }
.stat-value { font-size: 28px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 13px; color: #64748b; margin-top: 4px; }

/* Cards row */
.cards-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.info-card {
  flex: 1;
  min-width: 200px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
}
.card-body {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #64748b;
}

/* Badges */
.badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}
.badge.success { background: #dcfce7; color: #16a34a; }
.badge.warn { background: #fef9c3; color: #ca8a04; }

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}
.status-badge.completed { background: #dcfce7; color: #16a34a; }
.status-badge.failed { background: #fef2f2; color: #dc2626; }
.status-badge.pending { background: #fef9c3; color: #ca8a04; }
.status-badge.parsing, .status-badge.matching, .status-badge.analyzing {
  background: #dbeafe; color: #2563eb;
}

/* Data table */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 16px;
}
.data-table th {
  text-align: left;
  padding: 8px 12px;
  background: #f1f5f9;
  font-weight: 500;
  color: #475569;
}
.data-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
}
.amount { font-family: monospace; text-align: right; }

/* Suggestion cards */
.suggestion-cards, .explanation-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}
.suggestion-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
}
.suggestion-card.accepted { border-color: #22c55e; background: #f0fdf4; }
.suggestion-card.rejected { border-color: #ef4444; background: #fef2f2; opacity: 0.7; }
.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.category-badge {
  padding: 2px 8px;
  border-radius: 12px;
  color: #fff;
  font-size: 11px;
  font-weight: 500;
}
.confidence {
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}
.status-tag {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
}
.status-tag.accepted { background: #dcfce7; color: #16a34a; }
.status-tag.rejected { background: #fef2f2; color: #dc2626; }
.explanation { font-size: 13px; color: #475569; margin: 0; }
.suggestion-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.explanation-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
}
.explanation-header {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}
.type-badge, .mismatch-badge, .action-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}
.type-badge { background: #e0e7ff; color: #4f46e5; }
.mismatch-badge { background: #fef3c7; color: #92400e; }
.action-badge { color: #fff; }

/* Summary */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.summary-card {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
}
.summary-card h4 { font-size: 13px; color: #64748b; margin: 0 0 8px; }
.summary-card p { font-size: 16px; font-weight: 500; margin: 0; }
.big-number { font-size: 32px !important; font-weight: 700 !important; color: #4f46e5; }

.summary-details { margin-bottom: 24px; }
.summary-details h3 { font-size: 16px; margin-bottom: 12px; }

/* Section */
.section { margin-bottom: 24px; }
.section h3 { font-size: 16px; margin-bottom: 12px; }

/* Actions */
.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

/* History */
.history-panel {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 24px;
}
.history-panel h3 { margin: 0 0 12px; font-size: 16px; }

.loading { text-align: center; padding: 24px; color: #64748b; }
.empty { text-align: center; padding: 24px; color: #94a3b8; }
.muted { color: #94a3b8; }

.step-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
