import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reportsApi, type ReportGenerateData } from '../api/reports'

interface ReportSummary {
  id: string
  report_type: string
  period: string
  status: string
  created_at: string
}

export const useReportStore = defineStore('report', () => {
  const reports = ref<ReportSummary[]>([])
  const currentReport = ref<Record<string, unknown> | null>(null)
  const loading = ref(false)

  async function fetchReports(page = 1) {
    loading.value = true
    try {
      const res = await reportsApi.list(page)
      reports.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function generateReport(data: ReportGenerateData) {
    loading.value = true
    try {
      const res = await reportsApi.generate(data)
      currentReport.value = res.data.data
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchReport(id: string) {
    const res = await reportsApi.get(id)
    currentReport.value = res.data.data
  }

  async function downloadReport(id: string) {
    const res = await reportsApi.download(id)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `report_${id}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  return { reports, currentReport, loading, fetchReports, generateReport, fetchReport, downloadReport }
})
