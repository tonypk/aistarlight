// Chart of Accounts
export interface Account {
  id: string;
  company_id: string;
  account_number: string;
  name: string;
  account_type: "asset" | "liability" | "equity" | "revenue" | "expense";
  sub_type: string;
  normal_balance: "debit" | "credit";
  description: string;
  is_system: boolean;
  parent_id: string | null;
  qbo_account_id: string | null;
  created_at: string;
  updated_at: string;
}

// Journal Entries
export interface JournalLine {
  id: string;
  journal_entry_id: string;
  account_id: string;
  account_number?: string;
  account_name?: string;
  description: string | null;
  debit: string;
  credit: string;
}

export interface JournalEntry {
  id: string;
  company_id: string;
  entry_number: number;
  entry_date: string;
  reference: string | null;
  description: string | null;
  status: "draft" | "posted" | "reversed";
  source_type: string | null;
  source_id: string | null;
  posted_at: string | null;
  posted_by: string | null;
  created_by: string;
  lines: JournalLine[];
  created_at: string;
  updated_at: string;
}

// General Ledger
export interface TrialBalanceRow {
  account_id: string;
  account_number: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  total_debit: string;
  total_credit: string;
  balance: string;
}

export interface LedgerEntry {
  journal_entry_id: string;
  entry_number: number;
  entry_date: string;
  description: string | null;
  reference: string | null;
  debit: string;
  credit: string;
  running_balance: string;
}

// Financial Statements
export interface AccountBalance {
  account_id: string;
  account_code: string;
  account_name: string;
  sub_type?: string;
  balance: string;
  normal_balance: string;
  prior_balance?: string;
  change?: string;
}

export interface AccountGroup {
  group_name: string;
  accounts: AccountBalance[];
  total: string;
  prior_total?: string;
}

export interface BalanceSheet {
  as_of_date: string;
  assets: AccountGroup[];
  liabilities: AccountGroup[];
  equity: AccountGroup[];
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  retained_earnings: string;
  is_balanced: boolean;
  // Comparative
  prior_as_of_date?: string;
  prior_total_assets?: string;
  prior_total_liab?: string;
  prior_total_equity?: string;
  prior_retained_earn?: string;
}

export interface IncomeStatement {
  period_start: string;
  period_end: string;
  revenue: AccountBalance[];
  cogs: AccountBalance[];
  expenses: AccountBalance[];
  total_revenue: string;
  total_cogs: string;
  gross_profit: string;
  total_expenses: string;
  net_income: string;
  // Comparative
  prior_period_start?: string;
  prior_period_end?: string;
  prior_revenue?: string;
  prior_cogs?: string;
  prior_gross_profit?: string;
  prior_expenses?: string;
  prior_net_income?: string;
}

export interface CashFlowStatement {
  period_start: string;
  period_end: string;
  net_income: string;
  depreciation_amort: string;
  working_capital_changes: AccountBalance[];
  operating_total: string;
  investing_items: AccountBalance[];
  investing_total: string;
  financing_items: AccountBalance[];
  financing_total: string;
  net_change: string;
  beginning_cash: string;
  ending_cash: string;
}

// Tax Bridge
export interface TaxCalculationResult {
  form_type: string;
  period_start: string;
  period_end: string;
  result: Record<string, string>;
}

// Accounting Period
export interface AccountingPeriod {
  id: string;
  company_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: "open" | "closed" | "locked";
  created_at: string;
}
