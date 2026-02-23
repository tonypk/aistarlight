import { client } from './client'

export const knowledgeApi = {
  list: (page = 1, limit = 50, category?: string) =>
    client.get('/knowledge', { params: { page, limit, category: category || undefined } }),
  stats: () => client.get('/knowledge/stats'),
}
