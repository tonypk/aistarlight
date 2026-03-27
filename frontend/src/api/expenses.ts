import { client } from "./client";

// --- Expense Reports ---
export const expenseReportApi = {
  create: (data: { title: string; notes?: string; hr_payee_id?: string }) =>
    client.post("/expenses/reports", data),
  list: (params?: { status?: string; page?: number; limit?: number }) =>
    client.get("/expenses/reports", { params }),
  get: (id: string) => client.get(`/expenses/reports/${id}`),
  update: (id: string, data: { title: string; notes?: string }) =>
    client.put(`/expenses/reports/${id}`, data),
  delete: (id: string) => client.delete(`/expenses/reports/${id}`),
  submit: (id: string) => client.post(`/expenses/reports/${id}/submit`),
  revert: (id: string) => client.post(`/expenses/reports/${id}/revert`),
  approve: (id: string) => client.post(`/expenses/reports/${id}/approve`),
  reject: (id: string, data: { reason: string }) =>
    client.post(`/expenses/reports/${id}/reject`, data),
  markPaid: (id: string, data: { payment_reference?: string }) =>
    client.post(`/expenses/reports/${id}/mark-paid`, data),
};

// --- Expense Items ---
export const expenseItemApi = {
  add: (reportId: string, data: any) =>
    client.post(`/expenses/reports/${reportId}/items`, data),
  update: (id: string, data: any) =>
    client.put(`/expenses/items/${id}`, data),
  delete: (id: string) => client.delete(`/expenses/items/${id}`),
  uploadReceipt: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return client.post(`/expenses/items/${id}/receipt`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// --- Expense Approvals ---
export const expenseApprovalApi = {
  listPending: (params?: { page?: number; limit?: number }) =>
    client.get("/expenses/approvals", { params }),
};

// --- Finance Queue ---
export const expenseFinanceApi = {
  queue: (params?: { page?: number; limit?: number }) =>
    client.get("/expenses/finance/queue", { params }),
};

// --- Expense Policies ---
export const expensePolicyApi = {
  create: (data: any) => client.post("/expenses/policies", data),
  list: () => client.get("/expenses/policies"),
  get: (id: string) => client.get(`/expenses/policies/${id}`),
  update: (id: string, data: any) =>
    client.put(`/expenses/policies/${id}`, data),
  delete: (id: string) => client.delete(`/expenses/policies/${id}`),
};

// --- Expense Approvers ---
export const expenseApproverApi = {
  create: (data: any) => client.post("/expenses/approvers", data),
  list: () => client.get("/expenses/approvers"),
  update: (id: string, data: any) =>
    client.put(`/expenses/approvers/${id}`, data),
  delete: (id: string) => client.delete(`/expenses/approvers/${id}`),
};

// --- Expense Analytics ---
export const expenseAnalyticsApi = {
  get: (params?: { from?: string; to?: string }) =>
    client.get("/expenses/analytics", { params }),
};
