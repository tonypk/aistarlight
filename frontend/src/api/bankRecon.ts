import { client } from './client'

export interface SourceFileInfo {
  filename: string
  file_type: string
  format_detected: boolean
  bank_name: string | null
  row_count: number
}

export interface MatchPair {
  match_group_id: string
  record_id: string
  bank_id: string
  record_amount: number
  bank_amount: number
  date_diff_days: number | null
}

export interface UnmatchedEntry {
  id: string
  amount: number
  date: string | null
  description: string | null
}

export interface MatchResult {
  matched_pairs: MatchPair[]
  unmatched_records: UnmatchedEntry[]
  unmatched_bank: UnmatchedEntry[]
  match_rate: number
  total_records: number
  total_bank_entries: number
}

export interface AISuggestion {
  unmatched_entry_index: number
  suggested_record_id: string | null
  confidence: number
  explanation: string
  category: string
  status: string
}

export interface AIExplanation {
  entry_index: number
  entry_type: string
  mismatch_type: string
  explanation: string
  recommended_action: string
}

export interface BankReconBatch {
  id: string
  tenant_id: string
  created_by: string
  session_id: string | null
  status: string
  source_files: SourceFileInfo[] | null
  total_entries: number
  parse_summary: Record<string, unknown> | null
  match_result: MatchResult | null
  ai_suggestions: AISuggestion[] | null
  ai_explanations: AIExplanation[] | null
  amount_tolerance: number
  date_tolerance_days: number
  period: string
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface BankReconBatchListItem {
  id: string
  status: string
  period: string
  total_entries: number
  source_files: SourceFileInfo[] | null
  match_rate: number | null
  created_at: string
}

export const bankReconApi = {
  async process(formData: FormData) {
    const { data } = await client.post('/bank-recon/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    return data
  },

  async listBatches(page = 1, limit = 20) {
    const { data } = await client.get('/bank-recon/batches', {
      params: { page, limit },
    })
    return data
  },

  async getBatch(batchId: string) {
    const { data } = await client.get(`/bank-recon/batches/${batchId}`)
    return data
  },

  async acceptSuggestion(batchId: string, suggestionIndex: number) {
    const { data } = await client.post(
      `/bank-recon/batches/${batchId}/accept-suggestion`,
      { suggestion_index: suggestionIndex }
    )
    return data
  },

  async rejectSuggestion(batchId: string, suggestionIndex: number) {
    const { data } = await client.post(
      `/bank-recon/batches/${batchId}/reject-suggestion`,
      { suggestion_index: suggestionIndex }
    )
    return data
  },

  async rerunAnalysis(batchId: string) {
    const { data } = await client.post(
      `/bank-recon/batches/${batchId}/rerun-analysis`
    )
    return data
  },
}
