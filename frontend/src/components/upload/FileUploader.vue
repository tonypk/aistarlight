<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  uploaded: [file: File]
}>()

const dragOver = ref(false)
const selectedFile = ref<File | null>(null)

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) selectFile(file)
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) selectFile(file)
}

function selectFile(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['xlsx', 'xls', 'csv'].includes(ext || '')) {
    alert('Please upload .xlsx, .xls, or .csv files only')
    return
  }
  selectedFile.value = file
  emit('uploaded', file)
}
</script>

<template>
  <div
    class="uploader"
    :class="{ 'drag-over': dragOver }"
    @dragover.prevent="dragOver = true"
    @dragleave="dragOver = false"
    @drop.prevent="handleDrop"
  >
    <div class="upload-content">
      <p class="upload-icon">📄</p>
      <p v-if="!selectedFile">Drag & drop your Excel/CSV file here</p>
      <p v-else class="selected">{{ selectedFile.name }}</p>
      <label class="upload-btn">
        Browse Files
        <input type="file" accept=".xlsx,.xls,.csv" hidden @change="handleFileInput" />
      </label>
    </div>
  </div>
</template>

<style scoped>
.uploader {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
}
.uploader.drag-over {
  border-color: #4f46e5;
  background: #eef2ff;
}
.upload-icon { font-size: 48px; margin-bottom: 12px; }
.selected { color: #4f46e5; font-weight: 600; }
.upload-btn {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 24px;
  background: #4f46e5;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
}
.upload-btn:hover { background: #4338ca; }
</style>
