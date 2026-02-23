<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi } from '../api/data'
import FileUploader from '../components/upload/FileUploader.vue'
import { useUploadStore } from '../stores/upload'

const router = useRouter()
const uploadStore = useUploadStore()
const uploading = ref(false)
const error = ref('')

async function handleFileUploaded(file: File) {
  uploading.value = true
  error.value = ''
  try {
    const res = await dataApi.upload(file)
    uploadStore.setUploadResult(res.data.data)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to upload file'
  } finally {
    uploading.value = false
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

    <FileUploader @uploaded="handleFileUploaded" />

    <div v-if="uploading" class="loading">Uploading and parsing file...</div>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="uploadStore.hasFile" class="preview-section">
      <div class="file-info">
        Uploaded: <strong>{{ uploadStore.filename }}</strong>
      </div>

      <div v-for="(sheet, name) in uploadStore.sheets" :key="name" class="sheet">
        <h3>Sheet: {{ name }} ({{ sheet.row_count }} rows)</h3>
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

      <button class="proceed-btn" @click="proceedToMapping">
        Proceed to Column Mapping
      </button>
    </div>
  </div>
</template>

<style scoped>
.upload-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 24px; }
.loading { text-align: center; padding: 24px; color: #4f46e5; }
.error { color: #ef4444; margin-top: 12px; }
.preview-section { margin-top: 24px; }
.file-info {
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #166534;
}
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
  padding: 12px 28px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  text-decoration: none;
}
.proceed-btn:hover { background: #4338ca; }
</style>
