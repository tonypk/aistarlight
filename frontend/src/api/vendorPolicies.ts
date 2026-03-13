import { client } from './client'

export interface VendorPolicy {
  id: string
  company_id: string
  vendor_normalized: string
  aliases: string[]
  default_category: string
  account_code: string
  tax_code: string
  department: string
  project: string
  usage_count: number
  accept_count: number
  correction_count: number
  confidence_score: number
}

export interface RuleSuggestion {
  vendor_normalized: string
  correction_count: number
  accept_count: number
  confidence_score: number
  default_category: string
  account_code: string
  tax_code: string
  message: string
}

export interface UpdateVendorDefaults {
  category: string
  account_code: string
  tax_code: string
  department: string
  project: string
}

export const vendorPoliciesApi = {
  list: (page = 1, limit = 50) =>
    client.get('/vendor-policies', { params: { page, limit } }),

  get: (id: string) =>
    client.get(`/vendor-policies/${id}`),

  update: (id: string, data: UpdateVendorDefaults) =>
    client.put(`/vendor-policies/${id}`, data),

  delete: (id: string) =>
    client.delete(`/vendor-policies/${id}`),

  suggestions: () =>
    client.get('/vendor-policies/suggestions'),

  promote: (id: string) =>
    client.post(`/vendor-policies/${id}/promote`),
}
