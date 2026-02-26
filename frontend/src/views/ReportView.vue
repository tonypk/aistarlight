<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import ComplianceScoreBadge from '../components/report/ComplianceScoreBadge.vue'
import ReportPreview from '../components/report/ReportPreview.vue'
import { formsApi, type FormSummary } from '../api/forms'
import { useReportStore } from '../stores/report'
import { useUploadStore } from '../stores/upload'
import { reconciliationApi } from '../api/transactions'

interface SessionOption {
  id: string
  period: string
  status: string
  created_at: string
}

const router = useRouter()
const reportStore = useReportStore()
const uploadStore = useUploadStore()
const period = ref(new Date().toISOString().slice(0, 7))
const generating = ref(false)
const transitioning = ref<string | null>(null)
const error = ref('')

// F1: Compliance fix suggestions
interface FailedCheckFix {
  check_id: string
  check_name: string
  severity: string
  message: string
  fix_suggestion: string
  fix_action: string
  target_field?: string
}
const complianceFixes = ref<FailedCheckFix[]>([])
const complianceFixReportId = ref('')

// F8: Transition comment
const transitionComment = ref('')
const showCommentDialog = ref(false)
const pendingTransition = ref<{ id: string; target: string } | null>(null)

// F9: Amendments
const amendments = ref<Record<string, unknown>[]>([])
const showAmendments = ref<string | null>(null)

// Session-based report generation
const sessions = ref<SessionOption[]>([])
const selectedSessionId = ref('')

// Dynamic form type selection
const availableForms = ref<FormSummary[]>([])
const selectedFormType = ref('BIR_2550M')

// Data source: 'session' | 'file' | 'none'
const dataSource = computed(() => {
  if (selectedSessionId.value) return 'session'
  if (uploadStore.hasFile && uploadStore.hasMappings) return 'file'
  return 'none'
})

const canGenerate = computed(() => dataSource.value !== 'none')

onMounted(async () => {
  reportStore.fetchReports()

  // Load sessions for the selector
  try {
    const sessRes = await reconciliationApi.listSessions(1, 100)
    const all: SessionOption[] = sessRes.data.data || []
    // Show sessions that have been classified or reconciled (not just draft)
    sessions.value = all.filter(s => s.status !== 'draft')
  } catch {
    sessions.value = []
  }

  // Load available form types from schema registry + supported forms
  try {
    const res = await formsApi.list()
    // Filter out coming_soon forms — only show active/generatable forms
    const allForms: FormSummary[] = res.data.data || []
    availableForms.value = allForms.filter(f => f.status !== 'coming_soon')
    if (availableForms.value.length > 0 && !availableForms.value.find(f => f.form_type === selectedFormType.value)) {
      selectedFormType.value = availableForms.value[0].form_type
    }
  } catch {
    // Fallback: at minimum show BIR_2550M
    availableForms.value = [{ form_type: 'BIR_2550M', name: 'Monthly Value-Added Tax Declaration', frequency: 'monthly' }]
  }
})

async function handleGenerate() {
  generating.value = true
  error.value = ''
  try {
    if (selectedSessionId.value) {
      // Generate from session (uses transaction data from reconciliation)
      const res = await reconciliationApi.generateReport(selectedSessionId.value, selectedFormType.value)
      const reportId = res.data.data?.id
      if (reportId) {
        await reportStore.fetchReport(reportId)
      }
    } else if (uploadStore.hasFile && uploadStore.hasMappings) {
      // Generate from uploaded file
      await reportStore.generateReport({
        report_type: selectedFormType.value,
        period: period.value,
        data_file_id: uploadStore.fileId!,
        column_mappings: uploadStore.confirmedMappings,
      })
    } else {
      error.value = 'Please select a session or upload a file first'
      return
    }
    await reportStore.fetchReports()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to generate report'
  } finally {
    generating.value = false
  }
}

function handleDownload(id: string) {
  reportStore.downloadReport(id)
}

function handleEdit(id: string) {
  router.push(`/reports/${id}/edit`)
}

function promptTransition(id: string, targetStatus: string) {
  // For approve/reject/file, show comment dialog
  if (['approved', 'rejected', 'filed'].includes(targetStatus)) {
    pendingTransition.value = { id, target: targetStatus }
    transitionComment.value = ''
    showCommentDialog.value = true
  } else {
    handleTransition(id, targetStatus)
  }
}

