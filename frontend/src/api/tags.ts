import { client } from './client'

export interface Tag {
  id: string
  company_id: string
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface CreateTagData {
  name: string
  color: string
}

export interface UpdateTagData {
  name: string
  color: string
}

export const tagsApi = {
  list: (page = 1, limit = 50, search?: string) =>
    client.get('/tags', { params: { page, limit, search } }),

  create: (data: CreateTagData) =>
    client.post('/tags', data),

  update: (id: string, data: UpdateTagData) =>
    client.put(`/tags/${id}`, data),

  delete: (id: string) =>
    client.delete(`/tags/${id}`),

  getTransactionTags: (transactionId: string) =>
    client.get(`/transactions/${transactionId}/tags`),

  setTransactionTags: (transactionId: string, tagIds: string[]) =>
    client.put(`/transactions/${transactionId}/tags`, { tag_ids: tagIds }),
}
