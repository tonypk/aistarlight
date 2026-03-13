import { client } from './client'

export interface CategorySummary {
  category: string
  count: number
  total: string
}

export interface VendorSummary {
  vendor: string
  count: number
  total: string
}

export interface MonthSummary {
  month: string
  count: number
  total: string
}

export interface IncomeExpenseSummary {
  type: string
  count: number
  total: string
}

export interface SpendingDashboard {
  by_category: CategorySummary[]
  by_vendor: VendorSummary[]
  by_month: MonthSummary[]
  income_expense: IncomeExpenseSummary[]
  period: { from: string; to: string }
}

export const spendingApi = {
  getDashboard: (from: string, to: string) =>
    client.get<{ data: SpendingDashboard }>('/spending/dashboard', { params: { from, to } }),
}
