import { client } from './client'

// --- Chart of Accounts ---
export const accountsApi = {
  list: (params?: { page?: number; limit?: number }) =>
    client.get('/accounts', { params }),
  get: (id: string) =>
    client.get(`/accounts/${id}`),
  create: (data: { account_number: string; name: string; account_type: string; sub_type?: string; normal_balance: string; description?: string }) =>
    client.post('/accounts', data),
  update: (id: string, data: { name?: string; description?: string; sub_type?: string }) =>
    client.put(`/accounts/${id}`, data),
  delete: (id: string) =>
    client.delete(`/accounts/${id}`),
  seed: () =>
    client.post('/accounts/seed'),
  balance: (id: string, params?: { as_of?: string }) =>
    client.get(`/accounts/${id}/balance`, { params }),
}

// --- Journal Entries ---
export const journalApi = {
  list: (params?: { page?: number; limit?: number; status?: string }) =>
    client.get('/journal-entries', { params }),
  get: (id: string) =>
    client.get(`/journal-entries/${id}`),
  create: (data: { entry_date: string; reference?: string; description?: string; lines: { account_id: string; description?: string; debit: string; credit: string }[] }) =>
    client.post('/journal-entries', data),
  post: (id: string) =>
    client.post(`/journal-entries/${id}/post`),
  reverse: (id: string) =>
    client.post(`/journal-entries/${id}/reverse`),
}

// --- General Ledger ---
export const glApi = {
  trialBalance: (params?: { as_of?: string }) =>
    client.get('/gl/trial-balance', { params }),
  accountLedger: (accountId: string, params?: { from?: string; to?: string; page?: number; limit?: number }) =>
    client.get(`/gl/account/${accountId}/ledger`, { params }),
}

// --- Bridge 1: Receipt → Transaction ---
export const receiptBridgeApi = {
  convert: (batchId: string, sessionId: string) =>
    client.post(`/receipts/batches/${batchId}/convert`, { session_id: sessionId }),
}

// --- Bridge 2: Transaction → Journal Entry ---
export const journalBridgeApi = {
  generateFromSession: (sessionId: string) =>
    client.post('/journals/generate', { session_id: sessionId }),
  generateFromTransactions: (transactionIds: string[]) =>
    client.post('/journals/generate', { transaction_ids: transactionIds }),
}

// --- Bridge 3: GL → Financial Statements ---
export const statementsApi = {
  balanceSheet: (params?: { as_of?: string }) =>
    client.get('/statements/balance-sheet', { params }),
  incomeStatement: (params: { from: string; to: string }) =>
    client.get('/statements/income-statement', { params }),
}

// --- Bridge 4: GL → Tax Engine ---
export const taxBridgeApi = {
  calculate: (data: { form_type: string; period_start: string; period_end: string }) =>
    client.post('/tax/calculate', data),
}

// --- Bridge 5: Tax → eBIRForms Export ---
export const taxExportApi = {
  exportDAT: (formType: string, period: string) =>
    client.get('/tax/export', {
      params: { form_type: formType, period },
      responseType: 'blob',
    }),
}

// --- Accounting Periods ---
export const periodsApi = {
  list: () =>
    client.get('/accounting-periods'),
  create: (data: { name: string; start_date: string; end_date: string }) =>
    client.post('/accounting-periods', data),
  generate: (data: { year: number }) =>
    client.post('/accounting-periods/generate', data),
  close: (id: string) =>
    client.post(`/accounting-periods/${id}/close`),
  reopen: (id: string) =>
    client.post(`/accounting-periods/${id}/reopen`),
}
