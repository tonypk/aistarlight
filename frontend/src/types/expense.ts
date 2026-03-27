export interface ExpensePolicy {
  id: string
  company_id: string
  name: string
  category: string
  max_amount: number | null
  requires_receipt_above: number | null
  auto_approve_below: number | null
  ai_auto_approve: boolean
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ExpenseReport {
  id: string
  company_id: string
  submitter_user_id: string
  hr_payee_id: string | null
  report_number: string
  title: string
  status: 'draft' | 'submitted' | 'pending_approval' | 'approved' | 'rejected' | 'paid'
  total_amount: number
  currency: string
  submitted_at: string | null
  ai_reviewed_at: string | null
  ai_risk_score: number | null
  ai_decision: string | null
  ai_decision_reason: string | null
  approver_user_id: string | null
  approved_at: string | null
  rejection_reason: string | null
  reviewer_user_id: string | null
  paid_at: string | null
  payment_reference: string | null
  notes: string | null
  created_at: string
  updated_at: string
  items?: ExpenseItem[]
  audit_log?: ExpenseAudit[]
}

export interface ExpenseItem {
  id: string
  expense_report_id: string
  category: string
  description: string
  amount: number
  currency: string
  merchant_name: string | null
  transaction_date: string
  receipt_url: string | null
  receipt_ocr_data: any | null
  ai_category_confidence: number | null
  gl_account_id: string | null
  policy_id: string | null
  created_at: string
  updated_at: string
}

export interface ExpenseApprover {
  id: string
  company_id: string
  department_name: string
  approver_user_id: string
  max_amount: number | null
  priority: number
  is_active: boolean
  approver_name: string
  approver_email: string
  created_at: string
  updated_at: string
}

export interface ExpenseAudit {
  id: string
  expense_report_id: string | null
  action: string
  actor_user_id: string | null
  actor_type: string
  details: any | null
  created_at: string
  actor_name: string
}

export interface ExpenseSpendSummary {
  approved_count: number
  paid_count: number
  pending_count: number
  total_approved: number
  total_paid: number
  total_pending: number
}

export interface SpendByCategory {
  category: string
  total_amount: number
  item_count: number
}

export interface SpendByDepartment {
  department: string
  total_amount: number
  report_count: number
}
