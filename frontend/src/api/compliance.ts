import { client } from './client'

export const complianceApi = {
  validate: (reportId: string) => client.post(`/reports/${reportId}/validate`),
  getValidation: (reportId: string) => client.get(`/reports/${reportId}/validation`),
  getValidationHistory: (reportId: string) => client.get(`/reports/${reportId}/validation/history`),
}
