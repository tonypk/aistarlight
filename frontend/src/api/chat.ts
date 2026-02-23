import { client } from './client'

export interface ChatMessage {
  content: string
  context?: Record<string, unknown>
}

export const chatApi = {
  send: (data: ChatMessage) => client.post('/chat/message', data),
  history: (page = 1, limit = 50) => client.get('/chat/history', { params: { page, limit } }),
}
