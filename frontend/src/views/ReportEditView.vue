<script setup lang="ts">
import { computed, onMounted, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuditTrail from '../components/report/AuditTrail.vue'
import { useReportStore } from '../stores/report'

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()
const reportId = route.params.id as string

const saving = ref(false)
const error = ref('')
const recalculate = ref(true)
const notes = ref('')

// Editable fields state — populated from report data
const editableFields = reactive<Record<string, string>>({})
const originalFields = ref<Record<string, string>>({})

// BIR 2550M field definitions
const sections = [
  {
    name: 'Part II - Sales / Receipts',
    fields: [
      { key: 'line_1_vatable_sales', line: '1', label: 'Vatable Sales / Receipts', editable: true },
      { key: 'line_2_sales_to_government', line: '2', label: 'Sales to Government (5% VAT)', editable: true },
      { key: 'line_3_zero_rated_sales', line: '3', label: 'Zero-Rated Sales', editable: true },
      { key: 'line_4_exempt_sales', line: '4', label: 'Exempt Sales', editable: true },
      { key: 'line_5_total_sales', line: '5', label: 'Total Sales (Lines 1-4)', editable: false },
    ],
  },
  {
    name: 'Part III - Output Tax',
    fields: [
      { key: 'line_6_output_vat', line: '6', label: 'Output VAT (Line 1 x 12%)', editable: false },
      { key: 'line_6a_output_vat_government', line: '6A', label: 'Output VAT Government (Line 2 x 5%)', editable: false },
      { key: 'line_6b_total_output_vat', line: '6B', label: 'Total Output Tax', editable: false },
    ],
  },
  {
    name: 'Part IV - Allowable Input Tax',
    fields: [
      { key: 'line_7_input_vat_goods', line: '7', label: 'Input VAT - Goods', editable: true },
      { key: 'line_8_input_vat_capital', line: '8', label: 'Input VAT - Capital Goods', editable: true },
      { key: 'line_9_input_vat_services', line: '9', label: 'Input VAT - Services', editable: true },
      { key: 'line_10_input_vat_imports', line: '10', label: 'Input VAT - Imports', editable: true },
      { key: 'line_11_total_input_vat', line: '11', label: 'Total Input Tax (Lines 7-10)', editable: false },
    ],
  },
  {
    name: 'Part V - Tax Due',
    fields: [
      { key: 'line_12_vat_payable', line: '12', label: 'VAT Payable (6B - 11)', editable: false },
      { key: 'line_13_less_tax_credits', line: '13', label: 'Less: Tax Credits', editable: true },
      { key: 'line_14_net_vat_payable', line: '14', label: 'Net VAT Payable', editable: false },
      { key: 'line_15_add_penalties', line: '15', label: 'Add: Penalties', editable: true },
      { key: 'line_16_total_amount_due', line: '16', label: 'TOTAL AMOUNT DUE', editable: false },
    ],
  },
]

onMounted(async () => {
  const report = await reportStore.fetchReport(reportId)
  const data = (report.calculated_data || {}) as Record<string, string>
  for (const section of sections) {
    for (const field of section.fields) {
      editableFields[field.key] = data[field.key] || '0'
    }
  }
  originalFields.value = { ...editableFields }
})

const changedFields = computed(() => {
  const changes: Record<string, string> = {}
  for (const key of Object.keys(editableFields)) {
    if (editableFields[key] !== originalFields.value[key]) {
      changes[key] = editableFields[key]
    }
  }
  return changes
})

const hasChanges = computed(() => Object.keys(changedFields.value).length > 0)

const reportVersion = computed(() => {
  return (reportStore.currentReport?.version as number) || 1
})

function formatAmount(val: string): string {
  try {
    const num = parseFloat(val)
    return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  } catch {
    return val
  }
}

function isModified(key: string): boolean {
  return editableFields[key] !== originalFields.value[key]
}

function isOverridden(key: string): boolean {
  const overrides = reportStore.currentReport?.overrides as Record<string, string> | null
  return overrides ? key in overrides : false
}

async function handleSave() {
  if (!hasChanges.value) return
  saving.value = true
  error.value = ''
  try {
    await reportStore.editReport(reportId, {
      field_overrides: changedFields.value,
      recalculate: recalculate.value,
      notes: notes.value || undefined,
      version: reportVersion.value,
    })
    // Refresh field values from updated report
    const data = (reportStore.currentReport?.calculated_data || {}) as Record<string, string>
    for (const key of Object.keys(editableFields)) {
      editableFields[key] = data[key] || '0'
    }
    originalFields.value = { ...editableFields }
    notes.value = ''
    // Refresh audit logs
    reportStore.fetchAuditLogs(reportId)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to save changes'
  } finally {
    saving.value = false
  }
}

function handleBack() {
  router.push('/reports')
}
</script>

<template>
  <div class="edit-view">
    <div class="header-row">
      <button class="back-btn" @click="handleBack">&larr; Back to Reports</button>
      <h2>Edit Report</h2>
      <div class="version-badge">v{{ reportVersion }}</div>
    </div>

    <div v-if="reportStore.currentReport" class="edit-card">
      <div class="report-meta">
        <span><strong>Type:</strong> {{ reportStore.currentReport.report_type }}</span>
        <span><strong>Period:</strong> {{ reportStore.currentReport.period }}</span>
        <span><strong>Status:</strong>
          <span class="badge" :class="reportStore.currentReport.status as string">
            {{ reportStore.currentReport.status }}
          </span>
        </span>
      </div>

      <div class="options-row">
        <label class="toggle">
          <input type="checkbox" v-model="recalculate" />
          Auto-recalculate dependent fields
        </label>
      </div>

      <div v-for="section in sections" :key="section.name" class="section">
        <div class="section-header">{{ section.name }}</div>
        <div
          v-for="field in section.fields"
          :key="field.key"
          class="field-row"
          :class="{
            modified: isModified(field.key),
            overridden: isOverridden(field.key),
            computed: !field.editable,
          }"
        >
          <span class="line-no">{{ field.line }}</span>
          <span class="label">{{ field.label }}</span>
          <div class="value-cell">
            <template v-if="field.editable">
              <input
                type="text"
                v-model="editableFields[field.key]"
                class="field-input"
                :class="{ changed: isModified(field.key) }"
              />
            </template>
            <template v-else>
              <span class="computed-value">PHP {{ formatAmount(editableFields[field.key]) }}</span>
            </template>
          </div>
          <span v-if="isModified(field.key)" class="change-indicator" title="Modified">*</span>
          <span v-if="isOverridden(field.key) && !isModified(field.key)" class="override-indicator" title="Previously overridden">!</span>
        </div>
      </div>

      <!-- Change summary -->
      <div v-if="hasChanges" class="diff-preview">
        <h4>Pending Changes</h4>
        <div v-for="(newVal, key) in changedFields" :key="key" class="diff-item">
          <span class="diff-field">{{ key }}:</span>
          <span class="diff-old">{{ originalFields[key] }}</span>
          <span class="diff-arrow">&rarr;</span>
          <span class="diff-new">{{ newVal }}</span>
        </div>
      </div>

      <div class="notes-row">
        <label>Notes (optional):</label>
        <input type="text" v-model="notes" placeholder="Reason for changes..." class="notes-input" />
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button class="save-btn" @click="handleSave" :disabled="!hasChanges || saving">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
        <button class="cancel-btn" @click="handleBack">Cancel</button>
      </div>
    </div>

    <AuditTrail :report-id="reportId" />
  </div>
