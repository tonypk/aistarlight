import { client } from './client'
import type { TransactionFilters } from '../types/transaction'

export const reconciliationApi = {
  // Sessions
  createSession: (period: string, reportId?: string) =>
    client.post('/reconciliation/sessions', { period, report_id: reportId }),

  listSessions: (page = 1, limit = 20) =>
    client.get('/reconciliation/sessions', { params: { page, limit } }),

  getSession: (id: string) =>
    client.get(`/reconciliation/sessions/${id}`),

  deleteSession: (id: string) =>
    client.delete(`/reconciliation/sessions/${id}`),

  // Files
  addFile: (sessionId: string, data: {
    file_id: string
    source_type: string
    sheet_name?: string | null
    column_mappings?: Record<string, string> | null
  }) => client.post(`/reconciliation/sessions/${sessionId}/files`, data),

  // Classification
  classify: (sessionId: string, force = false) =>
    client.post(`/reconciliation/sessions/${sessionId}/classify`, { force }),

  // Transactions
  listTransactions: (sessionId: string, page = 1, limit = 50, filters?: TransactionFilters) =>
    client.get(`/reconciliation/sessions/${sessionId}/transactions`, {
      params: { page, limit, ...filters },
    }),

  updateTransaction: (sessionId: string, txnId: string, data: {
    vat_type?: string
    category?: string
    tin?: string
  }) => client.patch(`/reconciliation/sessions/${sessionId}/transactions/${txnId}`, data),

  // Anomalies
  detectAnomalies: (sessionId: string) =>
    client.post(`/reconciliation/sessions/${sessionId}/detect-anomalies`),

  listAnomalies: (sessionId: string, page = 1, limit = 50, status?: string) =>
    client.get(`/reconciliation/sessions/${sessionId}/anomalies`, {
      params: { page, limit, status },
    }),

  resolveAnomaly: (sessionId: string, anomalyId: string, data: {
    status: string
    resolution_note?: string
  }) => client.patch(`/reconciliation/sessions/${sessionId}/anomalies/${anomalyId}`, data),

  // Summary & Reconciliation
  getSummary: (sessionId: string) =>
    client.get(`/reconciliation/sessions/${sessionId}/summary`),

  reconcile: (sessionId: string, data?: {
    report_id?: string
    amount_tolerance?: number
    date_tolerance_days?: number
  }) => client.post(`/reconciliation/sessions/${sessionId}/reconcile`, data || {}),

  // Export
  exportCsv: (sessionId: string) =>
    client.get(`/reconciliation/sessions/${sessionId}/export`, { responseType: 'blob' }),
}
