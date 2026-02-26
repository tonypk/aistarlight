<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { receiptsApi } from '@/api/receipts'
import { compressBatch, type CompressResult } from '@/utils/imageCompressor'
import { useAccountingStore } from '@/stores/accounting'

const router = useRouter()
const accounting = useAccountingStore()
const converting = ref(false)

// State
const files = ref<File[]>([])
const previews = ref<{ name: string; url: string; size: string; originalSize: string; compressed: boolean }[]>([])
const period = ref('')
const reportType = ref('BIR_2550M')
const processing = ref(false)
const compressing = ref(false)
const compressProgress = ref({ done: 0, total: 0 })
const currentStep = ref(0)
const result = ref<any>(null)
const error = ref('')
const dragOver = ref(false)

// Compression stats
const compressionStats = ref<{ totalOriginal: number; totalCompressed: number } | null>(null)

// Batch history
const batches = ref<any[]>([])
const showHistory = ref(false)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp']
const MAX_FILES = 50
const STEPS = ['Compress', 'Upload', 'OCR', 'Parse', 'Report']

// Default period to current month
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
period.value = defaultPeriod

const canProcess = computed(() =>
  files.value.length > 0 && period.value && !processing.value && !compressing.value
)

const successCount = computed(() =>
  result.value?.results?.filter((r: any) => r.status === 'success').length ?? 0
)
const failCount = computed(() =>
  result.value?.results?.filter((r: any) => r.status === 'failed').length ?? 0
)

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
  if (e.dataTransfer?.files) {
    addFiles(Array.from(e.dataTransfer.files))
  }
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    addFiles(Array.from(input.files))
  }
  input.value = ''
}

async function addFiles(newFiles: File[]) {
  const valid = newFiles.filter(f => {
    const ext = f.name.split('.').pop()?.toLowerCase()
    return ALLOWED_TYPES.includes(f.type) || ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp'].includes(ext || '')
  })

  const remaining = MAX_FILES - files.value.length
  const toAdd = valid.slice(0, remaining)

  if (toAdd.length === 0) return

  // Compress images in browser before adding
  compressing.value = true
  compressProgress.value = { done: 0, total: toAdd.length }

  try {
    const results = await compressBatch(
      toAdd,
      { maxDimension: 2048, quality: 0.80, grayscale: false, maxFileSize: 2 * 1024 * 1024 },
      (done, total) => {
        compressProgress.value = { done, total }
      }
    )

    let totalOriginal = compressionStats.value?.totalOriginal ?? 0
    let totalCompressed = compressionStats.value?.totalCompressed ?? 0

    const compressedFiles: File[] = []
    results.forEach((r: CompressResult) => {
      compressedFiles.push(r.file)
      totalOriginal += r.originalSize
      totalCompressed += r.compressedSize
      previews.value.push({
        name: r.file.name,
        url: URL.createObjectURL(r.blob),
        size: formatSize(r.compressedSize),
        originalSize: formatSize(r.originalSize),
        compressed: r.ratio < 0.95,
      })
    })

    files.value = [...files.value, ...compressedFiles]
    compressionStats.value = { totalOriginal, totalCompressed }
  } catch (err: any) {
    error.value = `Image compression failed: ${err.message}`
  } finally {
    compressing.value = false
  }
}

function removeFile(index: number) {
  URL.revokeObjectURL(previews.value[index].url)
  files.value = files.value.filter((_, i) => i !== index)
  previews.value = previews.value.filter((_, i) => i !== index)
}

function clearFiles() {
  previews.value.forEach(p => URL.revokeObjectURL(p.url))
  files.value = []
  previews.value = []
  compressionStats.value = null
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function processReceipts() {
  processing.value = true
  error.value = ''
  result.value = null
  currentStep.value = 1

  // Simulate step progression
  const stepTimer = setInterval(() => {
    if (currentStep.value < 4) {
      currentStep.value++
    }
  }, 3000)

  try {
    const response = await receiptsApi.upload(files.value, period.value, reportType.value)
    clearInterval(stepTimer)
    currentStep.value = 5
    result.value = response.data.data
  } catch (err: any) {
    clearInterval(stepTimer)
    currentStep.value = 0
    error.value = err.response?.data?.detail || err.response?.data?.error || err.message || 'Processing failed'
  } finally {
    processing.value = false
  }
}

async function loadHistory() {
  try {
    const response = await receiptsApi.listBatches({ page: 1, limit: 10 })
    batches.value = response.data.data || []
    showHistory.value = true
  } catch {
    // Silently fail
  }
}

function goToReport(reportId: string) {
  router.push(`/reports/${reportId}/edit`)
}

function goToSession(sessionId: string) {
  router.push({
    path: '/reconciliation',
    query: { session: sessionId },
  })
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.85) return '#22c55e'
  if (confidence >= 0.60) return '#eab308'
  return '#ef4444'
}

