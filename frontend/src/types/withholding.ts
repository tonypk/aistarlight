/** TypeScript interfaces for Withholding Tax feature. */

export interface Supplier {
  id: string
  tin: string
  name: string
  address: string | null
  supplier_type: 'individual' | 'corporation'
  default_ewt_rate: number | null
  default_atc_code: string | null
  is_vat_registered: boolean
  created_at: string
  updated_at: string
}

export interface SupplierCreateData {
  tin: string
  name: string
  address?: string
  supplier_type?: string
  default_ewt_rate?: number
  default_atc_code?: string
  is_vat_registered?: boolean
}

export interface SupplierUpdateData {
  tin?: string
  name?: string
  address?: string
  supplier_type?: string
  default_ewt_rate?: number
  default_atc_code?: string
  is_vat_registered?: boolean
}

export interface WithholdingCertificate {
  id: string
  supplier_id: string
  supplier_name: string | null
  session_id: string | null
  period: string
  quarter: string
  atc_code: string
  income_type: string
  income_amount: number
  ewt_rate: number
  tax_withheld: number
  status: 'draft' | 'generated' | 'sent'
  file_path: string | null
  created_at: string
}

export interface EwtSummary {
  period: string
  total_certificates: number
  total_income: number
  total_tax_withheld: number
}

export interface SawtEntry {
  supplier_tin: string
  supplier_name: string
  atc_code: string
  income_type: string
  income_amount: number
  ewt_rate: number
  tax_withheld: number
  quarter: string
  period: string
}

export interface SawtSummary {
  period: string
  entries: SawtEntry[]
  total_income: number
  total_tax_withheld: number
  total_entries: number
}

export interface EwtRate {
  atc_code: string
  description: string
  rate: number
  category: string
}
