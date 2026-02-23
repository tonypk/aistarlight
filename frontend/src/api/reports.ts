import { client } from './client'

export interface ReportGenerateData {
  report_type: string
  period: string
  data_file_id?: string
  column_mappings?: Record<string, string>
  manual_data?: Record<string, unknown>
}

export const reportsApi = {
  generate: (data: ReportGenerateData) => client.post('/reports/generate', data),
  list: (page = 1, limit = 20) => client.get('/reports', { params: { page, limit } }),
  get: (id: string) => client.get(`/reports/${id}`),
  download: (id: string) => client.get(`/reports/${id}/download`, { responseType: 'blob' }),
  confirm: (id: string) => client.patch(`/reports/${id}/confirm`),
  supportedForms: () => client.get('/reports/supported-forms'),
}
