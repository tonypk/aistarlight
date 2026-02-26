/** Shared TypeScript interfaces for reconciliation feature. */

export interface SourceFileInfo {
  file_id: string;
  filename: string;
  file_type: string;
  sheet_name?: string | null;
  row_count: number;
  bank_name?: string | null;
}

export interface ReconciliationSession {
  id: string;
  period: string;
  status: "draft" | "classifying" | "reviewing" | "completed";
  report_id: string | null;
  source_files: SourceFileInfo[];
  summary: VatSummary | null;
  reconciliation_result: ReconciliationResult | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  source_type: "sales_record" | "purchase_record" | "bank_statement";
  source_file_id: string;
  row_index: number;
  date: string | null;
  description: string | null;
  amount: number;
  vat_amount: number;
  vat_type: VatType;
  category: Category;
  tin: string | null;
  confidence: number;
  classification_source: "ai" | "rule" | "user_override" | "auto_confirmed";
  match_group_id: string | null;
  match_status: "unmatched" | "matched" | "partial" | "manual";
  // Withholding tax fields
  ewt_rate: number | null;
  ewt_amount: number | null;
  atc_code: string | null;
  supplier_id: string | null;
}

export type VatType = "vatable" | "exempt" | "zero_rated" | "government";
export type Category = "goods" | "services" | "capital" | "imports" | "sale";
export type AnomalySeverity = "high" | "medium" | "low";
export type AnomalyStatus =
  | "open"
  | "acknowledged"
  | "resolved"
  | "false_positive";

export interface Anomaly {
  id: string;
  transaction_id: string | null;
  anomaly_type: string;
  severity: AnomalySeverity;
  description: string;
  details: Record<string, unknown> | null;
  status: AnomalyStatus;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_note: string | null;
  created_at: string;
}

export interface VatSummary {
  period: string;
  vatable_sales: string;
  sales_to_government: string;
  zero_rated_sales: string;
  vat_exempt_sales: string;
  total_sales: string;
  output_vat: string;
  output_vat_government: string;
  total_output_vat: string;
  input_vat_goods: string;
  input_vat_capital: string;
  input_vat_services: string;
  input_vat_imports: string;
  total_input_vat: string;
  net_vat: string;
  transaction_count: number;
  classification_stats: {
    by_vat_type: Record<string, number>;
    by_category: Record<string, number>;
  };
}

export interface ComparisonLine {
  line: string;
  label: string;
  computed: string;
  declared: string;
  difference: string;
  match: boolean;
}

export interface ReconciliationComparison {
  comparisons: ComparisonLine[];
  matched_lines: number;
  total_lines: number;
  total_difference: string;
  fully_matched: boolean;
}

export interface ReconciliationResult {
  session_id: string;
  period: string;
  summary: VatSummary;
  comparison: ReconciliationComparison | null;
  match_stats: {
    matched_pairs: number;
    unmatched_records: number;
    unmatched_bank: number;
    match_rate: number;
  };
  anomaly_count: number;
}

export interface TransactionFilters {
  vat_type?: VatType | null;
  category?: Category | null;
  source_type?: string | null;
  match_status?: string | null;
  min_confidence?: number | null;
  needs_review?: boolean | null;
  search?: string | null;
}
