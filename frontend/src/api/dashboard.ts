import { client } from "./client";

export interface MonthlyTrend {
  month: string;
  total_reports: number;
  filed_count: number;
  draft_count: number;
}

export interface ActivityItem {
  id: string;
  type: string;
  description: string;
  created_at: string;
}

export interface MonthlyPLPoint {
  month: string;
  revenue: string;
  expenses: string;
  net: string;
}

export interface FinancialSummary {
  revenue: string;
  expenses: string;
  net_income: string;
  gross_profit: string;
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  cash_balance: string;
  accounts_receivable: string;
  accounts_payable: string;
  monthly_pl: MonthlyPLPoint[];
}

export const dashboardApi = {
  getTrends(months: number = 6) {
    return client.get("/dashboard/trends", { params: { months } });
  },

  getActivity(limit: number = 10) {
    return client.get("/dashboard/activity", { params: { limit } });
  },

  getFinancialSummary() {
    return client.get("/dashboard/financial-summary");
  },
};
