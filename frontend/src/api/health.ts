import { client } from './client'

export interface AIHealthStatus {
  ai_enabled: boolean
  provider: string
  model: string
  features: {
    chat: boolean
    classification: boolean
    column_mapping: boolean
    anomaly_detection: boolean
    knowledge_rag: boolean
  }
}

export const healthApi = {
  getAIHealth: () => client.get<{ data: AIHealthStatus }>('/health/ai'),
}
