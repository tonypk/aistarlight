<script setup lang="ts">
import { onMounted } from 'vue'
import ReportPreview from '../components/report/ReportPreview.vue'
import { useReportStore } from '../stores/report'

const store = useReportStore()

onMounted(() => {
  store.fetchReports()
})

async function handleGenerate() {
  await store.generateReport({
    report_type: 'BIR_2550M',
    period: new Date().toISOString().slice(0, 7),
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

function handleDownload(id: string) {
  store.downloadReport(id)
}
</script>

<template>
  <div class="report-view">
    <div class="header-row">
      <h2>Reports</h2>
      <button class="gen-btn" @click="handleGenerate" :disabled="store.loading">
        {{ store.loading ? 'Generating...' : 'Generate BIR 2550M' }}
      </button>
    </div>

    <ReportPreview
      v-if="store.currentReport"
      :data="(store.currentReport.calculated_data as Record<string, string>)"
      report-type="BIR 2550M"
    />

    <div class="report-list" v-if="store.reports.length">
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
          <tr v-for="r in store.reports" :key="r.id">
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
