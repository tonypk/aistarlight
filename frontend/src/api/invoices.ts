import { client } from './client'

export interface InvoiceItem {
  id?: string
  invoice_id?: string
  line_number: number
  description: string
  quantity: number
  unit_price: number
  amount: number
  vat_type: string
  vat_rate: number
  vat_amount: number
  discount: number
  atc_code?: string
}

export interface Invoice {
  id: string
  company_id: string
  invoice_number: string
  invoice_type: string
  status: string
  customer_name: string
  customer_tin?: string
  customer_address?: string
  invoice_date: string
  due_date?: string
  subtotal: number
  vat_amount: number
  discount_amount: number
  total_amount: number
  vatable_sales: number
  vat_exempt_sales: number
  zero_rated_sales: number
  reference_number?: string
  notes?: string
  vendor_id?: string
  eis_submission_id?: string
  eis_status?: string
  eis_submitted_at?: string
  created_at: string
  updated_at: string
}

export interface InvoiceWithItems {
  invoice: Invoice
  items: InvoiceItem[]
}

export interface CreateInvoiceRequest {
  invoice_number?: string
  invoice_type: string
  customer_name: string
  customer_tin?: string
  customer_address?: string
  invoice_date: string
  due_date?: string
  reference_number?: string
  notes?: string
  vendor_id?: string
  items: {
    description: string
    quantity: number
    unit_price: number
    vat_type: string
    vat_rate?: number
    discount?: number
    atc_code?: string
  }[]
}

export const invoiceApi = {
  list: (page = 1, limit = 20, status?: string, type?: string) =>
    client.get('/invoices', { params: { page, limit, status, type } }),

  get: (id: string) =>
    client.get(`/invoices/${id}`),

  create: (data: CreateInvoiceRequest) =>
    client.post('/invoices', data),

  updateStatus: (id: string, status: string) =>
    client.patch(`/invoices/${id}/status`, { status }),

  delete: (id: string) =>
    client.delete(`/invoices/${id}`),

  exportEIS: (id: string) =>
    client.get(`/invoices/${id}/eis-export`, { responseType: 'blob' }),
}