</template>

<style scoped>
.edit-view { max-width: 900px; margin: 0 auto; }
.header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.back-btn {
  padding: 6px 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.version-badge {
  margin-left: auto;
  padding: 4px 10px;
  background: #f0f4ff;
  border: 1px solid #c7d2fe;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #4f46e5;
}
.edit-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}
.report-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  font-size: 14px;
}
.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.badge.draft { background: #fef3c7; color: #92400e; }
.badge.review { background: #dbeafe; color: #1e40af; }
.badge.rejected { background: #fee2e2; color: #991b1b; }
.options-row {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
}
.toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
}
.section { margin-bottom: 16px; }
.section-header {
  background: #f1f5f9;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #475569;
  border-radius: 6px;
  margin-bottom: 4px;
}
.field-row {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid #f3f4f6;
  gap: 8px;
}
.field-row.modified { background: #fef3c7; }
.field-row.overridden { border-left: 3px solid #f59e0b; }
.field-row.computed { background: #f8fafc; }
.line-no { width: 30px; color: #94a3b8; font-weight: 500; font-size: 13px; }
.label { flex: 1; font-size: 13px; color: #555; }
.value-cell { width: 180px; text-align: right; }
.field-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  text-align: right;
  font-family: monospace;
  font-size: 13px;
}
.field-input.changed {
  border-color: #f59e0b;
  background: #fffbeb;
}
.computed-value {
  font-family: monospace;
  font-size: 13px;
  color: #6b7280;
}
.change-indicator { color: #f59e0b; font-weight: 700; font-size: 16px; }
.override-indicator { color: #3b82f6; font-weight: 700; font-size: 14px; }
.diff-preview {
  margin-top: 16px;
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}
.diff-preview h4 { margin-bottom: 8px; font-size: 13px; color: #92400e; }
.diff-item { font-size: 12px; padding: 2px 0; display: flex; gap: 6px; align-items: center; }
.diff-field { font-weight: 500; color: #6b7280; }
.diff-old { color: #ef4444; text-decoration: line-through; }
.diff-arrow { color: #94a3b8; }
.diff-new { color: #22c55e; font-weight: 500; }
.notes-row {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.notes-row label { font-size: 13px; font-weight: 500; white-space: nowrap; }
.notes-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
}
.error { color: #ef4444; margin-top: 12px; font-size: 13px; }
.actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
.save-btn {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}
.save-btn:hover { background: #4338ca; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn {
  padding: 10px 24px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
}
</style>
