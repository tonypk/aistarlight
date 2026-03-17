<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { taxBridgeApi, taxExportApi } from '../api/accounting'
import { reportsApi } from '../api/reports'
import { complianceApi } from '../api/compliance'
import { client } from '../api/client'
import type { FormSummary } from '../api/forms'

// Wizard step
const step = ref(1)
const loading = ref(false)
const error = ref('')

// Step 1: Period & Form
const formType = ref('BIR_2550M')
const periodStart = ref('')
const periodEnd = ref('')
const availableForms = ref<FormSummary[]>([])
const recommendedForms = ref<{ form_type: string; name: string; frequency: string; required: boolean; reason: string; deadline_day?: number }[]>([])

// Step 2: GL Calculation
const taxResult = ref<{ form_type: string; period_start: string; period_end: string; result: Record<string, string> } | null>(null)

// Step 3: Report
const reportId = ref('')
const report = ref<any>(null)

// Step 4: Compliance
const validation = ref<{ overall_score: number; check_results: any[]; rag_findings: any[] } | null>(null)

// Initialize
onMounted(async () => {
  try {
    const [formsRes, recoRes] = await Promise.all([
      client.get('/forms'),
      client.get('/forms/recommended'),
    ])
    availableForms.value = formsRes.data?.data || []
    recommendedForms.value = recoRes.data?.data || []
  } catch {
    // Non-critical, continue with defaults
  }
  // Default to current month
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  periodStart.value = `${y}-${m}-01`
  const lastDay = new Date(y, now.getMonth() + 1, 0).getDate()
  periodEnd.value = `${y}-${m}-${String(lastDay).padStart(2, '0')}`
})

const periodLabel = computed(() => {
  if (!periodStart.value) return ''
  const d = new Date(periodStart.value)
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
})

const formLabel = computed(() => {
  const found = availableForms.value.find(f => f.form_type === formType.value)
  return found?.name || formType.value.replace(/_/g, ' ')
})

const resultEntries = computed(() => {
  if (!taxResult.value?.result) return []
  return Object.entries(taxResult.value.result)
    .filter(([k]) => k !== 'gl_source')
    .map(([key, value]) => ({
      key,
      label: key.replace(/_/g, ' ').replace(/^line \d+ /, (m) => m.toUpperCase()),
      value,
      numValue: parseFloat(value) || 0,
    }))
    .sort((a, b) => {
      const aNum = parseInt(a.key.match(/line_(\d+)/)?.[1] || '999')
      const bNum = parseInt(b.key.match(/line_(\d+)/)?.[1] || '999')
      return aNum - bNum
    })
})

const scoreColor = computed(() => {
  const s = validation.value?.overall_score ?? 0
  if (s >= 80) return '#2b8a3e'
  if (s >= 60) return '#e67700'
  return '#c92a2a'
})

const criticalChecks = computed(() => validation.value?.check_results?.filter((c: any) => !c.passed && c.severity === 'critical') || [])
const highChecks = computed(() => validation.value?.check_results?.filter((c: any) => !c.passed && c.severity === 'high') || [])
const mediumChecks = computed(() => validation.value?.check_results?.filter((c: any) => !c.passed && c.severity === 'medium') || [])
const passedChecks = computed(() => validation.value?.check_results?.filter((c: any) => c.passed) || [])

// Step 1: Select period
function setMonthlyPeriod(offset: number) {
  const d = new Date()
  d.setMonth(d.getMonth() + offset)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  periodStart.value = `${y}-${m}-01`
  const lastDay = new Date(y, d.getMonth() + 1, 0).getDate()
  periodEnd.value = `${y}-${m}-${String(lastDay).padStart(2, '0')}`
}

