<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { client } from '../api/client'

interface Preference {
  id: string
  report_type: string
  column_mappings: Record<string, string>
  format_rules: Record<string, string>
  auto_fill_rules: Record<string, string>
}

const preferences = ref<Preference[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await client.get('/memory/preferences')
    preferences.value = res.data.data || []
  } catch {
    // No preferences yet
  } finally {
    loading.value = false
  }
})

async function deletePreference(reportType: string) {
  if (!confirm(`Delete preferences for ${reportType}?`)) return
  await client.delete(`/memory/preferences/${reportType}`)
  preferences.value = preferences.value.filter(p => p.report_type !== reportType)
}
</script>

<template>
  <div class="memory-view">
    <h2>AI Memory</h2>
    <p class="desc">View and manage what the AI remembers about your preferences</p>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="!preferences.length" class="empty">
      <p>No saved preferences yet. The AI will learn your preferences as you use it.</p>
    </div>

    <div v-else class="pref-list">
      <div v-for="pref in preferences" :key="pref.id" class="pref-card">
        <div class="pref-header">
          <h3>{{ pref.report_type }}</h3>
          <button class="del-btn" @click="deletePreference(pref.report_type)">Delete</button>
        </div>

        <div v-if="Object.keys(pref.column_mappings).length" class="section">
          <h4>Column Mappings</h4>
          <div v-for="(target, source) in pref.column_mappings" :key="source" class="mapping-item">
            <span>{{ source }}</span> → <span>{{ target }}</span>
          </div>
        </div>

        <div v-if="Object.keys(pref.format_rules).length" class="section">
          <h4>Format Rules</h4>
          <pre>{{ JSON.stringify(pref.format_rules, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.memory-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 24px; }
.loading, .empty { text-align: center; padding: 48px; color: #888; }
.pref-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}
.pref-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.del-btn {
  padding: 6px 16px;
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
  border-radius: 6px;
  cursor: pointer;
}
.section { margin-bottom: 12px; }
.section h4 { font-size: 13px; color: #888; margin-bottom: 8px; }
.mapping-item { padding: 4px 0; font-family: monospace; font-size: 13px; }
pre { background: #f9fafb; padding: 12px; border-radius: 6px; font-size: 12px; }
</style>