async function confirmTransition() {
  if (!pendingTransition.value) return
  showCommentDialog.value = false
  const { id, target } = pendingTransition.value
  await handleTransition(id, target, transitionComment.value || undefined)
  pendingTransition.value = null
}

async function handleTransition(id: string, targetStatus: string, comment?: string) {
  transitioning.value = id
  error.value = ''
  complianceFixes.value = []
  try {
    await reportStore.transitionReport(id, { target_status: targetStatus, comment })
    await reportStore.fetchReports()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string; data?: { failed_checks?: FailedCheckFix[] } } }; status?: number }
    // F1: Handle 422 compliance blocked error
    if (err.response?.data?.data?.failed_checks) {
      complianceFixes.value = err.response.data.data.failed_checks
      complianceFixReportId.value = id
      error.value = err.response.data.error || 'Compliance check failed'
    } else {
      error.value = err.response?.data?.error || 'Transition failed'
    }
  } finally {
    transitioning.value = null
  }
}

async function handleAmend(id: string) {
  transitioning.value = id
  error.value = ''
  try {
    const amended = await reportStore.amendReport(id)
    if (amended?.id) {
      router.push(`/reports/${amended.id}/edit`)
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to create amendment'
  } finally {
    transitioning.value = null
  }
}

async function toggleAmendments(id: string) {
  if (showAmendments.value === id) {
    showAmendments.value = null
    return
  }
  try {
    amendments.value = await reportStore.fetchAmendments(id)
    showAmendments.value = id
  } catch {
    amendments.value = []
  }
}

function getWorkflowActions(status: string): { label: string; target: string; color: string }[] {
  const map: Record<string, { label: string; target: string; color: string }[]> = {
    draft: [{ label: 'Submit for Review', target: 'review', color: '#3b82f6' }],
    review: [
      { label: 'Approve', target: 'approved', color: '#22c55e' },
      { label: 'Reject', target: 'rejected', color: '#ef4444' },
      { label: 'Return to Draft', target: 'draft', color: '#f59e0b' },
    ],
    approved: [
      { label: 'Mark as Filed', target: 'filed', color: '#8b5cf6' },
      { label: 'Return to Review', target: 'review', color: '#f59e0b' },
    ],
    rejected: [{ label: 'Return to Draft', target: 'draft', color: '#f59e0b' }],
    filed: [{ label: 'Archive', target: 'archived', color: '#6b7280' }],
    archived: [],
  }
  return map[status] || []
}

function isEditable(status: string): boolean {
  return ['draft', 'review', 'rejected'].includes(status)
}

function statusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'draft',
    review: 'review',
    approved: 'approved',
    rejected: 'rejected',
    filed: 'filed',
    archived: 'archived',
    confirmed: 'confirmed',
  }
  return colors[status] || 'draft'
}

function formatFormType(type: string): string {
  return type.replace(/_/g, ' ')
}
</script>

