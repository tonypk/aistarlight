<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ComplianceScoreBadge from '../components/report/ComplianceScoreBadge.vue'
import ReportPreview from '../components/report/ReportPreview.vue'
import { formsApi, type FormSummary } from '../api/forms'
import { useReportStore } from '../stores/report'
import { useUploadStore } from '../stores/upload'

const router = useRouter()
const reportStore = useReportStore()
const uploadStore = useUploadStore()
const period = ref(new Date().toISOString().slice(0, 7))
const generating = ref(false)
const transitioning = ref<string | null>(null)
const error = ref('')

// Dynamic form type selection
const availableForms = ref<FormSummary[]>([])
const selectedFormType = ref('BIR_2550M')

onMounted(async () => {
  reportStore.fetchReports()
  // Load available form types from schema registry + supported forms
  try {
    const res = await formsApi.list()
    availableForms.value = res.data.data || []
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
    if (uploadStore.hasFile && uploadStore.hasMappings) {
      await reportStore.generateReport({
        report_type: selectedFormType.value,
        period: period.value,
        data_file_id: uploadStore.fileId!,
        column_mappings: uploadStore.confirmedMappings,
      })
    } else {
      await reportStore.generateReport({
        report_type: selectedFormType.value,
        period: period.value,
        manual_data: {
          sales_data: [
            { amount: 100000, vat_type: 'vatable' },
            { amount: 20000, vat_type: 'exempt' },
          ],
          purchases_data: [
            { amount: 50000, category: 'goods' },
            { amount: 10000, category: 'services' },
          ],
        },
      })
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

async function handleTransition(id: string, targetStatus: string) {
  transitioning.value = id
  error.value = ''
  try {
    await reportStore.transitionReport(id, { target_status: targetStatus })
    await reportStore.fetchReports()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Transition failed'
  } finally {
    transitioning.value = null
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
        <select v-model="selectedFormType" class="form-select">
          <option v-for="form in availableForms" :key="form.form_type" :value="form.form_type">
            {{ formatFormType(form.form_type) }} — {{ form.name }}
          </option>
        </select>
      </div>

      <div v-if="uploadStore.hasFile && uploadStore.hasMappings" class="data-source">
        Using uploaded file: <strong>{{ uploadStore.filename }}</strong>
        with {{ Object.keys(uploadStore.confirmedMappings).length }} mapped columns
      </div>
      <div v-else class="data-source data-source-demo">
        No file uploaded — will use sample data for demo.
        <router-link to="/upload">Upload a file</router-link> for real data.
      </div>

      <div class="form-row">
        <label>Period:</label>
        <input type="month" v-model="period" />
        <button
          class="gen-btn"
          @click="handleGenerate"
          :disabled="generating"
        >
          {{ generating ? 'Generating...' : 'Generate Report' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
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
    <div class="report-list" v-if="reportStore.reports.length">
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
          <tr v-for="r in reportStore.reports" :key="r.id">
            <td>{{ formatFormType(r.report_type) }}</td>
            <td>{{ r.period }}</td>
            <td><span class="badge" :class="statusColor(r.status)">{{ r.status }}</span></td>
            <td><ComplianceScoreBadge :score="r.compliance_score ?? null" /></td>
            <td>{{ new Date(r.created_at).toLocaleDateString() }}</td>
            <td class="actions-cell">
              <button class="dl-btn" @click="handleDownload(r.id)">PDF</button>
              <button class="csv-btn" @click="reportStore.exportCsv(r.id)">CSV</button>
              <button
                v-if="isEditable(r.status)"
                class="edit-btn"
                @click="handleEdit(r.id)"
              >Edit</button>
              <button
                v-for="action in getWorkflowActions(r.status)"
                :key="action.target"
                class="workflow-btn"
                :style="{ background: action.color }"
                :disabled="transitioning === r.id"
                @click="handleTransition(r.id, action.target)"
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
.data-source-demo {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}
.data-source-demo a { color: #4f46e5; }
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
</style>
