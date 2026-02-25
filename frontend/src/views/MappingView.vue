<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi } from '../api/data'
import { useUploadStore } from '../stores/upload'
import { TARGET_FIELDS, REPORT_TYPES } from '../config/targetFieldsByReportType'
import type { TargetField } from '../config/targetFieldsByReportType'

const router = useRouter()
const uploadStore = useUploadStore()

// --- State ---
const mappings = ref<Record<string, string>>({})
const aiLoading = ref(false)
const aiSuggested = ref(false)
const aiError = ref('')

// Phase 2: Confidence
const overallConfidence = ref(0)
const fieldConfidence = ref<Record<string, number>>({})
const unmappedColumns = ref<string[]>([])

// Phase 3: Template
const templateLoaded = ref(false)
const templateSaving = ref(false)

// Phase 4: Preview
const showPreview = ref(false)

// --- Computed ---
const currentTargetFields = computed<TargetField[]>(() => {
  const fields = TARGET_FIELDS[uploadStore.reportType] ?? TARGET_FIELDS.BIR_2550M
  return [...fields, { value: '_skip', label: '-- Skip --' }]
})

const currentReportLabel = computed(() => {
  return REPORT_TYPES.find(r => r.value === uploadStore.reportType)?.label ?? uploadStore.reportType
})

const confidenceBadge = computed(() => {
  const pct = Math.round(overallConfidence.value * 100)
  if (pct >= 85) return { label: `${pct}%`, cls: 'badge-green' }
  if (pct >= 60) return { label: `${pct}%`, cls: 'badge-yellow' }
  return { label: `${pct}%`, cls: 'badge-red' }
})

const previewRows = computed(() => {
  return uploadStore.sampleRows.slice(0, 5).map(row => {
    const out: Record<string, unknown> = {}
    for (const [src, target] of Object.entries(mappings.value)) {
      if (target && target !== '_skip' && target !== '') {
        out[target] = row[src]
      }
    }
    return out
  })
})

const previewColumns = computed(() => {
  const cols: string[] = []
  for (const [, target] of Object.entries(mappings.value)) {
    if (target && target !== '_skip' && target !== '' && !cols.includes(target)) {
      cols.push(target)
    }
  }
  return cols
})

// --- Lifecycle ---
onMounted(async () => {
  if (!uploadStore.hasFile) {
    router.push('/upload')
    return
  }
  // Initialize empty mappings (immutable)
  const init: Record<string, string> = {}
  for (const col of uploadStore.columns) {
    init[col] = ''
  }
  mappings.value = init
  // Phase 3: Try loading saved template
  await loadTemplate()
})

// --- Phase 3: Template ---
async function loadTemplate() {
  try {
    const res = await dataApi.getTemplate(uploadStore.reportType)
    const saved = res.data?.data?.column_mappings as Record<string, string> | undefined
    if (!saved || Object.keys(saved).length === 0) return

    // Match saved mappings to current columns (immutable)
    const applied = { ...mappings.value }
    let matched = 0
    for (const col of uploadStore.columns) {
      if (saved[col]) {
        applied[col] = saved[col]
        matched++
      }
    }
    if (matched > 0) {
      mappings.value = applied
      templateLoaded.value = true
    }
  } catch {
    // No saved template — that's fine
  }
}

async function saveTemplate() {
  templateSaving.value = true
  try {
    const toSave: Record<string, string> = {}
    for (const [col, target] of Object.entries(mappings.value)) {
      if (target && target !== '' && target !== '_skip') {
        toSave[col] = target
      }
    }
    await dataApi.saveTemplate(uploadStore.reportType, toSave)
  } catch {
    // Fire-and-forget — don't block the user
  } finally {
    templateSaving.value = false
  }
}

// --- Phase 1 + 2: AI Mapping ---
async function requestAiMapping() {
  aiLoading.value = true
  aiError.value = ''
  try {
    const res = await dataApi.suggestMapping({
      columns: uploadStore.columns,
      sample_rows: uploadStore.sampleRows as Record<string, unknown>[],
      report_type: uploadStore.reportType,
    })
    const data = res.data.data
    const suggested = data.mappings as Record<string, string>

    // Apply AI suggestions (immutable)
    const updated = { ...mappings.value }
    for (const [sourceCol, targetField] of Object.entries(suggested)) {
      if (sourceCol in updated) {
        updated[sourceCol] = targetField
      }
    }
    mappings.value = updated

    // Phase 2: Confidence data
    overallConfidence.value = typeof data.confidence === 'number' ? data.confidence : 0
    fieldConfidence.value = data.field_confidence ?? {}
    unmappedColumns.value = Array.isArray(data.unmapped) ? data.unmapped : []

    aiSuggested.value = true
    templateLoaded.value = false // AI overrides template
  } catch {
    aiError.value = 'AI mapping failed. Please map columns manually.'
  } finally {
    aiLoading.value = false
  }
}

// --- Phase 4: Preview + Confirm ---
function requestPreview() {
  // Validate at least one meaningful mapping
  let hasMeaningfulMapping = false
  for (const [, target] of Object.entries(mappings.value)) {
    if (target && target !== '' && target !== '_skip') {
      hasMeaningfulMapping = true
      break
    }
  }
  if (!hasMeaningfulMapping) {
    aiError.value = 'Please map at least one column to a target field.'
    return
  }
  aiError.value = ''
  showPreview.value = true
}

function backToEdit() {
  showPreview.value = false
}

