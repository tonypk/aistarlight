import { client } from "./client";

export interface OrgInfo {
  id: string;
  name: string;
  plan: string;
  max_companies: number;
  max_users: number;
}

export interface CompanySummary {
  id: string;
  company_name: string;
  tin_number: string;
  jurisdiction: string;
  plan: string;
  report_count: number;
  draft_count: number;
  vendor_count: number;
  last_check_at: string | null;
  cas_pass: boolean | null;
  revenue: string;
  expenses: string;
  net_income: string;
}

export interface OrgFinanceTotals {
  total_revenue: string;
  total_expenses: string;
  total_net_income: string;
  total_assets: string;
}

export interface OrgDashboardData {
  organization: OrgInfo;
  companies: CompanySummary[];
  total_finance: OrgFinanceTotals;
  company_count: number;
  member_count: number;
  compliance_all_pass: boolean;
}

export interface OrgMember {
  organization_id: string;
  user_id: string;
  role: string;
  joined_at: string;
  email: string;
  full_name: string | null;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  max_companies: number;
  max_users: number;
  is_active: boolean;
  created_at: string;
}

export interface CompanyComplianceResult {
  company_id: string;
  company_name: string;
  pass: boolean;
  score: number;
  error?: string;
}

export interface BatchComplianceResult {
  results: CompanyComplianceResult[];
  all_pass: boolean;
}

export const orgApi = {
  list: () => client.get<{ data: Organization[] }>("/orgs"),

  get: (orgId: string) =>
    client.get<{ data: Organization }>(`/orgs/${orgId}`),

  create: (data: { name: string; slug?: string }) =>
    client.post<{ data: Organization }>("/orgs", data),

  update: (orgId: string, data: { name: string; slug: string }) =>
    client.put<{ data: Organization }>(`/orgs/${orgId}`, data),

  dashboard: (orgId: string) =>
    client.get<{ data: OrgDashboardData }>(`/orgs/${orgId}/dashboard`),

  listMembers: (orgId: string) =>
    client.get<{ data: OrgMember[] }>(`/orgs/${orgId}/members`),

  addMember: (orgId: string, userId: string, role: string) =>
    client.post(`/orgs/${orgId}/members`, { user_id: userId, role }),

  updateMemberRole: (orgId: string, userId: string, role: string) =>
    client.patch(`/orgs/${orgId}/members/${userId}`, { role }),

  removeMember: (orgId: string, userId: string) =>
    client.delete(`/orgs/${orgId}/members/${userId}`),

  listCompanies: (orgId: string) =>
    client.get<{ data: CompanySummary[] }>(`/orgs/${orgId}/companies`),

  batchComplianceCheck: (orgId: string) =>
    client.post<{ data: BatchComplianceResult }>(
      `/orgs/${orgId}/batch/compliance-check`
    ),
};
