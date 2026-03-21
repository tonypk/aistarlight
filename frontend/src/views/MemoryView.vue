<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { client } from '../api/client'

const { t } = useI18n()

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
  if (!confirm(t('memory.deleteConfirm', { reportType }))) return
  try {
    await client.delete(`/memory/preferences/${reportType}`)
    preferences.value = preferences.value.filter(p => p.report_type !== reportType)
  } catch {
    alert(t('memory.deleteFailed'))
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="memory-view">
    <h2>{{ t('memory.title') }}</h2>
    <p class="desc">{{ t('memory.desc') }}</p>

    <div class="tabs">
      <button :class="{ active: activeTab === 'preferences' }" @click="activeTab = 'preferences'">
        {{ t('memory.preferencesTab', { count: preferences.length }) }}
      </button>
      <button :class="{ active: activeTab === 'corrections' }" @click="activeTab = 'corrections'">
        {{ t('memory.correctionsTab', { count: corrections.length }) }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ t('memory.loading') }}</div>

    <!-- Preferences tab -->
    <template v-else-if="activeTab === 'preferences'">
      <div v-if="!preferences.length" class="empty">
        <p>{{ t('memory.emptyPreferences') }}</p>
      </div>

      <div v-else class="pref-list">
        <div v-for="pref in preferences" :key="pref.id" class="pref-card">
          <div class="pref-header">
            <h3>{{ pref.report_type }}</h3>
            <button class="del-btn" @click="deletePreference(pref.report_type)">{{ t('common.delete') }}</button>
          </div>

          <div v-if="Object.keys(pref.column_mappings).length" class="section">
            <h4>{{ t('memory.columnMappings') }}</h4>
            <div v-for="(target, source) in pref.column_mappings" :key="source" class="mapping-item">
              <span>{{ source }}</span> &rarr; <span>{{ target }}</span>
            </div>
          </div>

          <div v-if="Object.keys(pref.format_rules).length" class="section">
            <h4>{{ t('memory.formatRules') }}</h4>
            <pre>{{ JSON.stringify(pref.format_rules, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </template>

    <!-- Corrections tab -->
    <template v-else-if="activeTab === 'corrections'">
      <div v-if="!corrections.length" class="empty">
        <p>{{ t('memory.emptyCorrections') }}</p>
      </div>

      <div v-else class="corrections-list">
        <table>
          <thead>
            <tr>
              <th>{{ t('memory.thReportType') }}</th>
              <th>{{ t('memory.thField') }}</th>
              <th>{{ t('memory.thOldValue') }}</th>
              <th>{{ t('memory.thNewValue') }}</th>
              <th>{{ t('memory.thReason') }}</th>
              <th>{{ t('memory.thDate') }}</th>
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
.desc { color: var(--text-muted); margin-bottom: 20px; }

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.tabs button {
  padding: 8px 20px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
}
.tabs button.active {
  background: var(--brand-primary);
  color: #fff;
  border-color: var(--brand-primary);
}

.loading, .empty { text-align: center; padding: 48px; color: var(--text-muted); }

.pref-card {
  background: var(--bg-surface);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-default);
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
.section h4 { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.mapping-item { padding: 4px 0; font-family: monospace; font-size: 13px; }
pre { background: var(--bg-surface-alt); padding: 12px; border-radius: 6px; font-size: 12px; }

.corrections-list {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-default);
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 10px 12px; color: var(--text-muted); font-size: 13px; border-bottom: 1px solid var(--border-default); background: var(--bg-surface-alt); }
td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.val.old { color: #ef4444; }
.val.new { color: #059669; }
.date { color: var(--text-muted); white-space: nowrap; }
</style>
