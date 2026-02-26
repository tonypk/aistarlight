import { client } from "./client";

export interface FixSuggestion {
  field: string;
  current_value: string;
  suggested_value: string;
  reason: string;
}

export const complianceApi = {
  validate: (reportId: string) => client.post(`/reports/${reportId}/validate`),
  getValidation: (reportId: string) =>
    client.get(`/reports/${reportId}/validation`),
  getValidationHistory: (reportId: string) =>
    client.get(`/reports/${reportId}/validation/history`),
  suggestFixes: (reportId: string) =>
    client.get(`/compliance/reports/${reportId}/suggest-fixes`),
  autoFix: (reportId: string, suggestions: FixSuggestion[]) =>
    client.post(`/compliance/reports/${reportId}/auto-fix`, { suggestions }),
};
