import { defineStore } from "pinia";
import { ref } from "vue";
import {
  reportsApi,
  type ReportGenerateData,
  type ReportEditData,
  type ReportTransitionData,
} from "../api/reports";

interface ReportSummary {
  id: string;
  report_type: string;
  period: string;
  status: string;
  compliance_score?: number | null;
  created_at: string;
  version?: number;
}

interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  changes: Record<string, { old: string; new: string }> | null;
  comment: string | null;
  created_at: string;
}

export const useReportStore = defineStore("report", () => {
  const reports = ref<ReportSummary[]>([]);
  const currentReport = ref<Record<string, unknown> | null>(null);
  const auditLogs = ref<AuditLogEntry[]>([]);
  const loading = ref(false);

  async function fetchReports(page = 1) {
    loading.value = true;
    try {
      const res = await reportsApi.list(page);
      reports.value = res.data.data;
    } finally {
      loading.value = false;
    }
  }

  async function generateReport(data: ReportGenerateData) {
    loading.value = true;
    try {
      const res = await reportsApi.generate(data);
      currentReport.value = res.data.data;
      return res.data.data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchReport(id: string) {
    const res = await reportsApi.get(id);
    currentReport.value = res.data.data;
    return res.data.data;
  }

  async function editReport(id: string, data: ReportEditData) {
    loading.value = true;
    try {
      const res = await reportsApi.edit(id, data);
      currentReport.value = res.data.data;
      return res.data.data;
    } finally {
      loading.value = false;
    }
  }

  async function transitionReport(id: string, data: ReportTransitionData) {
    loading.value = true;
    try {
      const res = await reportsApi.transition(id, data);
      currentReport.value = res.data.data;
      return res.data.data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAuditLogs(reportId: string) {
    const res = await reportsApi.auditLogs(reportId);
    auditLogs.value = res.data.data;
    return res.data.data;
  }

  async function downloadReport(id: string) {
    let url = "";
    try {
      const res = await reportsApi.download(id);
      url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      alert("Failed to download report. Please try again.");
    } finally {
      if (url) window.URL.revokeObjectURL(url);
    }
  }

  async function exportCsv(id: string) {
    let url = "";
    try {
      const res = await reportsApi.exportCsv(id);
      url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      alert("Failed to export CSV. Please try again.");
    } finally {
      if (url) window.URL.revokeObjectURL(url);
    }
  }

  return {
    reports,
    currentReport,
    auditLogs,
    loading,
    fetchReports,
    generateReport,
    fetchReport,
    editReport,
    transitionReport,
    fetchAuditLogs,
    downloadReport,
    exportCsv,
  };
});
