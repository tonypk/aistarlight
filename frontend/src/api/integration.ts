import { client } from './client'

export interface IntegrationSource {
  id: string
  company_id: string
  source_system: string
  remote_company_id: number
  api_key_hash: string
  webhook_secret: string
  status: string
  last_event_at: string | null
  created_at: string
}

export interface IntegrationEvent {
  id: string
  company_id: string
  source_system: string
  event_id: string
  event_type: string
  payload: Record<string, unknown>
  status: string
  error_message: string | null
  processed_at: string | null
  created_at: string
}

export interface GLMappingRule {
  id: string
  company_id: string
  jurisdiction: string
  source_dimension: string
  source_value: string
  target_account_id: string
  debit_credit: string
  priority: number
  effective_from: string
  effective_to: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  account_number?: string
  account_name?: string
}

export interface CreateGLMappingRequest {
  jurisdiction: string
  source_dimension: string
  source_value: string
  target_account_id: string
  debit_credit: string
  priority?: number
  effective_from?: string
}

export interface UpdateGLMappingRequest {
  target_account_id: string
  debit_credit: string
  priority?: number
  effective_to?: string | null
  is_active?: boolean
}

export const integrationApi = {
  // Integration Sources
  listSources: () =>
    client.get('/integrations/sources'),

  getSource: (id: string) =>
    client.get(`/integrations/sources/${id}`),

  // Integration Events (inbox)
  listEvents: (page = 1, limit = 20) =>
    client.get('/integrations/events', { params: { page, limit } }),

  // GL Mapping Rules
  listMappings: (jurisdiction?: string) =>
    client.get('/gl-mappings', { params: { jurisdiction } }),

  getMapping: (id: string) =>
    client.get(`/gl-mappings/${id}`),

  createMapping: (data: CreateGLMappingRequest) =>
    client.post('/gl-mappings', data),

  updateMapping: (id: string, data: UpdateGLMappingRequest) =>
    client.put(`/gl-mappings/${id}`, data),

  deleteMapping: (id: string) =>
    client.delete(`/gl-mappings/${id}`),

  seedDefaults: (jurisdiction = 'PH') =>
    client.post(`/gl-mappings/seed?jurisdiction=${jurisdiction}`),
}
