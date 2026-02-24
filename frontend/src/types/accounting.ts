// Chart of Accounts
export interface Account {
  id: string
  company_id: string
  account_number: string
  name: string
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
  sub_type: string
  normal_balance: 'debit' | 'credit'
  description: string
  is_system: boolean
  parent_id: string | null
  qbo_account_id: string | null
  created_at: string
  updated_at: string
}

// Journal Entries
export interface JournalLine {
  id: string
  journal_entry_id: string
  account_id: string
  account_number?: string
  account_name?: string
  description: string | null
  debit: string
  credit: string
}

export interface JournalEntry {
  id: string
  company_id: string
  entry_number: number
  entry_date: string
  reference: string | null
  description: string | null
  status: 'draft' | 'posted' | 'reversed'
  source_type: string | null
  source_id: string | null
  posted_at: string | null
  posted_by: string | null
  created_by: string
  lines: JournalLine[]
  created_at: string
  updated_at: string
}

// General Ledger
export interface TrialBalanceRow {
  account_id: string
  account_number: string
  account_name: string
  account_type: string
  normal_balance: string
  total_debit: string
  total_credit: string
  balance: string
}

export interface LedgerEntry {
  journal_entry_id: string
  entry_number: number
  entry_date: string
  description: string | null
  reference: string | null
  debit: string
  credit: string
  running_balance: string
}

// Financial Statements
export interface AccountBalance {
  account_id: string
  account_code: string
  account_name: string
  balance: string
  normal_balance: string
}

export interface BalanceSheet {
  as_of_date: string
  assets: AccountBalance[]
  liabilities: AccountBalance[]
  equity: AccountBalance[]
  total_assets: string
  total_liabilities: string
  total_equity: string
  retained_earnings: string
  is_balanced: boolean
}

export interface IncomeStatement {
  period_start: string
  period_end: string
  revenue: AccountBalance[]
  cogs: AccountBalance[]
  expenses: AccountBalance[]
  total_revenue: string
  total_cogs: string
  gross_profit: string
  total_expenses: string
  net_income: string
}

// Tax Bridge
export interface TaxCalculationResult {
  form_type: string
  period_start: string
  period_end: string
  result: Record<string, string>
}

// Accounting Period
export interface AccountingPeriod {
  id: string
  company_id: string
  name: string
  start_date: string
  end_date: string
  status: 'open' | 'closed' | 'locked'
  created_at: string
}
