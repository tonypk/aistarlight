<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ReportPreview from '../components/report/ReportPreview.vue'
import { useReportStore } from '../stores/report'
import { useUploadStore } from '../stores/upload'

const reportStore = useReportStore()
const uploadStore = useUploadStore()
const period = ref(new Date().toISOString().slice(0, 7))
const generating = ref(false)
const error = ref('')

onMounted(() => {
  reportStore.fetchReports()
})

async function handleGenerate() {
  generating.value = true
  error.value = ''
  try {
    if (uploadStore.hasFile && uploadStore.hasMappings) {
      // File-based flow
      await reportStore.generateReport({
        report_type: 'BIR_2550M',
        period: period.value,
        data_file_id: uploadStore.fileId!,
        column_mappings: uploadStore.confirmedMappings,
      })
    } else {
      // Manual data fallback (demo)
      await reportStore.generateReport({
        report_type: 'BIR_2550M',
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
</script>

<template>
  <div class="report-view">
    <div class="header-row">
      <h2>Reports</h2>
    </div>

    <!-- Generation form -->
    <div class="gen-card">
      <h3>Generate BIR 2550M</h3>

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
      report-type="BIR 2550M"
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
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in reportStore.reports" :key="r.id">
            <td>{{ r.report_type }}</td>
            <td>{{ r.period }}</td>
            <td><span class="badge" :class="r.status">{{ r.status }}</span></td>
            <td>{{ new Date(r.created_at).toLocaleDateString() }}</td>
            <td>
              <button class="dl-btn" @click="handleDownload(r.id)">Download PDF</button>
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
.data-source {
  padding: 10px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  margin-bottom: 16px;
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
}
.form-row label { font-weight: 500; }
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
.dl-btn {
  padding: 4px 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
</style>