<template>
  <div class="report-view">
    <div class="header-row">
      <h2>Reports</h2>
    </div>

    <!-- Generation form -->
    <div class="gen-card">
      <h3>Generate Report</h3>

      <div class="form-row">
        <label>Form Type:</label>
        <select v-model="selectedFormType" class="form-select" data-testid="report-form-type">
          <option v-for="form in availableForms" :key="form.form_type" :value="form.form_type">
            {{ formatFormType(form.form_type) }} — {{ form.name }}
          </option>
        </select>
      </div>

      <div class="form-row">
        <label>Data Source:</label>
        <select v-model="selectedSessionId" class="form-select">
          <option value="">— Select a session —</option>
          <option v-for="s in sessions" :key="s.id" :value="s.id">
            {{ s.period }} ({{ s.status }}) — {{ new Date(s.created_at).toLocaleDateString() }}
          </option>
        </select>
      </div>

      <div v-if="dataSource === 'session'" class="data-source">
        Generating from session data (VAT summary from reconciliation)
      </div>
      <div v-else-if="dataSource === 'file'" class="data-source">
        Using uploaded file: <strong>{{ uploadStore.filename }}</strong>
        with {{ Object.keys(uploadStore.confirmedMappings).length }} mapped columns
      </div>
      <div v-else class="data-source data-source-warn">
        No data source selected.
        <router-link to="/classification">Classify transactions</router-link> or
        <router-link to="/upload">upload a file</router-link> first.
      </div>

      <div class="form-row">
        <label>Period:</label>
        <input type="month" v-model="period" data-testid="report-period" />
        <button
          class="gen-btn"
          @click="handleGenerate"
          :disabled="generating || !canGenerate"
          data-testid="report-generate-btn"
        >
          {{ generating ? 'Generating...' : 'Generate Report' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- F1: Compliance Fix Suggestions -->
    <div v-if="complianceFixes.length" class="fixes-panel">
      <h4>Compliance Issues to Fix</h4>
      <div v-for="fix in complianceFixes" :key="fix.check_id" class="fix-item" :class="fix.severity">
        <div class="fix-header">
          <span class="fix-severity" :class="fix.severity">{{ fix.severity }}</span>
          <strong>{{ fix.check_name }}</strong>
        </div>
        <p class="fix-message">{{ fix.message }}</p>
        <p class="fix-suggestion">{{ fix.fix_suggestion }}</p>
        <span v-if="fix.target_field" class="fix-field">Field: {{ fix.target_field }}</span>
      </div>
      <button v-if="complianceFixReportId" class="edit-btn" @click="handleEdit(complianceFixReportId)">
        Edit Report to Fix Issues
      </button>
    </div>

    <!-- F8: Transition Comment Dialog -->
    <div v-if="showCommentDialog" class="dialog-overlay" @click.self="showCommentDialog = false">
      <div class="dialog">
        <h4>{{ pendingTransition?.target === 'approved' ? 'Approve' : pendingTransition?.target === 'rejected' ? 'Reject' : 'File' }} Report</h4>
        <label>Comment (optional):</label>
        <textarea v-model="transitionComment" rows="3" placeholder="Add a comment..."></textarea>
        <div class="dialog-actions">
          <button class="cancel-btn" @click="showCommentDialog = false">Cancel</button>
          <button class="confirm-btn" @click="confirmTransition">Confirm</button>
        </div>
      </div>
    </div>

    <!-- F9: Amendment Chain -->
    <div v-if="showAmendments && amendments.length" class="amendments-panel">
      <h4>Amendment Chain</h4>
      <table class="amendments-table">
        <thead><tr><th>#</th><th>Status</th><th>Period</th><th>Created</th></tr></thead>
        <tbody>
          <tr v-for="a in amendments" :key="(a as any).id">
            <td>{{ (a as any).amendment_number === 0 ? 'Original' : 'Amendment #' + (a as any).amendment_number }}</td>
            <td><span class="badge" :class="statusColor((a as any).status)">{{ (a as any).status }}</span></td>
            <td>{{ (a as any).period }}</td>
            <td>{{ new Date((a as any).created_at).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
      <button class="cancel-btn" @click="showAmendments = null">Close</button>
    </div>

    <!-- Current report preview -->
    <ReportPreview
      v-if="reportStore.currentReport"
      :data="(reportStore.currentReport.calculated_data as Record<string, string>)"
      :report-type="formatFormType((reportStore.currentReport.report_type as string) || selectedFormType)"
      :status="(reportStore.currentReport.status as string)"
      :form-type="(reportStore.currentReport.report_type as string) || selectedFormType"
    />

    <!-- Report history -->
    <div class="report-list" v-if="reportStore.reports.length" data-testid="report-table">
      <h3>Previous Reports</h3>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Period</th>
            <th>Status</th>
            <th>Compliance</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in reportStore.reports" :key="r.id" data-testid="report-row">
            <td>{{ formatFormType(r.report_type) }}</td>
            <td>{{ r.period }}</td>
            <td><span class="badge" :class="statusColor(r.status)">{{ r.status }}</span></td>
            <td><ComplianceScoreBadge :score="r.compliance_score ?? null" /></td>
            <td>{{ new Date(r.created_at).toLocaleDateString() }}</td>
            <td class="actions-cell">
              <button class="dl-btn" @click="handleDownload(r.id)">PDF</button>
              <button class="csv-btn" @click="reportStore.exportCsv(r.id)">CSV</button>
              <button class="excel-btn" @click="reportStore.exportExcel(r.id)">Excel</button>
              <button
                v-if="isEditable(r.status)"
                class="edit-btn"
                @click="handleEdit(r.id)"
              >Edit</button>
              <button
                v-if="r.status === 'filed'"
                class="amend-btn"
                :disabled="transitioning === r.id"
                @click="handleAmend(r.id)"
              >Amend</button>
              <button
                v-if="(r as any).amendment_number > 0 || (r as any).original_report_id"
                class="chain-btn"
                @click="toggleAmendments(r.id)"
              >Chain</button>
              <button
                v-for="action in getWorkflowActions(r.status)"
                :key="action.target"
                class="workflow-btn"
                :style="{ background: action.color }"
                :disabled="transitioning === r.id"
                @click="promptTransition(r.id, action.target)"
              >{{ action.label }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.gen-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 24px;
}
.gen-card h3 { margin-bottom: 16px; }
.form-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-width: 320px;
  background: #fff;
}
.data-source {
  padding: 10px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  margin: 16px 0;
  font-size: 14px;
  color: #166534;
}
.data-source-warn {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}
.data-source-warn a { color: #4f46e5; }
.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.form-row label { font-weight: 500; white-space: nowrap; }
.form-row input[type="month"] {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.gen-btn {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.gen-btn:hover { background: #4338ca; }
.gen-btn:disabled { opacity: 0.6; }
.error { color: #ef4444; margin-top: 12px; }
.report-list {
  margin-top: 24px;
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.report-list h3 { margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px; color: #888; font-size: 13px; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px; border-bottom: 1px solid #f3f4f6; }
.badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.badge.draft { background: #fef3c7; color: #92400e; }
.badge.confirmed { background: #d1fae5; color: #065f46; }
.badge.review { background: #dbeafe; color: #1e40af; }
.badge.approved { background: #d1fae5; color: #065f46; }
.badge.rejected { background: #fee2e2; color: #991b1b; }
.badge.filed { background: #ede9fe; color: #5b21b6; }
.badge.archived { background: #f3f4f6; color: #6b7280; }
.actions-cell {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.dl-btn {
  padding: 4px 10px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.csv-btn {
  padding: 4px 10px;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #065f46;
}
.csv-btn:hover { background: #a7f3d0; }
.edit-btn {
  padding: 4px 10px;
  background: #dbeafe;
  border: 1px solid #93c5fd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #1e40af;
}
.edit-btn:hover { background: #bfdbfe; }
.workflow-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  color: #fff;
  font-weight: 500;
}
.workflow-btn:hover { opacity: 0.9; }
.workflow-btn:disabled { opacity: 0.5; }
.excel-btn {
  padding: 4px 10px;
  background: #dbeafe;
  border: 1px solid #93c5fd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #1e40af;
}
.excel-btn:hover { background: #bfdbfe; }
.amend-btn {
  padding: 4px 10px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #92400e;
}
.chain-btn {
  padding: 4px 10px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
/* Compliance fixes panel */
.fixes-panel {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.fixes-panel h4 { margin-bottom: 12px; color: #991b1b; }
.fix-item {
  background: #fff;
  border: 1px solid #fde8e8;
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 8px;
}
.fix-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.fix-severity {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}
.fix-severity.critical { background: #fee2e2; color: #dc2626; }
.fix-severity.high { background: #fef3c7; color: #d97706; }
.fix-severity.medium { background: #e0f2fe; color: #0284c7; }
.fix-severity.low { background: #f3f4f6; color: #6b7280; }
.fix-message { font-size: 13px; color: #6b7280; margin: 0 0 4px; }
.fix-suggestion { font-size: 13px; color: #166534; font-weight: 500; margin: 0 0 4px; }
.fix-field { font-size: 11px; color: #9ca3af; }
/* Dialog */
.dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.dialog {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 420px;
  max-width: 90vw;
}
.dialog h4 { margin-bottom: 12px; }
.dialog label { display: block; font-size: 13px; color: #555; margin-bottom: 6px; }
.dialog textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 14px;
  resize: vertical;
}
.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.cancel-btn {
  padding: 6px 16px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.confirm-btn {
  padding: 6px 16px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
/* Amendments panel */
.amendments-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.amendments-panel h4 { margin-bottom: 10px; }
.amendments-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
.amendments-table th { text-align: left; padding: 6px 8px; font-size: 12px; color: #888; border-bottom: 1px solid #e5e7eb; }
.amendments-table td { padding: 6px 8px; font-size: 13px; border-bottom: 1px solid #f3f4f6; }
</style>
