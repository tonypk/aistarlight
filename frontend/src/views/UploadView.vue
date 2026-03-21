<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { dataApi } from '../api/data'
import { parseFileInBrowser, estimateJsonSize } from '../utils/fileParser'
import FileUploader from '../components/upload/FileUploader.vue'
import { useUploadStore } from '../stores/upload'
import { useAuthStore } from '../stores/auth'
import { getReportTypes } from '../config/targetFieldsByReportType'

const { t } = useI18n()

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
      return t('upload.errorHintSize')
    case 'format':
      return t('upload.errorHintFormat')
    case 'parse':
      return t('upload.errorHintParse')
    case 'network':
      return t('upload.errorHintNetwork')
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
  progressStage.value = t('upload.uploadingFile')
  const res = await dataApi.upload(file, (progress) => {
    uploadProgress.value = Math.round(progress * 80)
    if (progress > 0.5) progressStage.value = t('upload.parsingOnServer')
  })
  uploadProgress.value = 100
  progressStage.value = t('upload.done')
  uploadStore.setUploadResult(res.data.data)
}

async function handleLargeFile(file: File) {
  // Step 1: Parse in browser (0-60%)
  progressStage.value = t('upload.readingFile', { size: formatSize(file.size) })
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
  progressStage.value = t('upload.sendingData', { size: formatSize(jsonSize) })

  const res = await dataApi.uploadParsed(parsed, (progress) => {
    uploadProgress.value = 60 + Math.round(progress * 35)
  })

  uploadProgress.value = 100
  progressStage.value = t('upload.done')
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
    <h2>{{ t('upload.title') }}</h2>
    <p class="desc">{{ t('upload.desc') }}</p>

    <FileUploader ref="fileUploaderRef" @uploaded="handleFileUploaded" />

    <!-- Report Type Selector -->
    <div class="report-type-section">
      <label class="report-type-label">{{ t('upload.reportType') }}</label>
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
            {{ t('common.retry') }}
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
          <span data-testid="upload-filename">{{ t('upload.uploaded') }} <strong>{{ uploadStore.filename }}</strong></span>
        </div>

        <div v-for="(sheet, name) in uploadStore.sheets" :key="name" class="sheet">
          <h3>{{ t('upload.sheet', { name }) }} <span class="row-badge">{{ t('upload.rowCount', { count: sheet.row_count }) }}</span></h3>
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
          {{ t('upload.proceedToMapping') }}
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
  color: var(--text-muted);
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
  color: var(--text-primary);
  white-space: nowrap;
}
.report-type-select {
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-surface);
  min-width: 280px;
}
.report-type-select:focus {
  outline: none;
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
}

/* Progress */
.progress-section {
  margin-top: 20px;
}
.progress-bar-wrap {
  height: 6px;
  background: var(--border-default);
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-primary), #818cf8);
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
  color: var(--brand-primary);
}
.progress-pct {
  color: var(--text-muted);
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
  color: var(--text-muted);
  font-size: 13px;
}
.retry-btn {
  padding: 6px 16px;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  background: var(--bg-surface);
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
  background: var(--bg-surface);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-default);
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
  color: var(--brand-primary);
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
  background: var(--bg-surface-alt);
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border-default);
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
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.proceed-btn:hover {
  background: var(--brand-primary-hover);
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

@media (max-width: 768px) {
  .upload-view { max-width: 100%; }
  .report-type-section { flex-direction: column; align-items: stretch; }
  .report-type-select { min-width: 0; width: 100%; }
  .sheet { padding: 16px; }
  .proceed-btn { width: 100%; justify-content: center; }
}
</style>
