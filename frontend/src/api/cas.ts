import { client } from "./client";

export interface ComplianceResult {
  overall_pass: boolean;
  sequential_numbering_ok: boolean;
  hash_chain_intact: boolean;
  double_entry_balanced: boolean;
  periods_properly_closed: boolean;
  audit_trail_complete: boolean;
  subsidiary_ledgers_ok: boolean;
  details: Record<string, unknown>;
}

export interface ComplianceCheckSummary {
  id: string;
  company_id: string;
  check_date: string;
  overall_pass: boolean;
  sequential_numbering_ok: boolean;
  hash_chain_intact: boolean;
  double_entry_balanced: boolean;
  periods_properly_closed: boolean;
  audit_trail_complete: boolean;
  subsidiary_ledgers_ok: boolean;
}

export interface SubsidiaryLedgerEntry {
  entry_id: string;
  entry_number?: number;
  company_seq_no?: number;
  entry_date: string;
  entry_description?: string;
  journal_book?: string;
  line_id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  debit: string;
  credit: string;
  line_description?: string;
  tax_code?: string;
  tax_amount: string;
}

export const casApi = {
  runCheck: () => client.post<{ data: ComplianceResult }>("/cas/check"),
  getLatest: () => client.get<{ data: ComplianceResult }>("/cas/latest"),
  listChecks: (params?: { limit?: number; offset?: number }) =>
    client.get<{ data: ComplianceCheckSummary[] }>("/cas/checks", { params }),
  getSubsidiaryLedger: (params: {
    book: string;
    from?: string;
    to?: string;
  }) =>
    client.get<{ data: SubsidiaryLedgerEntry[] }>("/cas/subsidiary-ledger", {
      params,
    }),
};
