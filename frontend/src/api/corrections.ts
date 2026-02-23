import { client } from './client'
import type { CorrectionCreate } from '@/types/correction'

export const correctionsApi = {
  create: (data: CorrectionCreate) => client.post('/corrections', data),
  list: (params?: { entity_type?: string; field_name?: string; since?: string; page?: number; limit?: number }) =>
    client.get('/corrections', { params }),
  stats: () => client.get('/corrections/stats'),
  entityHistory: (entityType: string, entityId: string) =>
    client.get(`/corrections/entity/${entityType}/${entityId}`),
  // Learning endpoints
  learningStats: () => client.get('/corrections/learning/stats'),
  analyze: () => client.post('/corrections/learning/analyze'),
  rules: () => client.get('/corrections/rules'),
  updateRule: (ruleId: string, data: { is_active: boolean }) =>
    client.patch(`/corrections/rules/${ruleId}`, data),
}