function setQuarterlyPeriod(q: number) {
  const y = new Date().getFullYear()
  const startMonth = (q - 1) * 3 + 1
  const endMonth = q * 3
  periodStart.value = `${y}-${String(startMonth).padStart(2, '0')}-01`
  const lastDay = new Date(y, endMonth, 0).getDate()
  periodEnd.value = `${y}-${String(endMonth).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
}

function setAnnualPeriod(year: number) {
  periodStart.value = `${year}-01-01`
  periodEnd.value = `${year}-12-31`
}

// Step 2: Calculate from GL
async function calculateFromGL() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await taxBridgeApi.calculate({
      form_type: formType.value,
      period_start: periodStart.value,
      period_end: periodEnd.value,
    })
    taxResult.value = data.data
    step.value = 2
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'GL calculation failed. Make sure you have journal entries for this period.'
  } finally {
    loading.value = false
  }
}

// Step 3: Save as report
async function saveAsReport() {
  if (!taxResult.value) return
  loading.value = true
  error.value = ''
  try {
    // Convert result map to manual_data for report generation
    const manualData: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(taxResult.value.result)) {
      manualData[k] = v
    }
    const { data } = await reportsApi.generate({
      report_type: formType.value,
      period: periodStart.value.slice(0, 7), // YYYY-MM
      manual_data: manualData,
    })
    report.value = data.data
    reportId.value = data.data?.id
    step.value = 3
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Failed to save report'
  } finally {
    loading.value = false
  }
}

// Step 4: Run compliance check
async function runCompliance() {
  if (!reportId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await complianceApi.validate(reportId.value)
    validation.value = data.data
    step.value = 4
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Compliance check failed'
  } finally {
    loading.value = false
  }
}

// Step 5: Export
async function exportDAT() {
  try {
    const period = periodStart.value.slice(0, 7) // YYYY-MM
    const { data } = await taxExportApi.exportDAT(formType.value, period)
    const blob = new Blob([data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formType.value}_${period}.dat`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Export not available for this form type yet'
  }
}

