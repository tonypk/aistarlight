/** TypeScript interfaces for correction tracking and compliance validation. */

export interface Correction {
  id: string
  entity_type: 'transaction_classification' | 'report_field' | 'ewt_classification'
  entity_id: string
  field_name: string
  old_value: string | null
  new_value: string
  reason: string | null
  context_data: Record<string, unknown> | null
  created_at: string
  user_id: string
}

export interface CorrectionCreate {
  entity_type: string
  entity_id: string
  field_name: string
  old_value?: string | null
  new_value: string
  reason?: string
}

export interface CorrectionStats {
  total_corrections: number
  by_field: { field_name: string; new_value: string; entity_type: string; count: number }[]
  by_entity_type: Record<string, number>
}

export interface CorrectionRule {
  id: string
  rule_type: string
  match_criteria: Record<string, unknown>
  correction_field: string
  correction_value: string
  confidence: number
  source_correction_count: number
  is_active: boolean
  created_at: string
}

export interface CheckResult {
  check_id: string
  check_name: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  passed: boolean
  message: string
}

export interface RagFinding {
  finding: string
  severity: 'high' | 'medium' | 'low'
  regulation_reference: string
}

export interface ValidationResult {
  id: string
  report_id: string
  overall_score: number
  check_results: CheckResult[]
  rag_findings: RagFinding[] | null
  validated_at: string
}
