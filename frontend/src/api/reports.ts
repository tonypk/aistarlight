import { client } from './client'

export interface ReportGenerateData {
  report_type: string
  period: string
  data_file_id?: string
  column_mappings?: Record<string, string>
  manual_data?: Record<string, unknown>
}

export interface ReportEditData {
  field_overrides: Record<string, string>
  recalculate?: boolean
  notes?: string
  version: number
}

export interface ReportTransitionData {
  target_status: string
  comment?: string
}

export const reportsApi = {
  generate: (data: ReportGenerateData) => client.post('/reports/generate', data),
  list: (page = 1, limit = 20) => client.get('/reports', { params: { page, limit } }),
  get: (id: string) => client.get(`/reports/${id}`),
  download: (id: string) => client.get(`/reports/${id}/download`, { responseType: 'blob' }),
  confirm: (id: string) => client.patch(`/reports/${id}/confirm`),
  edit: (id: string, data: ReportEditData) => client.patch(`/reports/${id}/edit`, data),
  transition: (id: string, data: ReportTransitionData) => client.patch(`/reports/${id}/transition`, data),
  supportedForms: () => client.get('/reports/supported-forms'),
  auditLogs: (reportId: string, page = 1) => client.get(`/audit/report/${reportId}`, { params: { page } }),
}
