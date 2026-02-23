<script setup lang="ts">
import { ref } from 'vue'
import { client } from '../api/client'
import FileUploader from '../components/upload/FileUploader.vue'

interface SheetData {
  columns: string[]
  row_count: number
  preview: Record<string, unknown>[]
}

const preview = ref<Record<string, SheetData> | null>(null)
const uploading = ref(false)
const error = ref('')

async function handleFileUploaded(file: File) {
  uploading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await client.post('/data/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    preview.value = res.data.data.sheets
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to parse file'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="upload-view">
    <h2>Upload Financial Data</h2>
    <p class="desc">Upload your sales and purchase records (Excel or CSV)</p>

    <FileUploader @uploaded="handleFileUploaded" />

    <div v-if="uploading" class="loading">Parsing file...</div>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="preview" class="preview-section">
      <div v-for="(sheet, name) in preview" :key="name" class="sheet">
        <h3>Sheet: {{ name }} ({{ sheet.row_count }} rows)</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th v-for="col in sheet.columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in sheet.preview" :key="i">
                <td v-for="col in sheet.columns" :key="col">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <router-link to="/mapping" class="proceed-btn">Proceed to Mapping</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 24px; }
.loading { text-align: center; padding: 24px; color: #4f46e5; }
.error { color: #ef4444; margin-top: 12px; }
.preview-section { margin-top: 24px; }
.sheet {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}
.sheet h3 { margin-bottom: 16px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f9fafb; padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px; border-bottom: 1px solid #f3f4f6; }
.proceed-btn {
  display: inline-block;
  margin-top: 16px;
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
}
</style>
