<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi } from '../api/data'
import { useUploadStore } from '../stores/upload'

const router = useRouter()
const uploadStore = useUploadStore()
const mappings = ref<Record<string, string>>({})
const aiLoading = ref(false)
const aiSuggested = ref(false)
const aiError = ref('')

const targetFields = [
  { value: 'date', label: 'Date' },
  { value: 'description', label: 'Description' },
  { value: 'amount', label: 'Amount' },
  { value: 'vat_amount', label: 'VAT Amount' },
  { value: 'vat_type', label: 'VAT Type (vatable/exempt/zero_rated/government)' },
  { value: 'category', label: 'Category (goods/services/capital/imports)' },
  { value: 'tin', label: 'TIN' },
  { value: '_skip', label: '-- Skip --' },
]

onMounted(() => {
  if (!uploadStore.hasFile) {
    router.push('/upload')
    return
  }
  // Initialize empty mappings
  for (const col of uploadStore.columns) {
    mappings.value[col] = ''
  }
})

async function requestAiMapping() {
  aiLoading.value = true
  try {
    const res = await dataApi.suggestMapping({
      columns: uploadStore.columns,
      sample_rows: uploadStore.sampleRows as Record<string, unknown>[],
      report_type: 'BIR_2550M',
    })
    const suggested = res.data.data.mappings as Record<string, string>
    // Apply AI suggestions
    for (const [sourceCol, targetField] of Object.entries(suggested)) {
      if (sourceCol in mappings.value) {
        mappings.value[sourceCol] = targetField
      }
    }
    aiSuggested.value = true
  } catch {
    aiError.value = 'AI mapping failed. Please map columns manually.'
  } finally {
    aiLoading.value = false
  }
}

function confirmMapping() {
  // Keep all mapped columns (including _skip), filter out unselected ones
  const finalMappings: Record<string, string> = {}
  let hasMeaningfulMapping = false
  for (const [col, target] of Object.entries(mappings.value)) {
    if (target && target !== '') {
      finalMappings[col] = target
      if (target !== '_skip') hasMeaningfulMapping = true
    }
  }
  if (!hasMeaningfulMapping) {
    aiError.value = 'Please map at least one column to a target field.'
    return
  }
  uploadStore.setMappings(finalMappings)
  router.push('/classification')
}
</script>

<template>
  <div class="mapping-view">
    <h2>Column Mapping</h2>
    <p class="desc">Map your spreadsheet columns to BIR form fields</p>

    <div v-if="!uploadStore.hasFile" class="no-file">
      <p>No file uploaded. Please <router-link to="/upload">upload a file</router-link> first.</p>
    </div>

    <template v-else>
      <div class="file-info">
        File: <strong>{{ uploadStore.filename }}</strong>
        ({{ uploadStore.columns.length }} columns)
      </div>

      <button
        class="ai-btn"
        @click="requestAiMapping"
        :disabled="aiLoading"
      >
        {{ aiLoading ? 'AI is analyzing...' : aiSuggested ? 'Re-run AI Mapping' : 'Auto-Map with AI' }}
      </button>
      <p v-if="aiError" class="ai-error">{{ aiError }}</p>

      <div class="mapping-table">
        <div class="mapping-row header">
          <span>Your Column</span>
          <span>Sample Data</span>
          <span>Maps To</span>
        </div>
        <div v-for="col in uploadStore.columns" :key="col" class="mapping-row">
          <span class="source">{{ col }}</span>
          <span class="sample">{{ uploadStore.sampleRows[0]?.[col] ?? '—' }}</span>
          <select v-model="mappings[col]">
            <option value="">-- Select --</option>
            <option v-for="f in targetFields" :key="f.value" :value="f.value">
              {{ f.label }}
            </option>
          </select>
        </div>
      </div>

      <button class="confirm-btn" @click="confirmMapping">
        Confirm Mapping & Generate Report
      </button>
    </template>
  </div>
</template>

<style scoped>
.mapping-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 24px; }
.no-file { text-align: center; padding: 48px; color: #888; }
.no-file a { color: #4f46e5; }
.file-info {
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #166534;
}
.ai-btn {
  margin-bottom: 16px;
  padding: 10px 24px;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.ai-btn:hover { background: #6d28d9; }
.ai-btn:disabled { opacity: 0.6; cursor: default; }
.ai-error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }
.mapping-table {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
.mapping-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  padding: 12px 20px;
  border-bottom: 1px solid #f3f4f6;
  align-items: center;
}
.mapping-row.header {
  background: #f9fafb;
  font-weight: 600;
  font-size: 13px;
  color: #888;
}
.source { font-weight: 500; }
.sample { color: #888; font-size: 13px; }
select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.confirm-btn {
  margin-top: 24px;
  padding: 12px 32px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.confirm-btn:hover { background: #4338ca; }
</style>