async function downloadPDF() {
  if (!reportId.value) return
  try {
    const { data } = await reportsApi.download(reportId.value)
    const blob = new Blob([data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formType.value}_${periodStart.value.slice(0, 7)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'PDF export failed'
  }
}

async function downloadExcel() {
  if (!reportId.value) return
  try {
    const { data } = await reportsApi.exportExcel(reportId.value)
    const blob = new Blob([data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formType.value}_${periodStart.value.slice(0, 7)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Excel export failed'
  }
}

function goToStep(s: number) {
  if (s < step.value) step.value = s
}

function formatMoney(v: string | number): string {
  const n = Number(v) || 0
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function startOver() {
  step.value = 1
  taxResult.value = null
  reportId.value = ''
  report.value = null
  validation.value = null
  error.value = ''
}
</script>

<template>
  <div class="tax-prep">
    <div class="view-header">
      <h2>Prep for Taxes</h2>
      <button v-if="step > 1" class="btn" @click="startOver">Start Over</button>
    </div>

    <!-- Progress Steps -->
    <div class="steps-bar">
      <div v-for="s in 4" :key="s" :class="['step-item', { active: step === s, done: step > s }]" @click="goToStep(s)">
        <div class="step-num">{{ step > s ? '&#10003;' : s }}</div>
        <div class="step-label">{{ ['Select Period', 'Review GL Data', 'Save Report', 'Compliance'][s - 1] }}</div>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Step 1: Select Period & Form -->
    <div v-if="step === 1" class="step-content">
      <h3>Step 1: Select Tax Form & Period</h3>

      <div class="form-section">
        <label>Tax Form</label>
        <div class="form-cards">
          <div
            v-for="form in recommendedForms"
            :key="form.form_type"
            :class="['form-card', { selected: formType === form.form_type }]"
            @click="formType = form.form_type"
          >
            <div class="form-card-header">
              <strong>{{ form.form_type.replace(/_/g, ' ') }}</strong>
              <span v-if="form.required" class="badge badge-red">Required</span>
            </div>
            <div class="form-card-name">{{ form.name }}</div>
            <div class="form-card-freq">{{ form.frequency }} | Due: Day {{ form.deadline_day || '-' }}</div>
            <div class="form-card-reason">{{ form.reason }}</div>
          </div>
        </div>

        <div v-if="!recommendedForms.length" class="manual-select">
          <select v-model="formType">
            <option value="BIR_2550M">BIR 2550M - Monthly VAT</option>
            <option value="BIR_2550Q">BIR 2550Q - Quarterly VAT</option>
            <option value="BIR_0619E">BIR 0619E - Monthly EWT</option>
            <option value="BIR_1601C">BIR 1601C - Monthly Compensation</option>
            <option value="BIR_1701">BIR 1701 - Annual ITR (Individual)</option>
            <option value="BIR_1702">BIR 1702 - Annual ITR (Corporation)</option>
          </select>
        </div>
      </div>

      <div class="form-section">
        <label>Filing Period</label>
        <div class="period-shortcuts">
          <button class="btn-sm" @click="setMonthlyPeriod(-1)">Last Month</button>
          <button class="btn-sm" @click="setMonthlyPeriod(0)">This Month</button>
          <button class="btn-sm" @click="setQuarterlyPeriod(1)">Q1</button>
          <button class="btn-sm" @click="setQuarterlyPeriod(2)">Q2</button>
          <button class="btn-sm" @click="setQuarterlyPeriod(3)">Q3</button>
          <button class="btn-sm" @click="setQuarterlyPeriod(4)">Q4</button>
          <button class="btn-sm" @click="setAnnualPeriod(new Date().getFullYear() - 1)">{{ new Date().getFullYear() - 1 }}</button>
          <button class="btn-sm" @click="setAnnualPeriod(new Date().getFullYear())">{{ new Date().getFullYear() }}</button>
        </div>
        <div class="date-range">
          <div class="form-group">
            <label>From</label>
            <input type="date" v-model="periodStart" />
          </div>
          <div class="form-group">
            <label>To</label>
            <input type="date" v-model="periodEnd" />
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button class="btn primary" :disabled="!periodStart || !periodEnd || loading" @click="calculateFromGL">
          {{ loading ? 'Calculating...' : 'Calculate from GL' }}
        </button>
      </div>
    </div>

    <!-- Step 2: Review GL Data -->
    <div v-if="step === 2" class="step-content">
      <h3>Step 2: Review GL Auto-Fill — {{ formLabel }}</h3>
      <p class="step-subtitle">Period: {{ periodLabel }} ({{ periodStart }} to {{ periodEnd }})</p>

      <div v-if="taxResult" class="gl-results">
        <table class="data-table">
          <thead>
            <tr><th>Line</th><th>Description</th><th class="money">Amount (PHP)</th></tr>
          </thead>
          <tbody>
            <tr v-for="entry in resultEntries" :key="entry.key" :class="{ 'total-row': entry.key.includes('total') || entry.key.includes('payable') }">
              <td class="mono">{{ entry.key.match(/line_(\d+)/)?.[1] || '-' }}</td>
              <td>{{ entry.label }}</td>
              <td class="money">{{ formatMoney(entry.value) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="gl-note">Data sourced from General Ledger. Review amounts before saving.</p>
      </div>

      <div class="step-actions">
        <button class="btn" @click="step = 1">Back</button>
        <button class="btn primary" :disabled="loading" @click="saveAsReport">
          {{ loading ? 'Saving...' : 'Save as Report' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Report Saved -->
    <div v-if="step === 3" class="step-content">
      <h3>Step 3: Report Saved</h3>
      <div class="success-box">
        <div class="success-icon">&#10003;</div>
        <div>
          <strong>{{ formLabel }}</strong> report for <strong>{{ periodLabel }}</strong> has been saved as a draft.
          <div v-if="report" class="report-id">Report ID: {{ report.id }}</div>
        </div>
      </div>

      <div class="step-actions">
        <button class="btn" @click="step = 2">Back</button>
        <button class="btn primary" :disabled="loading" @click="runCompliance">
          {{ loading ? 'Validating...' : 'Run Compliance Check' }}
        </button>
      </div>
    </div>

    <!-- Step 4: Compliance & Export -->
    <div v-if="step === 4" class="step-content">
      <h3>Step 4: Compliance Check & Export</h3>

      <div v-if="validation" class="compliance-section">
        <div class="score-card" :style="{ borderLeftColor: scoreColor }">
          <div class="score-value" :style="{ color: scoreColor }">{{ validation.overall_score }}</div>
          <div class="score-label">Compliance Score</div>
          <div class="score-status">
            {{ validation.overall_score >= 80 ? 'Ready to file' : validation.overall_score >= 60 ? 'Review recommended' : 'Issues found' }}
          </div>
        </div>

        <!-- Issues -->
        <div v-if="criticalChecks.length" class="check-group">
          <h4 class="severity-critical">Critical Issues ({{ criticalChecks.length }})</h4>
          <div v-for="c in criticalChecks" :key="c.check_id" class="check-item critical">
            <span class="check-icon">&#10007;</span>
            <div><strong>{{ c.check_name }}</strong><br/>{{ c.message }}</div>
          </div>
        </div>

        <div v-if="highChecks.length" class="check-group">
          <h4 class="severity-high">High Issues ({{ highChecks.length }})</h4>
          <div v-for="c in highChecks" :key="c.check_id" class="check-item high">
            <span class="check-icon">&#10007;</span>
            <div><strong>{{ c.check_name }}</strong><br/>{{ c.message }}</div>
          </div>
        </div>

        <div v-if="mediumChecks.length" class="check-group">
          <h4 class="severity-medium">Medium Issues ({{ mediumChecks.length }})</h4>
          <div v-for="c in mediumChecks" :key="c.check_id" class="check-item medium">
            <span class="check-icon">!</span>
            <div><strong>{{ c.check_name }}</strong><br/>{{ c.message }}</div>
          </div>
        </div>

        <div v-if="passedChecks.length" class="check-group">
          <details>
            <summary class="severity-passed">Passed Checks ({{ passedChecks.length }})</summary>
            <div v-for="c in passedChecks" :key="c.check_id" class="check-item passed">
              <span class="check-icon">&#10003;</span>
              <div>{{ c.check_name }}</div>
            </div>
          </details>
        </div>

        <!-- RAG Findings -->
        <div v-if="validation.rag_findings?.length" class="check-group">
          <h4>AI-Powered Findings</h4>
          <div v-for="(f, i) in validation.rag_findings" :key="i" class="rag-finding">
            <span :class="['badge', f.severity === 'high' ? 'badge-red' : f.severity === 'medium' ? 'badge-orange' : 'badge-gray']">{{ f.severity }}</span>
            <div>
              {{ f.finding }}
              <div v-if="f.regulation_reference" class="reg-ref">Ref: {{ f.regulation_reference }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Actions -->
      <div class="export-section">
        <h4>Export Options</h4>
        <div class="export-buttons">
          <button class="btn primary" @click="exportDAT">
            Export eBIRForms (.dat)
          </button>
          <button class="btn" @click="downloadPDF">
            Download PDF
          </button>
          <button class="btn" @click="downloadExcel">
            Download Excel
          </button>
        </div>
        <p class="export-note">eBIRForms DAT export supports all BIR forms: 2550M, 2550Q, 1601C, 0619E, 1701, 1702, 2316, 2307, and SAWT.</p>
      </div>

      <div class="step-actions">
        <button class="btn" @click="step = 3">Back</button>
        <button class="btn" @click="startOver">File Another Form</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tax-prep { max-width: 900px; margin: 0 auto; padding: 1rem; }
.view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.view-header h2 { margin: 0; }

/* Steps bar */
.steps-bar { display: flex; gap: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-color, #eee); }
.step-item { flex: 1; text-align: center; padding: 0.75rem 0.5rem; cursor: pointer; position: relative; border-bottom: 3px solid transparent; margin-bottom: -2px; }
.step-item.active { border-bottom-color: #228be6; }
.step-item.done { border-bottom-color: #40c057; }
.step-num { width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.85rem; background: var(--border-color, #e9ecef); color: #666; margin-bottom: 0.25rem; }
.step-item.active .step-num { background: #228be6; color: #fff; }
.step-item.done .step-num { background: #40c057; color: #fff; }
.step-label { font-size: 0.8rem; color: #888; }
.step-item.active .step-label { color: #228be6; font-weight: 500; }

.step-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

h3 { margin: 0 0 0.5rem; }
.step-subtitle { color: #666; margin: 0 0 1rem; }
.step-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color, #eee); }

.error { color: #dc3545; padding: 0.5rem; background: #fff5f5; border-radius: 4px; margin-bottom: 1rem; }

/* Form section */
.form-section { margin-bottom: 1.5rem; }
.form-section > label { font-weight: 600; display: block; margin-bottom: 0.5rem; }

/* Form cards */
.form-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; }
.form-card { border: 2px solid var(--border-color, #e9ecef); border-radius: 8px; padding: 0.75rem; cursor: pointer; transition: border-color 0.15s; }
.form-card:hover { border-color: #a5d8ff; }
.form-card.selected { border-color: #228be6; background: #f0f7ff; }
.form-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }
.form-card-name { font-size: 0.85rem; color: #333; }
.form-card-freq { font-size: 0.75rem; color: #888; margin-top: 0.25rem; }
.form-card-reason { font-size: 0.75rem; color: #666; margin-top: 0.25rem; font-style: italic; }

.manual-select select { width: 100%; padding: 0.5rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; }

/* Period shortcuts */
.period-shortcuts { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem; }
.date-range { display: flex; gap: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; }
.form-group label { font-size: 0.85rem; color: #666; }
.form-group input { padding: 0.4rem 0.6rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; }

/* GL Results table */
.gl-results { margin-top: 1rem; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border-color, #eee); }
.data-table th { font-weight: 600; font-size: 0.85rem; color: #666; }
.mono { font-family: monospace; }
.money { text-align: right; font-variant-numeric: tabular-nums; }
.total-row { font-weight: 600; background: var(--hover-bg, #f8f9fa); }
.gl-note { font-size: 0.85rem; color: #888; margin-top: 0.5rem; font-style: italic; }

/* Success box */
.success-box { display: flex; gap: 1rem; align-items: center; padding: 1rem; background: #d3f9d8; border-radius: 8px; }
.success-icon { width: 40px; height: 40px; border-radius: 50%; background: #40c057; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; flex-shrink: 0; }
.report-id { font-size: 0.8rem; color: #666; margin-top: 0.25rem; font-family: monospace; }

/* Compliance */
.compliance-section { margin-bottom: 1.5rem; }
.score-card { display: flex; align-items: center; gap: 1rem; padding: 1rem; background: var(--hover-bg, #f8f9fa); border-radius: 8px; border-left: 4px solid; margin-bottom: 1rem; }
.score-value { font-size: 2.5rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 0.85rem; color: #666; }
.score-status { font-weight: 500; }

.check-group { margin-bottom: 1rem; }
.check-group h4 { margin: 0.5rem 0; }
.severity-critical { color: #c92a2a; }
.severity-high { color: #e67700; }
.severity-medium { color: #1971c2; }
.severity-passed { color: #2b8a3e; cursor: pointer; }

.check-item { display: flex; gap: 0.5rem; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.25rem; }
.check-item.critical { background: #fff5f5; }
.check-item.high { background: #fff9db; }
.check-item.medium { background: #e7f5ff; }
.check-item.passed { background: #ebfbee; }
.check-icon { font-weight: 700; flex-shrink: 0; width: 20px; text-align: center; }
.check-item.critical .check-icon { color: #c92a2a; }
.check-item.high .check-icon { color: #e67700; }
.check-item.medium .check-icon { color: #1971c2; }
.check-item.passed .check-icon { color: #2b8a3e; }

.rag-finding { display: flex; gap: 0.5rem; padding: 0.5rem; margin-bottom: 0.25rem; }
.reg-ref { font-size: 0.8rem; color: #888; margin-top: 0.2rem; }

/* Export */
.export-section { padding: 1rem; background: var(--hover-bg, #f8f9fa); border-radius: 8px; }
.export-section h4 { margin: 0 0 0.75rem; }
.export-buttons { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.export-note { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }

/* Badges & buttons */
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: 500; }
.badge-red { background: #ffe0e0; color: #c92a2a; }
.badge-orange { background: #fff3e0; color: #e67700; }
.badge-gray { background: #e9ecef; color: #495057; }
.badge-green { background: #d3f9d8; color: #2b8a3e; }

.btn { padding: 0.5rem 1rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; cursor: pointer; background: var(--bg-color, #fff); }
.btn.primary { background: #228be6; color: #fff; border-color: #228be6; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.85rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; cursor: pointer; background: var(--bg-color, #fff); }
.btn-sm:hover { background: var(--hover-bg, #f0f0f0); }

@media (max-width: 768px) {
  .tax-prep { max-width: 100%; padding: 0.5rem; }
  .steps-bar { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .step-item { min-width: 80px; flex-shrink: 0; padding: 0.5rem 0.25rem; }
  .step-label { font-size: 0.7rem; }
  .form-cards { grid-template-columns: 1fr; }
  .date-range { flex-direction: column; gap: 0.5rem; }
  .score-card { flex-direction: column; text-align: center; }
  .export-buttons { flex-direction: column; }
  .export-buttons .btn { width: 100%; }
}
</style>