function confirmMapping() {
  const finalMappings: Record<string, string> = {}
  for (const [col, target] of Object.entries(mappings.value)) {
    if (target && target !== '' && target !== '_skip') {
      finalMappings[col] = target
    }
  }
  uploadStore.setMappings(finalMappings)
  // Phase 3: Save template in background
  saveTemplate()
  router.push('/classification')
}

function getFieldConfidence(col: string): number | null {
  if (!aiSuggested.value) return null
  return fieldConfidence.value[col] ?? null
}

function isLowConfidence(col: string): boolean {
  const fc = getFieldConfidence(col)
  return fc !== null && fc < 0.6
}
</script>

<template>
  <div class="mapping-view">
    <h2>Column Mapping</h2>
    <p class="desc">
      Map your spreadsheet columns to
      <strong>{{ currentReportLabel }}</strong> fields
    </p>

    <div v-if="!uploadStore.hasFile" class="no-file">
      <p>No file uploaded. Please <router-link to="/upload">upload a file</router-link> first.</p>
    </div>

    <template v-else-if="!showPreview">
      <!-- File info -->
      <div class="file-info">
        File: <strong>{{ uploadStore.filename }}</strong>
        ({{ uploadStore.columns.length }} columns)
      </div>

      <!-- Template loaded hint -->
      <div v-if="templateLoaded" class="template-hint">
        Using saved mapping template. Click "Auto-Map with AI" to get fresh suggestions.
      </div>

      <!-- AI button + confidence badge -->
      <div class="ai-bar">
        <button
          class="ai-btn"
          @click="requestAiMapping"
          :disabled="aiLoading"
          data-testid="mapping-ai-btn"
        >
          {{ aiLoading ? 'AI is analyzing...' : aiSuggested ? 'Re-run AI Mapping' : 'Auto-Map with AI' }}
        </button>

        <span v-if="aiSuggested" class="confidence-badge" :class="confidenceBadge.cls" data-testid="mapping-confidence">
          Confidence: {{ confidenceBadge.label }}
        </span>
      </div>

      <p v-if="aiError" class="ai-error">{{ aiError }}</p>

      <!-- Mapping table -->
      <div class="mapping-table" :class="{ 'with-confidence': aiSuggested }">
        <div class="mapping-row header">
          <span>Your Column</span>
          <span>Sample Data</span>
          <span>Maps To</span>
          <span v-if="aiSuggested">Confidence</span>
        </div>
        <div
          v-for="col in uploadStore.columns"
          :key="col"
          class="mapping-row"
          :class="{ 'low-confidence': isLowConfidence(col) }"
        >
          <span class="source">{{ col }}</span>
          <span class="sample">{{ uploadStore.sampleRows[0]?.[col] ?? '—' }}</span>
          <select v-model="mappings[col]">
            <option value="">-- Select --</option>
            <option v-for="f in currentTargetFields" :key="f.value" :value="f.value">
              {{ f.label }}
            </option>
          </select>
          <span v-if="aiSuggested" class="conf-value">
            <template v-if="getFieldConfidence(col) !== null">
              {{ Math.round((getFieldConfidence(col) ?? 0) * 100) }}%
            </template>
            <template v-else>—</template>
          </span>
        </div>
      </div>

      <!-- Unmapped columns warning -->
      <div v-if="unmappedColumns.length > 0" class="unmapped-warning">
        <strong>Unmapped columns:</strong>
        {{ unmappedColumns.join(', ') }}
        <p class="unmapped-hint">These columns could not be automatically matched. Map them manually or skip them.</p>
      </div>

      <button class="confirm-btn" @click="requestPreview" data-testid="mapping-preview-btn">
        Preview Mapping
      </button>
    </template>

    <!-- Phase 4: Preview -->
    <template v-else>
      <div class="preview-section">
        <h3>Mapping Preview</h3>
        <p class="preview-desc">Review the first 5 rows with your mapping applied:</p>

        <div class="preview-table-wrap">
          <table class="preview-table">
            <thead>
              <tr>
                <th v-for="col in previewColumns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in previewRows" :key="i">
                <td v-for="col in previewColumns" :key="col">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="preview-actions">
          <button class="back-btn" @click="backToEdit">Back to Edit</button>
          <button class="confirm-btn" @click="confirmMapping" data-testid="mapping-confirm-btn">Confirm & Continue</button>
        </div>
      </div>
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

/* Template hint */
.template-hint {
  padding: 10px 16px;
  background: #ecfdf5;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #065f46;
  font-size: 14px;
}

/* AI bar */
.ai-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ai-btn {
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

/* Confidence badge */
.confidence-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-red { background: #fee2e2; color: #991b1b; }

.ai-error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

/* Mapping table */
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
/* When confidence column is shown */
.with-confidence .mapping-row {
  grid-template-columns: 1fr 1fr 1fr 80px;
}
.conf-value {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}
.source { font-weight: 500; }
.sample { color: #888; font-size: 13px; }
select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

/* Low confidence highlight */
.low-confidence {
  background: #fff7ed;
}

/* Unmapped warning */
.unmapped-warning {
  margin-top: 16px;
  padding: 12px 16px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
}
.unmapped-hint {
  margin: 4px 0 0;
  color: #a16207;
  font-size: 13px;
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

/* Preview */
.preview-section h3 { margin-bottom: 8px; }
.preview-desc {
  color: #6b7280;
  margin-bottom: 16px;
  font-size: 14px;
}
.preview-table-wrap { overflow-x: auto; }
.preview-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 13px;
}
.preview-table th {
  background: #f9fafb;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}
.preview-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
}
.preview-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
.back-btn {
  padding: 12px 32px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.back-btn:hover { background: #f9fafb; }
</style>
