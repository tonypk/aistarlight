<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi } from '../api/data'
import type { FieldCandidate, ConflictGroup, MappingCorrectionItem } from '../api/data'
import { useUploadStore } from '../stores/upload'
import { TARGET_FIELDS, REPORT_TYPES } from '../config/targetFieldsByReportType'
import type { TargetField } from '../config/targetFieldsByReportType'
import SearchableFieldSelect from '../components/SearchableFieldSelect.vue'
import DisambiguationPanel from '../components/DisambiguationPanel.vue'

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

// Preview
const showPreview = ref(false)

// Candidates & Conflicts (Phase 1 response)
const candidates = ref<Record<string, FieldCandidate[]>>({})
const conflicts = ref<ConflictGroup[]>([])

// Disambiguation (Phase 3)
const disambiguatingTarget = ref<string | null>(null)

// Correction tracking (Phase 4)
const aiOriginalMappings = ref<Record<string, string>>({})

// --- Computed ---
const currentTargetFields = computed<TargetField[]>(() => {
  return TARGET_FIELDS[uploadStore.reportType] ?? TARGET_FIELDS.BIR_2550M
})

const groupedTargetFields = computed(() => {
  const fields = currentTargetFields.value
  const groups: { label: string; fields: TargetField[] }[] = []
  const groupMap = new Map<string, TargetField[]>()

  for (const f of fields) {
    const g = f.group || 'Other'
    if (!groupMap.has(g)) {
      groupMap.set(g, [])
    }
    groupMap.get(g)!.push(f)
  }
  for (const [label, gFields] of groupMap) {
    groups.push({ label, fields: gFields })
  }
  return groups
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

// Phase 2C: Duplicate/conflict detection (computed)
const duplicateMappings = computed(() => {
  const counts: Record<string, string[]> = {}
  for (const [col, target] of Object.entries(mappings.value)) {
    if (target && target !== '_skip' && target !== '') {
      ;(counts[target] ??= []).push(col)
    }
  }
  return Object.fromEntries(Object.entries(counts).filter(([, c]) => c.length > 1))
})

const hasConflicts = computed(() => Object.keys(duplicateMappings.value).length > 0)

const conflictCount = computed(() => Object.keys(duplicateMappings.value).length)

// Used fields set (for SearchableFieldSelect)
const usedFieldsSet = computed(() => {
  const used = new Set<string>()
  for (const target of Object.values(mappings.value)) {
    if (target && target !== '' && target !== '_skip') {
      used.add(target)
    }
  }
  return used
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

// Disambiguation panel state
const disambiguationProps = computed(() => {
  const target = disambiguatingTarget.value
  if (!target) return null

  const competingCols = duplicateMappings.value[target] ?? []
  const targetField = currentTargetFields.value.find(f => f.value === target)

  return {
    targetField: target,
    targetLabel: targetField?.label ?? target,
    competingColumns: competingCols,
    sampleRows: uploadStore.sampleRows as Record<string, unknown>[],
    candidates: candidates.value,
    allTargetFields: currentTargetFields.value,
  }
})

// --- Lifecycle ---
onMounted(async () => {
  if (!uploadStore.hasFile) {
    router.push('/upload')
    return
  }
  const init: Record<string, string> = {}
  for (const col of uploadStore.columns) {
    init[col] = ''
  }
  mappings.value = init
  await loadTemplate()
})

// --- Template ---
async function loadTemplate() {
  try {
    const res = await dataApi.getTemplate(uploadStore.reportType)
    const saved = res.data?.data?.column_mappings as Record<string, string> | undefined
    if (!saved || Object.keys(saved).length === 0) return

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
    // No saved template
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
    // Fire-and-forget
  } finally {
    templateSaving.value = false
  }
}

// --- AI Mapping ---
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

    // Save original AI mappings for correction tracking
    aiOriginalMappings.value = { ...suggested }

    // Confidence data
    overallConfidence.value = typeof data.confidence === 'number' ? data.confidence : 0
    fieldConfidence.value = data.field_confidence ?? {}
    unmappedColumns.value = Array.isArray(data.unmapped) ? data.unmapped : []

    // Candidates & conflicts from backend
    candidates.value = data.candidates ?? {}
    conflicts.value = data.conflicts ?? []

    aiSuggested.value = true
    templateLoaded.value = false
  } catch {
    aiError.value = 'AI mapping failed. Please map columns manually.'
  } finally {
    aiLoading.value = false
  }
}

// --- Sample data helpers ---
function sampleTooltip(col: string): string {
  const rows = uploadStore.sampleRows.slice(0, 3)
  return rows
    .map((r, i) => `Row ${i + 1}: ${r[col] ?? '--'}`)
    .join('\n')
}

function sampleDisplay(col: string): string {
  return String(uploadStore.sampleRows[0]?.[col] ?? '\u2014')
}

function extraSampleCount(): number {
  return Math.min(uploadStore.sampleRows.length - 1, 2)
}

// --- Mapping update handler ---
function updateMapping(col: string, value: string) {
  mappings.value = { ...mappings.value, [col]: value }
}

// --- Conflict helpers ---
function isConflictColumn(col: string): boolean {
  const target = mappings.value[col]
  if (!target || target === '' || target === '_skip') return false
  return !!duplicateMappings.value[target]
}

function openDisambiguation(target: string) {
  disambiguatingTarget.value = target
}

function handleDisambiguationResolve(selectedCol: string) {
  const target = disambiguatingTarget.value
  if (!target) return

  // Keep the selected column mapped, clear others
  const updated = { ...mappings.value }
  for (const [col, t] of Object.entries(updated)) {
    if (t === target && col !== selectedCol) {
      updated[col] = ''
    }
  }
  mappings.value = updated
  disambiguatingTarget.value = null
}

// --- Confidence ---
function getFieldConfidence(col: string): number | null {
  if (!aiSuggested.value) return null
  return fieldConfidence.value[col] ?? null
}

function isLowConfidence(col: string): boolean {
  const fc = getFieldConfidence(col)
  return fc !== null && fc < 0.6
}

// --- Preview + Confirm ---
function requestPreview() {
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

  // Save template in background
  saveTemplate()

  // Phase 4: Record corrections (fire-and-forget)
  recordCorrections(finalMappings)

  router.push('/classification')
}

// Phase 4: Track and send corrections
function recordCorrections(finalMappings: Record<string, string>) {
  if (Object.keys(aiOriginalMappings.value).length === 0) return

  const corrections: MappingCorrectionItem[] = []
  for (const [col, newTarget] of Object.entries(finalMappings)) {
    const oldTarget = aiOriginalMappings.value[col] ?? ''
    if (oldTarget !== newTarget && (oldTarget !== '' || newTarget !== '')) {
      const sampleValues = uploadStore.sampleRows
        .slice(0, 3)
        .map(r => r[col])
        .filter(v => v != null)
      corrections.push({
        column_name: col,
        old_target: oldTarget,
        new_target: newTarget,
        sample_values: sampleValues as unknown[],
      })
    }
  }

  // Also check columns that AI mapped but user removed
  for (const [col, oldTarget] of Object.entries(aiOriginalMappings.value)) {
    if (oldTarget && !finalMappings[col]) {
      corrections.push({
        column_name: col,
        old_target: oldTarget,
        new_target: '_skip',
      })
    }
  }

  if (corrections.length > 0) {
    dataApi.recordMappingCorrections(uploadStore.reportType, corrections).catch(() => {
      // Fire-and-forget
    })
  }
}

function getFieldLabel(target: string): string {
  const f = currentTargetFields.value.find(t => t.value === target)
  return f?.label ?? target
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

      <!-- Conflict banner -->
      <div v-if="hasConflicts" class="conflict-banner">
        <strong>{{ conflictCount }} conflict(s) detected:</strong>
        Multiple columns are mapped to the same target field.
        <div class="conflict-list">
          <span
            v-for="(cols, target) in duplicateMappings"
            :key="String(target)"
            class="conflict-item"
          >
            <strong>{{ getFieldLabel(String(target)) }}</strong>
            ({{ cols.join(', ') }})
            <button class="resolve-btn" @click="openDisambiguation(String(target))">Resolve</button>
          </span>
        </div>
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
          :class="{
            'low-confidence': isLowConfidence(col),
            'conflict-row': isConflictColumn(col),
          }"
        >
          <span class="source">{{ col }}</span>
          <span class="sample" :title="sampleTooltip(col)">
            {{ sampleDisplay(col) }}
            <small v-if="uploadStore.sampleRows.length > 1" class="more">
              +{{ extraSampleCount() }}
            </small>
          </span>
          <SearchableFieldSelect
            :modelValue="mappings[col] ?? ''"
            @update:modelValue="updateMapping(col, $event)"
            :groups="groupedTargetFields"
            :usedFields="usedFieldsSet"
            :candidates="candidates[col]"
            :isConflict="isConflictColumn(col)"
          />
          <span v-if="aiSuggested" class="conf-value">
            <template v-if="getFieldConfidence(col) !== null">
              {{ Math.round((getFieldConfidence(col) ?? 0) * 100) }}%
            </template>
            <template v-else>--</template>
          </span>
        </div>
      </div>

      <!-- Unmapped columns warning -->
      <div v-if="unmappedColumns.length > 0" class="unmapped-warning">
        <strong>Unmapped columns:</strong>
        {{ unmappedColumns.join(', ') }}
        <p class="unmapped-hint">These columns could not be automatically matched. Map them manually or skip them.</p>
      </div>

      <button
        class="confirm-btn"
        @click="requestPreview"
        data-testid="mapping-preview-btn"
        :disabled="hasConflicts"
        :title="hasConflicts ? 'Resolve all conflicts before proceeding' : ''"
      >
        {{ hasConflicts ? `Resolve ${conflictCount} Conflict(s) First` : 'Preview Mapping' }}
      </button>
    </template>

    <!-- Preview -->
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

    <!-- Disambiguation Panel -->
    <DisambiguationPanel
      v-if="disambiguationProps"
      v-bind="disambiguationProps"
      @resolve="handleDisambiguationResolve"
      @close="disambiguatingTarget = null"
    />
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

/* Conflict banner */
.conflict-banner {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #991b1b;
  font-size: 14px;
}
.conflict-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.conflict-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fee2e2;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
}
.resolve-btn {
  padding: 2px 8px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.resolve-btn:hover {
  background: #dc2626;
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
.sample {
  color: #888;
  font-size: 13px;
  cursor: help;
}
.sample .more {
  color: #a1a1aa;
  margin-left: 4px;
  font-size: 11px;
}

/* Low confidence highlight */
.low-confidence {
  background: #fff7ed;
}

/* Conflict row highlight */
.conflict-row {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
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
.confirm-btn:disabled {
  background: #9ca3af;
  cursor: default;
}

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
