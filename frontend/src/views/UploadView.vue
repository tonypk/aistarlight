<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi } from '../api/data'
import { parseFileInBrowser, estimateJsonSize } from '../utils/fileParser'
import FileUploader from '../components/upload/FileUploader.vue'
import { useUploadStore } from '../stores/upload'
import { useAuthStore } from '../stores/auth'
import { getReportTypes } from '../config/targetFieldsByReportType'

const router = useRouter()
const uploadStore = useUploadStore()
const authStore = useAuthStore()
const REPORT_TYPES = computed(() => getReportTypes(authStore.jurisdiction))
const uploading = ref(false)
const uploadProgress = ref(0)
const progressStage = ref('')
const error = ref('')
const errorCode = ref<'size' | 'format' | 'parse' | 'network' | 'server' | ''>('')
const lastFile = ref<File | null>(null)
const fileUploaderRef = ref<InstanceType<typeof FileUploader> | null>(null)

/**
 * Files <= 10MB: upload raw to server (server parses)
 * Files > 10MB: parse in browser with SheetJS, send JSON (much smaller)
 */
const RAW_UPLOAD_THRESHOLD = 10 * 1024 * 1024 // 10MB

const errorHint = computed(() => {
  switch (errorCode.value) {
    case 'size':
      return 'Try removing unnecessary columns or splitting into multiple sheets.'
    case 'format':
      return 'Save your file as .xlsx or .csv and try again.'
    case 'parse':
      return 'Make sure the file is not corrupted and the first row contains column headers.'
    case 'network':
      return 'Check your internet connection and try again.'
    default:
      return ''
  }
})