async function convertToTransactions() {
  if (!result.value?.batch_id || !result.value?.session_id) return
  converting.value = true
  try {
    await accounting.convertReceiptToTransactions(result.value.batch_id, result.value.session_id)
    router.push({ path: '/classification', query: { session: result.value.session_id } })
  } finally {
    converting.value = false
  }
}

const batchActionLoading = ref<string | null>(null)

async function convertBatch(batch: any) {
  if (!batch.id || !batch.session_id) return
  batchActionLoading.value = `convert-${batch.id}`
  try {
    await accounting.convertReceiptToTransactions(batch.id, batch.session_id)
    showHistory.value = false
    router.push({ path: '/classification', query: { session: batch.session_id } })
  } catch {
    error.value = 'Failed to convert batch to transactions'
  } finally {
    batchActionLoading.value = null
  }
}

async function generateJournalsForBatch(batch: any) {
  if (!batch.session_id) return
  batchActionLoading.value = `journal-${batch.id}`
  try {
    await accounting.generateJournalsFromSession(batch.session_id)
    showHistory.value = false
    router.push('/journal-entries')
  } catch {
    error.value = 'Failed to generate journal entries'
  } finally {
    batchActionLoading.value = null
  }
}

function reset() {
  clearFiles()
  result.value = null
  error.value = ''
  currentStep.value = 0
}
</script>

