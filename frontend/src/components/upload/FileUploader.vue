<script setup lang="ts">
import { ref, computed } from 'vue'

// Large files are handled by browser-side SheetJS parsing, so the limit is generous.
const MAX_FILE_SIZE_MB = 200
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
const ALLOWED_EXTENSIONS = ['xlsx', 'xls', 'csv']

const emit = defineEmits<{
  uploaded: [file: File]
}>()

const dragOver = ref(false)
const selectedFile = ref<File | null>(null)
const validationError = ref('')

const fileInfo = computed(() => {
  if (!selectedFile.value) return null
  const f = selectedFile.value
  return {
    name: f.name,
    size: formatSize(f.size),
    ext: f.name.split('.').pop()?.toUpperCase() || '',
  }
})

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) selectFile(file)
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) selectFile(file)
  // Reset so the same file can be re-selected
  target.value = ''
}

function selectFile(file: File) {
  validationError.value = ''
  selectedFile.value = null

  // Validate extension
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    validationError.value = `Unsupported format: .${ext}. Only .xlsx, .xls, .csv files are accepted.`
    return
  }

  // Validate file size
  if (file.size > MAX_FILE_SIZE) {
    validationError.value = `File too large: ${formatSize(file.size)}. Maximum allowed: ${MAX_FILE_SIZE_MB}MB. Please reduce file size or split into multiple files.`
    return
  }

  // Validate not empty
  if (file.size === 0) {
    validationError.value = 'File is empty. Please select a file with data.'
    return
  }

  selectedFile.value = file
  emit('uploaded', file)
}

function clearFile() {
  selectedFile.value = null
  validationError.value = ''
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

defineExpose({ clearFile })
</script>

<template>
  <div class="uploader-wrapper">
    <div
      class="uploader"
      :class="{ 'drag-over': dragOver, 'has-error': !!validationError }"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="handleDrop"
      data-testid="file-dropzone"
    >
      <div class="upload-content">
        <!-- No file selected -->
        <template v-if="!selectedFile">
          <div class="upload-icon-wrap">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 16V4m0 0L8 8m4-4l4 4" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="upload-title">Drag & drop your Excel/CSV file here</p>
          <p class="upload-hint">Supports .xlsx, .xls, .csv — large files are automatically optimized</p>
          <label class="upload-btn">
            Browse Files
            <input type="file" accept=".xlsx,.xls,.csv" hidden @change="handleFileInput" data-testid="file-input" />
          </label>
        </template>

        <!-- File selected -->
        <template v-else>
          <div class="file-selected">
            <div class="file-badge">
              <span class="file-ext">{{ fileInfo?.ext }}</span>
            </div>
            <div class="file-details">
              <span class="file-name" data-testid="file-name">{{ fileInfo?.name }}</span>
              <span class="file-size">{{ fileInfo?.size }}</span>
            </div>
            <button class="file-change" @click.stop="clearFile">
              Change File
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Inline validation error -->
    <Transition name="slide">
      <div v-if="validationError" class="validation-error" data-testid="file-validation-error">
        <svg class="error-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>
        <span>{{ validationError }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.uploader-wrapper {
  width: 100%;
}

.uploader {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 40px 24px;
  text-align: center;
  transition: all 0.2s ease;
  cursor: pointer;
  background: #fafafa;
}
.uploader:hover {
  border-color: #a5b4fc;
  background: #f5f3ff;
}
.uploader.drag-over {
  border-color: #4f46e5;
  background: #eef2ff;
  transform: scale(1.01);
}
.uploader.has-error {
  border-color: #fca5a5;
  background: #fef2f2;
}

.upload-icon-wrap {
  margin-bottom: 12px;
}
.upload-icon {
  width: 48px;
  height: 48px;
  color: #9ca3af;
  margin: 0 auto;
}
.uploader:hover .upload-icon,
.uploader.drag-over .upload-icon {
  color: #4f46e5;
}

.upload-title {
  font-size: 16px;
  font-weight: 500;
  color: #374151;
  margin: 0 0 4px 0;
}
.upload-hint {
  font-size: 13px;
  color: #9ca3af;
  margin: 0 0 16px 0;
}

.upload-btn {
  display: inline-block;
  padding: 8px 24px;
  background: #4f46e5;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.15s;
}
.upload-btn:hover { background: #4338ca; }

/* File selected state */
.file-selected {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}
.file-badge {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.file-ext {
  font-size: 11px;
  font-weight: 700;
  color: #4f46e5;
  text-transform: uppercase;
}
.file-details {
  flex: 1;
  text-align: left;
  min-width: 0;
}
.file-name {
  display: block;
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: 12px;
  color: #9ca3af;
}
.file-change {
  padding: 6px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.file-change:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* Validation error */
.validation-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 10px;
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
  line-height: 1.4;
}
.error-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
