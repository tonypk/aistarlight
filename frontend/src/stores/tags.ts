import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tagsApi } from '../api/tags'
import type { Tag, CreateTagData, UpdateTagData } from '../api/tags'

export const useTagStore = defineStore('tags', () => {
  const tags = ref<Tag[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchTags(page = 1, limit = 50, search?: string) {
    loading.value = true
    try {
      const res = await tagsApi.list(page, limit, search)
      tags.value = res.data.data || []
      total.value = res.data.meta?.total ?? tags.value.length
    } finally {
      loading.value = false
    }
  }

  async function createTag(data: CreateTagData) {
    const res = await tagsApi.create(data)
    const created = res.data.data as Tag
    tags.value = [created, ...tags.value]
    return created
  }

  async function updateTag(id: string, data: UpdateTagData) {
    const res = await tagsApi.update(id, data)
    const updated = res.data.data as Tag
    tags.value = tags.value.map(t => t.id === id ? updated : t)
    return updated
  }

  async function deleteTag(id: string) {
    await tagsApi.delete(id)
    tags.value = tags.value.filter(t => t.id !== id)
  }

  async function getTransactionTags(transactionId: string): Promise<Tag[]> {
    const res = await tagsApi.getTransactionTags(transactionId)
    return res.data.data || []
  }

  async function setTransactionTags(transactionId: string, tagIds: string[]) {
    const res = await tagsApi.setTransactionTags(transactionId, tagIds)
    return res.data.data as Tag[]
  }

  return {
    tags,
    total,
    loading,
    fetchTags,
    createTag,
    updateTag,
    deleteTag,
    getTransactionTags,
    setTransactionTags,
  }
})
