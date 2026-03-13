import { client } from './client'

export interface ApprovalSettings {
  id?: string
  company_id?: string
  is_enabled: boolean
  amount_threshold: number
  new_vendor_receipts: number
  risk_flags_require_approval: boolean
  approver_user_id?: string | null
}

export interface ReceiptApproval {
  id: string
  batch_id: string
  company_id: string
  status: string
  trigger_reason: string
  requested_by: { Valid: boolean; Bytes?: string } | null
  approved_by: { Valid: boolean; Bytes?: string } | null
  notes: string | null
  created_at: string
  updated_at: string
  results?: any
  total_images?: number
  period?: string
  batch_created_at?: string
}

export const approvalsApi = {
  getSettings: () =>
    client.get<{ data: ApprovalSettings }>('/approvals/settings'),

  updateSettings: (settings: Partial<ApprovalSettings>) =>
    client.put<{ data: ApprovalSettings }>('/approvals/settings', settings),

  listPending: (page = 1, limit = 20) =>
    client.get<{ data: ReceiptApproval[]; meta: { total: number } }>('/approvals/pending', {
      params: { page, limit },
    }),

  listAll: (page = 1, limit = 20) =>
    client.get<{ data: ReceiptApproval[]; meta: { total: number } }>('/approvals', {
      params: { page, limit },
    }),

  approve: (id: string, notes?: string) =>
    client.post<{ data: ReceiptApproval }>(`/approvals/${id}/approve`, { notes }),

  reject: (id: string, notes?: string) =>
    client.post<{ data: ReceiptApproval }>(`/approvals/${id}/reject`, { notes }),
}
