<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { formsApi, type FormSection } from '../../api/forms'

const props = defineProps<{
  data: Record<string, string> | null
  reportType: string
  status?: string
  formType?: string // e.g. "BIR_2550M" — used to fetch schema
}>()

// Schema-driven sections (loaded from API)
const schemaSections = ref<FormSection[]>([])
const schemaLoaded = ref(false)

// Total field IDs from schema (editable=false and line includes "total" or is a summary line)
const totalFieldIds = ref<Set<string>>(new Set())

async function loadSchema(formType: string) {
  try {
    const res = await formsApi.getSchema(formType)
    const schema = res.data.data
    schemaSections.value = schema.schema_def.sections
    schemaLoaded.value = true

    // Build set of total/computed fields
    const totals = new Set<string>()
    for (const section of schemaSections.value) {
      for (const field of section.fields) {
        if (!field.editable) {
          totals.add(field.id)
        }
      }
    }
    totalFieldIds.value = totals
  } catch {
    schemaLoaded.value = false
  }
}

onMounted(() => {
  if (props.formType) {
    loadSchema(props.formType)
  }
})

watch(() => props.formType, (newType) => {
  if (newType) loadSchema(newType)
})

// Fallback: infer sections from data keys (for reports without schema)
interface LineItem {
  key: string
  lineNo: string
  label: string
  value: string
}

const fallbackSections = computed(() => {
  if (!props.data || schemaLoaded.value) return []

  const sectionDefs = [
    { prefix: 'line_1_', section: 'Sales / Receipts', through: 'line_5_' },
    { prefix: 'line_6', section: 'Output Tax', through: 'line_6b_' },
    { prefix: 'line_7_', section: 'Allowable Input Tax', through: 'line_11_' },
    { prefix: 'line_12_', section: 'Tax Due', through: 'line_16_' },
  ]

  const items: (LineItem & { section: string })[] = []
  for (const [key, value] of Object.entries(props.data)) {
    if (!key.startsWith('line_')) continue
    const parts = key.split('_')
    const lineNo = (parts[1] || '').toUpperCase()
    const label = parts.slice(2).join(' ')

    let section = 'Other'
    for (const sd of sectionDefs) {
      const num = parseInt(parts[1])
      const sdStart = parseInt(sd.prefix.split('_')[1])
      const sdEnd = parseInt(sd.through.split('_')[1])
      if (num >= sdStart && num <= sdEnd) {
        section = sd.section
        break
      }
    }
    items.push({ key, lineNo, label, value, section })
  }

  const grouped: { name: string; items: LineItem[] }[] = []
  let currentSection = ''
  for (const item of items) {
    if (item.section !== currentSection) {
      currentSection = item.section
      grouped.push({ name: currentSection, items: [] })
    }
    grouped[grouped.length - 1].items.push(item)
  }
  return grouped
})

const workflowSteps = ['draft', 'review', 'approved', 'filed', 'archived']

const currentStepIndex = computed(() => {
  if (!props.status) return -1
  if (props.status === 'rejected') return 0
  return workflowSteps.indexOf(props.status)
})

const taxCredit = computed(() => props.data?.tax_credit_carried_forward || '0')

function formatAmount(val: string): string {
  try {
    const num = parseFloat(val)
    return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  } catch {
    return val
  }
}

function isTotalField(fieldId: string): boolean {
  if (totalFieldIds.value.size > 0) {
    return totalFieldIds.value.has(fieldId)
  }
  // Fallback heuristic
  return fieldId.includes('total') || fieldId.includes('line_16') || fieldId.includes('line_5_') || fieldId.includes('line_6b_') || fieldId.includes('line_11_')
}

function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    draft: 'badge-draft',
    review: 'badge-review',
    approved: 'badge-approved',
    rejected: 'badge-rejected',
    filed: 'badge-filed',
    archived: 'badge-archived',
  }
  return map[status] || 'badge-draft'
}
</script>

<template>
  <div class="preview" v-if="data">
    <div class="preview-header">
      <h3>{{ reportType }} Preview</h3>
      <span v-if="status" class="status-badge" :class="statusBadgeClass(status)">{{ status }}</span>
    </div>

    <!-- Workflow progress bar -->
    <div v-if="status" class="workflow-progress">
      <div
        v-for="(step, idx) in workflowSteps"
        :key="step"
        class="progress-step"
        :class="{
          active: idx === currentStepIndex,
          done: idx < currentStepIndex,
        }"
      >
        <div class="step-dot"></div>
        <span class="step-label">{{ step }}</span>
      </div>
    </div>

    <!-- Schema-driven rendering -->
    <template v-if="schemaLoaded">
      <div v-for="section in schemaSections" :key="section.id" class="section">
        <div class="section-header">{{ section.name }}</div>
        <table>
          <tbody>
            <tr
              v-for="field in section.fields"
              :key="field.id"
              :class="{ total: isTotalField(field.id) }"
            >
              <td class="line-no">{{ field.line }}</td>
              <td class="label">{{ field.label }}</td>
              <td class="value">PHP {{ formatAmount(data[field.id] || '0') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Fallback rendering (no schema) -->
    <template v-else>
      <div v-for="section in fallbackSections" :key="section.name" class="section">
        <div class="section-header">{{ section.name }}</div>
        <table>
          <tbody>
            <tr v-for="item in section.items" :key="item.key" :class="{ total: isTotalField(item.key) }">
              <td class="line-no">{{ item.lineNo }}</td>
              <td class="label">{{ item.label }}</td>
              <td class="value">PHP {{ formatAmount(item.value) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="parseFloat(taxCredit) > 0" class="credit-note">
      Excess Input VAT / Tax Credit Carried Forward: PHP {{ formatAmount(taxCredit) }}
    </div>
  </div>
</template>

<style scoped>
.preview {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
h3 { margin: 0; }
.status-badge {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-draft { background: #fef3c7; color: #92400e; }
.badge-review { background: #dbeafe; color: #1e40af; }
.badge-approved { background: #d1fae5; color: #065f46; }
.badge-rejected { background: #fee2e2; color: #991b1b; }
.badge-filed { background: #ede9fe; color: #5b21b6; }
.badge-archived { background: #f3f4f6; color: #6b7280; }

.workflow-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 12px 0;
  position: relative;
}
.workflow-progress::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 10%;
  right: 10%;
  height: 2px;
  background: #e5e7eb;
}
.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
  z-index: 1;
}
.step-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #e5e7eb;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #e5e7eb;
}
.progress-step.done .step-dot { background: #22c55e; box-shadow: 0 0 0 2px #22c55e; }
.progress-step.active .step-dot { background: #3b82f6; box-shadow: 0 0 0 2px #3b82f6; }
.step-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: capitalize;
}
.progress-step.done .step-label { color: #22c55e; }
.progress-step.active .step-label { color: #3b82f6; font-weight: 600; }

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
table { width: 100%; }
td { padding: 6px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.line-no { width: 40px; color: #94a3b8; font-weight: 500; }
.label { color: #555; }
.value { text-align: right; font-family: monospace; white-space: nowrap; }
tr.total { background: #f8fafc; }
tr.total .label, tr.total .value { font-weight: 700; }
.credit-note {
  margin-top: 12px;
  padding: 8px 12px;
  background: #fef3c7;
  border-radius: 6px;
  font-size: 13px;
  color: #92400e;
}
</style>