<template>
  <div class="receipt-upload">
    <div class="page-header">
      <h1>Receipt Scanner</h1>
      <p class="subtitle">Upload receipt images for automatic OCR, parsing, and BIR report generation</p>
      <button class="btn-secondary" @click="loadHistory">View History</button>
    </div>

    <!-- Step Progress -->
    <div v-if="processing || currentStep === 5" class="steps">
      <div
        v-for="(step, i) in STEPS"
        :key="step"
        class="step"
        :class="{
          active: currentStep === i + 1,
          done: currentStep > i + 1,
        }"
      >
        <div class="step-indicator">
          <span v-if="currentStep > i + 1" class="check">&#10003;</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="step-label">{{ step }}</span>
      </div>
    </div>

    <!-- Upload Section (shown when no result) -->
    <div v-if="!result" class="upload-section">
      <!-- Drop Zone -->
      <div
        class="drop-zone"
        :class="{ 'drag-over': dragOver }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @click="($refs.fileInput as HTMLInputElement)?.click()"
      >
        <div class="drop-content">
          <span class="drop-icon">&#128247;</span>
          <p>Drag & drop receipt images here</p>
          <p class="drop-hint">or click to browse (JPG, PNG, TIFF, WEBP — max {{ MAX_FILES }} files)</p>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp"
          multiple
          hidden
          @change="handleFileInput"
        />
      </div>

      <!-- Compressing Indicator -->
      <div v-if="compressing" class="compress-status">
        <div class="compress-spinner"></div>
        <span>Compressing images... {{ compressProgress.done }}/{{ compressProgress.total }}</span>
        <div class="compress-bar">
          <div class="compress-bar-fill" :style="{ width: (compressProgress.total ? compressProgress.done / compressProgress.total * 100 : 0) + '%' }"></div>
        </div>
      </div>

      <!-- Compression Stats -->
      <div v-if="compressionStats && !compressing" class="compress-stats">
        <span class="stats-label">Compressed:</span>
        <span class="stats-original">{{ formatSize(compressionStats.totalOriginal) }}</span>
        <span class="stats-arrow">&rarr;</span>
        <span class="stats-compressed">{{ formatSize(compressionStats.totalCompressed) }}</span>
        <span class="stats-ratio">({{ ((1 - compressionStats.totalCompressed / compressionStats.totalOriginal) * 100).toFixed(0) }}% saved)</span>
      </div>

      <!-- Previews -->
      <div v-if="previews.length > 0" class="preview-section">
        <div class="preview-header">
          <span>{{ previews.length }} file(s) selected</span>
          <button class="btn-text" @click="clearFiles">Clear All</button>
        </div>
        <div class="preview-grid">
          <div v-for="(p, i) in previews" :key="i" class="preview-card">
            <img :src="p.url" :alt="p.name" class="preview-img" />
            <div class="preview-info">
              <span class="preview-name" :title="p.name">{{ p.name }}</span>
              <span class="preview-size">
                {{ p.size }}
                <span v-if="p.compressed" class="size-saved" :title="'Original: ' + p.originalSize">
                  &darr;{{ p.originalSize }}
                </span>
              </span>
            </div>
            <button class="remove-btn" @click.stop="removeFile(i)">&times;</button>
          </div>
        </div>
      </div>

      <!-- Parameters -->
      <div class="params">
        <div class="param-group">
          <label>Tax Period</label>
          <input type="month" v-model="period" />
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="error-banner">{{ error }}</div>

      <!-- Process Button -->
      <button
        class="btn-primary process-btn"
        :disabled="!canProcess"
        @click="processReceipts"
      >
        <span v-if="processing" class="spinner"></span>
        {{ processing ? 'Processing...' : 'Process Receipts' }}
      </button>
    </div>

    <!-- Results Section -->
    <div v-if="result" class="results-section">
      <div class="results-summary">
        <div class="summary-card success">
          <span class="summary-number">{{ successCount }}</span>
          <span class="summary-label">Parsed</span>
        </div>
        <div class="summary-card" :class="failCount > 0 ? 'fail' : 'neutral'">
          <span class="summary-number">{{ failCount }}</span>
          <span class="summary-label">Failed</span>
        </div>
        <div class="summary-card neutral">
          <span class="summary-number">{{ result.total_images }}</span>
          <span class="summary-label">Total</span>
        </div>
      </div>

      <!-- Receipt Results Table -->
      <div class="results-table-wrap">
        <table class="results-table">
          <thead>
            <tr>
              <th>#</th>
              <th>File</th>
              <th>Vendor</th>
              <th>Amount</th>
              <th>VAT Type</th>
              <th>Date</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in result.results" :key="i" :class="{ 'row-failed': r.status === 'failed' }">
              <td>{{ i + 1 }}</td>
              <td class="cell-filename" :title="r.filename">{{ r.filename }}</td>
              <td>{{ r.vendor_name || '—' }}</td>
              <td class="cell-amount">
                {{ r.total_amount ? `₱${Number(r.total_amount).toLocaleString('en', { minimumFractionDigits: 2 })}` : '—' }}
              </td>
              <td>
                <span class="badge" :class="'badge-' + (r.vat_type || 'unknown')">
                  {{ r.vat_type || '—' }}
                </span>
              </td>
              <td>{{ r.date || '—' }}</td>
              <td>
                <span
                  v-if="r.overall_confidence != null"
                  class="confidence"
                  :style="{ color: confidenceColor(r.overall_confidence) }"
                >
                  {{ (r.overall_confidence * 100).toFixed(0) }}%
                </span>
                <span v-else>—</span>
              </td>
              <td>
                <span class="status-badge" :class="'status-' + r.status">
                  {{ r.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Action Links -->
      <div class="result-actions">
        <button
          v-if="result.report_id"
          class="btn-primary"
          @click="goToReport(result.report_id)"
        >
          View Report
        </button>
        <button
          v-if="result.session_id"
          class="btn-secondary"
          @click="goToSession(result.session_id)"
        >
          View Transactions
        </button>
        <button
          v-if="result.batch_id && result.session_id"
          class="btn-bridge"
          :disabled="converting"
          @click="convertToTransactions"
        >
          {{ converting ? 'Converting...' : 'Convert to Transactions' }}
        </button>
        <button class="btn-secondary" @click="reset">
          Upload More
        </button>
      </div>
    </div>

    <!-- Batch History Modal -->
    <div v-if="showHistory" class="modal-overlay" @click.self="showHistory = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Receipt Batch History</h2>
          <button class="close-btn" @click="showHistory = false">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="batches.length === 0" class="empty-state">No batches yet.</div>
          <table v-else class="results-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Period</th>
                <th>Images</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in batches" :key="b.id">
                <td>{{ new Date(b.created_at).toLocaleDateString() }}</td>
                <td>{{ b.period }}</td>
                <td>{{ b.processed_count }}/{{ b.total_images }}</td>
                <td>
                  <span class="status-badge" :class="'status-' + b.status">{{ b.status }}</span>
                </td>
                <td class="batch-actions">
                  <button v-if="b.report_id" class="btn-text" @click="goToReport(b.report_id); showHistory = false">
                    Report
                  </button>
                  <button v-if="b.session_id" class="btn-text" @click="goToSession(b.session_id); showHistory = false">
                    Transactions
                  </button>
                  <button
                    v-if="b.status === 'completed' && b.session_id"
                    class="btn-text btn-convert"
                    :disabled="batchActionLoading === `convert-${b.id}`"
                    @click="convertBatch(b)"
                  >
                    {{ batchActionLoading === `convert-${b.id}` ? 'Converting...' : 'Convert' }}
                  </button>
                  <button
                    v-if="b.status === 'completed' && b.session_id"
                    class="btn-text btn-journal"
                    :disabled="batchActionLoading === `journal-${b.id}`"
                    @click="generateJournalsForBatch(b)"
                  >
                    {{ batchActionLoading === `journal-${b.id}` ? 'Generating...' : 'Journal Entries' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.receipt-upload {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.page-header h1 { margin: 0; font-size: 24px; }
.subtitle { color: #888; margin: 0; flex: 1; }

/* Steps */
.steps {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}
.step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
}
.step.active { color: #4f46e5; font-weight: 600; }
.step.done { color: #22c55e; }
.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  background: #e5e7eb;
  color: #666;
}
.step.active .step-indicator { background: #4f46e5; color: #fff; }
.step.done .step-indicator { background: #22c55e; color: #fff; }
.check { font-size: 14px; }
.step-label { font-size: 13px; }

/* Drop Zone */
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 20px;
}
.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #4f46e5;
  background: #f5f3ff;
}
.drop-icon { font-size: 48px; display: block; margin-bottom: 8px; }
.drop-hint { color: #999; font-size: 13px; margin-top: 4px; }

/* Compress Status */
.compress-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f3ff;
  border: 1px solid #c4b5fd;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #4f46e5;
  flex-wrap: wrap;
}
.compress-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #c4b5fd;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}
.compress-bar {
  flex: 1;
  min-width: 120px;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}
.compress-bar-fill {
  height: 100%;
  background: #4f46e5;
  border-radius: 3px;
  transition: width 0.3s;
}

/* Compression Stats */
.compress-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}
.stats-label { color: #666; }
.stats-original { color: #999; text-decoration: line-through; }
.stats-arrow { color: #22c55e; font-weight: bold; }
.stats-compressed { color: #16a34a; font-weight: 600; }
.stats-ratio { color: #22c55e; font-size: 13px; }

.size-saved {
  display: block;
  font-size: 10px;
  color: #22c55e;
}

/* Previews */
.preview-section { margin-bottom: 20px; }
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}
.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.preview-card {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.preview-img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}
.preview-info {
  padding: 4px 8px;
  font-size: 11px;
}
.preview-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-size { color: #999; }
.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.6);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Params */
.params {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.param-group { display: flex; flex-direction: column; gap: 4px; }
.param-group label { font-size: 13px; color: #666; font-weight: 500; }
.param-group input,
.param-group select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

/* Buttons */
.btn-primary {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  padding: 8px 16px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn-secondary:hover { background: #f9fafb; }
.btn-bridge {
  padding: 8px 16px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn-bridge:hover { background: #047857; }
.btn-bridge:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-text {
  background: none;
  border: none;
  color: #4f46e5;
  cursor: pointer;
  font-size: 13px;
  padding: 4px 8px;
}
.btn-text:hover { text-decoration: underline; }
.btn-convert { color: #059669; }
.btn-journal { color: #d97706; }
.batch-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.process-btn { width: 100%; justify-content: center; }

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Error */
.error-banner {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-bottom: 16px;
  font-size: 14px;
}

/* Results */
.results-section { margin-top: 16px; }
.results-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.summary-card {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  background: #f8f9fa;
}
.summary-card.success { background: #f0fdf4; }
.summary-card.fail { background: #fef2f2; }
.summary-number { display: block; font-size: 28px; font-weight: 700; }
.summary-card.success .summary-number { color: #22c55e; }
.summary-card.fail .summary-number { color: #ef4444; }
.summary-label { font-size: 13px; color: #666; }

.results-table-wrap { overflow-x: auto; margin-bottom: 20px; }
.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.results-table th,
.results-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}
.results-table th { font-weight: 600; color: #374151; background: #f9fafb; }
.row-failed { background: #fef2f2; }
.cell-filename { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-amount { font-family: monospace; text-align: right; }

.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.badge-vatable { background: #dbeafe; color: #1d4ed8; }
.badge-exempt { background: #fef3c7; color: #92400e; }
.badge-zero_rated { background: #d1fae5; color: #065f46; }

.confidence { font-weight: 600; font-size: 13px; }

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.status-success { background: #d1fae5; color: #065f46; }
.status-failed { background: #fecaca; color: #991b1b; }
.status-processing { background: #dbeafe; color: #1d4ed8; }
.status-completed { background: #d1fae5; color: #065f46; }
.status-pending { background: #e5e7eb; color: #374151; }

.result-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal {
  background: #fff;
  border-radius: 12px;
  width: 700px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.modal-header h2 { margin: 0; font-size: 18px; }
.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}
.modal-body { padding: 16px 20px; overflow-y: auto; }
.empty-state { text-align: center; color: #999; padding: 32px; }
</style>
