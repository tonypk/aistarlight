<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { knowledgeApi } from '../api/knowledge'

interface KnowledgeEntry {
  id: string
  category: string
  source: string
  content: string
  has_embedding: boolean
  created_at: string
}

interface Stats {
  total: number
  with_embeddings: number
  categories: Record<string, number>
}

const entries = ref<KnowledgeEntry[]>([])
const stats = ref<Stats | null>(null)
const loading = ref(false)
const error = ref('')
const activeCategory = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    const [entriesRes, statsRes] = await Promise.all([
      knowledgeApi.list(),
      knowledgeApi.stats(),
    ])
    entries.value = entriesRes.data.data
    stats.value = statsRes.data.data
  } catch {
    error.value = 'Failed to load knowledge base.'
  } finally {
    loading.value = false
  }
})

async function filterByCategory(category: string | null) {
  activeCategory.value = category
  loading.value = true
  try {
    const res = await knowledgeApi.list(1, 50, category || undefined)
    entries.value = res.data.data
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="knowledge-view">
    <h2>Knowledge Base</h2>
    <p class="desc">Philippine tax regulations used by the AI assistant</p>

    <!-- Stats cards -->
    <div v-if="stats" class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total Entries</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.with_embeddings }}</div>
        <div class="stat-label">With Embeddings</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ Object.keys(stats.categories).length }}</div>
        <div class="stat-label">Categories</div>
      </div>
    </div>

    <!-- Category filter -->
    <div v-if="stats" class="category-filter">
      <button
        :class="{ active: activeCategory === null }"
        @click="filterByCategory(null)"
      >
        All ({{ stats.total }})
      </button>
      <button
        v-for="(count, cat) in stats.categories"
        :key="cat"
        :class="{ active: activeCategory === cat }"
        @click="filterByCategory(cat as string)"
      >
        {{ cat }} ({{ count }})
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-msg">{{ error }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading">Loading...</div>

    <!-- Entries list -->
    <div v-else class="entries">
      <div v-for="entry in entries" :key="entry.id" class="entry-card">
        <div class="entry-header">
          <span class="category-badge">{{ entry.category }}</span>
          <span class="source">{{ entry.source }}</span>
          <span v-if="entry.has_embedding" class="emb-badge">vector</span>
          <span v-else class="emb-badge no-emb">no vector</span>
        </div>
        <p class="entry-content">{{ entry.content }}</p>
        <div class="entry-footer">
          {{ formatDate(entry.created_at) }}
        </div>
      </div>

      <div v-if="!entries.length" class="empty">
        No knowledge entries found.
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge-view h2 { margin-bottom: 4px; }
.desc { color: #888; margin-bottom: 20px; }

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 24px;
  text-align: center;
  flex: 1;
}
.stat-value { font-size: 28px; font-weight: 700; color: #4f46e5; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }

.category-filter {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.category-filter button {
  padding: 6px 16px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: #555;
}
.category-filter button.active {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
}

.loading { text-align: center; padding: 32px; color: #888; }

.entries { display: flex; flex-direction: column; gap: 12px; }
.entry-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 20px;
}
.entry-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.category-badge {
  background: #eef2ff;
  color: #4f46e5;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.source {
  font-size: 13px;
  color: #888;
  flex: 1;
}
.emb-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #d1fae5;
  color: #065f46;
}
.emb-badge.no-emb {
  background: #fef3c7;
  color: #92400e;
}
.entry-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
.entry-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #aaa;
}
.empty { text-align: center; padding: 48px; color: #888; }
.error-msg { color: #ef4444; text-align: center; padding: 24px; }
</style>