function classifyError(err: unknown): void {
  // Browser parse errors (thrown directly as Error, not from axios)
  if (err instanceof Error && !('response' in err)) {
    errorCode.value = 'parse'
    error.value = err.message || 'Failed to read file in browser.'
    return
  }

  // Axios errors
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const e = err as any

  const code: string = e?.code || ''
  const message: string = e?.message || ''

  if (code === 'ERR_NETWORK' || code === 'ECONNABORTED' || message.includes('timeout')) {
    errorCode.value = 'network'
    error.value = 'Upload timed out or network error occurred.'
    return
  }

  const status: number | undefined = e?.response?.status
  const detail: string = e?.response?.data?.error || ''

  if (status === 413 || detail.toLowerCase().includes('too large') || detail.toLowerCase().includes('exceeds')) {
    errorCode.value = 'size'
    error.value = detail || 'File is too large.'
    return
  }

  if (status === 415 || detail.toLowerCase().includes('unsupported') || detail.toLowerCase().includes('format')) {
    errorCode.value = 'format'
    error.value = detail || 'Unsupported file format.'
    return
  }

  if (
    status === 400 &&
    (detail.toLowerCase().includes('parse') ||
      detail.toLowerCase().includes('empty') ||
      detail.toLowerCase().includes('cannot open'))
  ) {
    errorCode.value = 'parse'
    error.value = detail || 'Failed to parse file.'
    return
  }

  errorCode.value = 'server'
  error.value = detail || 'Failed to upload file. Please try again.'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function handleFileUploaded(file: File) {
  uploading.value = true
  uploadProgress.value = 0
  progressStage.value = ''
  error.value = ''
  errorCode.value = ''
  lastFile.value = file
  uploadStore.clear()

  try {
    if (file.size > RAW_UPLOAD_THRESHOLD) {
      // Large file: parse in browser, send JSON
      await handleLargeFile(file)
    } else {
      // Small file: upload raw to server
      await handleSmallFile(file)
    }
  } catch (e: unknown) {
    classifyError(e)
    fileUploaderRef.value?.clearFile()
  } finally {
    uploading.value = false
  }
}

async function handleSmallFile(file: File) {
  progressStage.value = 'Uploading file...'
  const res = await dataApi.upload(file, (progress) => {
    uploadProgress.value = Math.round(progress * 80)
    if (progress > 0.5) progressStage.value = 'Parsing on server...'
  })
  uploadProgress.value = 100
  progressStage.value = 'Done!'
  uploadStore.setUploadResult(res.data.data)
}

async function handleLargeFile(file: File) {
  // Step 1: Parse in browser (0-60%)
  progressStage.value = `Reading file (${formatSize(file.size)})...`
  uploadProgress.value = 5

  const parsed = await parseFileInBrowser(file, (stage) => {
    progressStage.value = stage
    // Increment progress during parsing
    if (uploadProgress.value < 55) {
      uploadProgress.value += 5
    }
  })
  uploadProgress.value = 60

  // Step 2: Send JSON to server (60-95%)
  const jsonSize = estimateJsonSize(parsed)
  progressStage.value = `Sending data (${formatSize(jsonSize)})...`

  const res = await dataApi.uploadParsed(parsed, (progress) => {
    uploadProgress.value = 60 + Math.round(progress * 35)
  })

  uploadProgress.value = 100
  progressStage.value = 'Done!'
  uploadStore.setUploadResult(res.data.data)
}

function retry() {
  if (lastFile.value) {
    handleFileUploaded(lastFile.value)
  }
}

function proceedToMapping() {
  router.push('/mapping')
}
</script>

<template>
  <div class="upload-view">
    <h2>Upload Financial Data</h2>
    <p class="desc">Upload your sales and purchase records (Excel or CSV)</p>

    <FileUploader ref="fileUploaderRef" @uploaded="handleFileUploaded" />

    <!-- Report Type Selector -->
    <div class="report-type-section">
      <label class="report-type-label">Report Type</label>
      <select
        class="report-type-select"
        data-testid="upload-report-type"
        :value="uploadStore.reportType"
        @change="uploadStore.setReportType(($event.target as HTMLSelectElement).value)"
      >
        <option v-for="rt in REPORT_TYPES" :key="rt.value" :value="rt.value">
          {{ rt.label }}
        </option>
      </select>
    </div>

    <!-- Upload Progress -->
    <Transition name="fade">
      <div v-if="uploading" class="progress-section" data-testid="upload-progress">
        <div class="progress-bar-wrap">
          <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <div class="progress-info">
          <span class="progress-text">{{ progressStage }}</span>
          <span class="progress-pct">{{ uploadProgress }}%</span>
        </div>
      </div>
    </Transition>

    <!-- Error with retry -->
    <Transition name="slide">
      <div v-if="error && !uploading" class="error-section">
        <div class="error-banner">
          <div class="error-main">
            <svg class="error-svg" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clip-rule="evenodd"
              />
            </svg>
            <div class="error-text">
              <p class="error-msg">{{ error }}</p>
              <p v-if="errorHint" class="error-hint">{{ errorHint }}</p>
            </div>
          </div>
          <button
            v-if="lastFile && (errorCode === 'network' || errorCode === 'server')"
            class="retry-btn"
            @click="retry"
          >
            Retry
          </button>
        </div>
      </div>
    </Transition>

    <!-- Success: file preview -->
    <Transition name="fade">
      <div v-if="uploadStore.hasFile && !uploading" class="preview-section" data-testid="upload-success">
        <div class="file-info">
          <svg class="check-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clip-rule="evenodd"
            />
          </svg>
          <span data-testid="upload-filename">Uploaded: <strong>{{ uploadStore.filename }}</strong></span>
        </div>

        <div v-for="(sheet, name) in uploadStore.sheets" :key="name" class="sheet">
          <h3>Sheet: {{ name }} <span class="row-badge">{{ sheet.row_count }} rows</span></h3>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th v-for="col in sheet.columns" :key="col">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in sheet.preview.slice(0, 5)" :key="i">
                  <td v-for="col in sheet.columns" :key="col">{{ row[col] ?? '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <button class="proceed-btn" @click="proceedToMapping" data-testid="upload-proceed-btn">
          Proceed to Column Mapping
          <svg class="arrow-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.upload-view {
  max-width: 900px;
  margin: 0 auto;
}
.upload-view h2 {
  margin-bottom: 8px;
}
.desc {
  color: #888;
  margin-bottom: 24px;
}

/* Report Type */
.report-type-section {
  margin: 16px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}
.report-type-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}
.report-type-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  background: #fff;
  min-width: 280px;
}
.report-type-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
}

/* Progress */
.progress-section {
  margin-top: 20px;
}
.progress-bar-wrap {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #818cf8);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 13px;
}
.progress-text {
  color: #4f46e5;
}
.progress-pct {
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
}

/* Error */
.error-section {
  margin-top: 16px;
}
.error-banner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
}
.error-main {
  display: flex;
  gap: 10px;
  flex: 1;
}
.error-svg {
  width: 20px;
  height: 20px;
  color: #ef4444;
  flex-shrink: 0;
  margin-top: 1px;
}
.error-msg {
  margin: 0;
  color: #dc2626;
  font-size: 14px;
  font-weight: 500;
}
.error-hint {
  margin: 4px 0 0 0;
  color: #9ca3af;
  font-size: 13px;
}
.retry-btn {
  padding: 6px 16px;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  background: #fff;
  color: #dc2626;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.retry-btn:hover {
  background: #fef2f2;
  border-color: #dc2626;
}

/* Success preview */
.preview-section {
  margin-top: 24px;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #166534;
  font-size: 14px;
}
.check-icon {
  width: 20px;
  height: 20px;
  color: #22c55e;
  flex-shrink: 0;
}

.sheet {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}
.sheet h3 {
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.row-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 4px;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  background: #f9fafb;
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
}
td {
  padding: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.proceed-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 28px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.proceed-btn:hover {
  background: #4338ca;
}
.arrow-icon {
  width: 18px;
  height: 18px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
