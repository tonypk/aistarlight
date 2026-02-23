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

interface Correction {
  id: string
  report_type: string
  field_name: string | null
  old_value: string | null
  new_value: string | null
  reason: string | null
  created_at: string
}

const activeTab = ref<'preferences' | 'corrections'>('preferences')
const preferences = ref<Preference[]>([])
const corrections = ref<Correction[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [prefRes, corrRes] = await Promise.all([
      client.get('/memory/preferences'),
      client.get('/memory/corrections'),
    ])
    preferences.value = prefRes.data.data || []
    corrections.value = corrRes.data.data || []
  } catch {
    // No data yet
  } finally {
    loading.value = false
  }
})

async function deletePreference(reportType: string) {
  if (!confirm(`Delete preferences for ${reportType}?`)) return
  await client.delete(`/memory/preferences/${reportType}`)
  preferences.value = preferences.value.filter(p => p.report_type !== reportType)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="memory-view">
    <h2>AI Memory</h2>
    <p class="desc">View and manage what the AI remembers about your preferences</p>

    <div class="tabs">
      <button :class="{ active: activeTab === 'preferences' }" @click="activeTab = 'preferences'">
        Preferences ({{ preferences.length }})
      </button>
      <button :class="{ active: activeTab === 'corrections' }" @click="activeTab = 'corrections'">
        Corrections ({{ corrections.length }})
      </button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <!-- Preferences tab -->
    <template v-else-if="activeTab === 'preferences'">
      <div v-if="!preferences.length" class="empty">
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
              <span>{{ source }}</span> &rarr; <span>{{ target }}</span>
            </div>
          </div>

          <div v-if="Object.keys(pref.format_rules).length" class="section">
            <h4>Format Rules</h4>
            <pre>{{ JSON.stringify(pref.format_rules, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </template>

    <!-- Corrections tab -->
    <template v-else-if="activeTab === 'corrections'">
      <div v-if="!corrections.length" class="empty">
        <p>No correction history yet. Corrections are recorded when you modify AI-generated values.</p>
      </div>

      <div v-else class="corrections-list">
        <table>
          <thead>
            <tr>
              <th>Report Type</th>
              <th>Field</th>
              <th>Old Value</th>
              <th>New Value</th>
              <th>Reason</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in corrections" :key="c.id">
              <td>{{ c.report_type }}</td>
              <td>{{ c.field_name || '-' }}</td>
              <td class="val old">{{ c.old_value || '-' }}</td>
              <td class="val new">{{ c.new_value || '-' }}</td>
              <td>{{ c.reason || '-' }}</td>
              <td class="date">{{ formatDate(c.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.memory-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 20px; }

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.tabs button {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  color: #555;
}
.tabs button.active {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
}

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

.corrections-list {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 10px 12px; color: #888; font-size: 13px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; }
td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.val.old { color: #ef4444; }
.val.new { color: #059669; }
.date { color: #888; white-space: nowrap; }
</style>
