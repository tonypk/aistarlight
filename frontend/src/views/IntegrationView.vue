<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { integrationApi, type IntegrationSource, type IntegrationEvent } from '../api/integration'
import { useToastStore } from '@/stores/toast'

const { t } = useI18n()
const toast = useToastStore()

const sources = ref<IntegrationSource[]>([])
const events = ref<IntegrationEvent[]>([])
const loading = ref(false)
const page = ref(1)
const expandedEvent = ref<string | null>(null)
const showAddSource = ref(false)
const addLoading = ref(false)
const newSource = ref({ remote_company_id: '', webhook_secret: '' })

const statusBadge = (status: string) => {
  switch (status) {
    case 'processed': return 'badge-success'
    case 'received': return 'badge-info'
    case 'failed': return 'badge-danger'
    default: return 'badge-secondary'
  }
}

const eventTypeLabel = (type: string) => {
  switch (type) {
    case 'payroll.run.completed': return t('integration.payrollCompleted')
    case 'payroll.run.reversed': return t('integration.payrollReversed')
    case 'employee.upserted': return t('integration.employeeSynced')
    case 'employee.terminated': return t('integration.employeeTerminated')
    default: return type
  }
}

const formatDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString()
}

async function fetchData() {
  loading.value = true
  try {
    const [srcRes, evtRes] = await Promise.all([
      integrationApi.listSources(),
      integrationApi.listEvents(page.value, 50),
    ])
    sources.value = srcRes.data.data || []
    events.value = evtRes.data.data || []
  } catch (e) {
    toast.error(t('integration.loadFailed'))
  } finally {
    loading.value = false
  }
}

function togglePayload(id: string) {
  expandedEvent.value = expandedEvent.value === id ? null : id
}

const stats = computed(() => {
  const total = events.value.length
  const processed = events.value.filter(e => e.status === 'processed').length
  const failed = events.value.filter(e => e.status === 'failed').length
  const pending = events.value.filter(e => e.status === 'received').length
  return { total, processed, failed, pending }
})

async function addSource() {
  if (!newSource.value.remote_company_id) {
    toast.error(t('integration.remoteCompanyIdRequired'))
    return
  }
  addLoading.value = true
  try {
    await integrationApi.createSource({
      source_system: 'aigonhr',
      remote_company_id: newSource.value.remote_company_id,
      webhook_secret: newSource.value.webhook_secret || undefined,
    })
    toast.success(t('integration.sourceConnected'))
    showAddSource.value = false
    newSource.value = { remote_company_id: '', webhook_secret: '' }
    fetchData()
  } catch {
    toast.error(t('integration.createSourceFailed'))
  } finally {
    addLoading.value = false
  }
}

async function removeSource(id: string) {
  if (!confirm(t('integration.disconnectConfirm'))) return
  try {
    await integrationApi.deleteSource(id)
    toast.success(t('integration.sourceRemoved'))
    fetchData()
  } catch {
    toast.error(t('integration.removeSourceFailed'))
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ t('integration.title') }}</h1>
      <button class="btn btn-secondary" @click="fetchData()" :disabled="loading">{{ t('integration.refresh') }}</button>
    </div>

    <p class="description">
      {{ t('integration.desc') }}
    </p>

    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">{{ t('integration.totalEvents') }}</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">{{ stats.processed }}</div>
        <div class="stat-label">{{ t('integration.processed') }}</div>
      </div>
      <div class="stat-card stat-danger" v-if="stats.failed > 0">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">{{ t('integration.failed') }}</div>
      </div>
      <div class="stat-card stat-info" v-if="stats.pending > 0">
        <div class="stat-value">{{ stats.pending }}</div>
        <div class="stat-label">{{ t('integration.pending') }}</div>
      </div>
    </div>

    <!-- Sources -->
    <section class="section">
      <div class="section-header">
        <h2>{{ t('integration.connectedSources') }}</h2>
        <button v-if="!showAddSource" class="btn btn-primary btn-sm" @click="showAddSource = true">{{ t('integration.connectAIGoNHR') }}</button>
      </div>

      <!-- Add source form -->
      <div v-if="showAddSource" class="add-source-form">
        <h3>{{ t('integration.connectFormTitle') }}</h3>
        <p class="form-hint">{{ t('integration.connectFormHint') }}</p>
        <div class="form-row">
          <label>{{ t('integration.remoteCompanyId') }}</label>
          <input v-model="newSource.remote_company_id" :placeholder="t('integration.remoteCompanyIdPlaceholder')" />
        </div>
        <div class="form-row">
          <label>{{ t('integration.webhookSecret') }}</label>
          <input v-model="newSource.webhook_secret" type="password" :placeholder="t('integration.webhookSecretPlaceholder')" />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" :disabled="addLoading" @click="addSource">
            {{ addLoading ? t('integration.connecting') : t('integration.connect') }}
          </button>
          <button class="btn btn-secondary" @click="showAddSource = false">{{ t('integration.cancel') }}</button>
        </div>
      </div>

      <div v-if="sources.length > 0" class="source-cards">
        <div v-for="src in sources" :key="src.id" class="source-card">
          <div class="source-header">
            <span class="source-system">{{ src.source_system.toUpperCase() }}</span>
            <span :class="['badge', src.status === 'active' ? 'badge-success' : 'badge-secondary']">{{ src.status }}</span>
          </div>
          <div class="source-detail">{{ t('integration.remoteCompany', { id: src.remote_company_id }) }}</div>
          <div class="source-detail">{{ t('integration.lastEvent', { date: formatDate(src.last_event_at) }) }}</div>
          <div class="source-detail">{{ t('integration.connected', { date: formatDate(src.created_at) }) }}</div>
          <div class="source-actions">
            <button class="btn btn-sm btn-danger" @click="removeSource(src.id)">{{ t('integration.disconnect') }}</button>
          </div>
        </div>
      </div>
      <div v-else-if="!showAddSource" class="empty">
        <p>{{ t('integration.emptyNoSources') }}</p>
      </div>
    </section>

    <!-- Events -->
    <section class="section">
      <h2>{{ t('integration.eventHistory') }}</h2>
      <div v-if="loading" class="loading">{{ t('integration.loadingEvents') }}</div>
      <div v-else-if="events.length === 0" class="empty">
        <p>{{ t('integration.emptyNoEvents') }}</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>{{ t('integration.thEventType') }}</th>
            <th>{{ t('integration.thEventId') }}</th>
            <th>{{ t('integration.thStatus') }}</th>
            <th>{{ t('integration.thReceived') }}</th>
            <th>{{ t('integration.thProcessed') }}</th>
            <th>{{ t('integration.thDetails') }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="evt in events" :key="evt.id">
            <tr>
              <td><span class="event-type">{{ eventTypeLabel(evt.event_type) }}</span></td>
              <td><code>{{ evt.event_id.substring(0, 12) }}...</code></td>
              <td><span :class="['badge', statusBadge(evt.status)]">{{ evt.status }}</span></td>
              <td>{{ formatDate(evt.created_at) }}</td>
              <td>{{ formatDate(evt.processed_at) }}</td>
              <td>
                <button class="btn btn-sm btn-secondary" @click="togglePayload(evt.id)">
                  {{ expandedEvent === evt.id ? t('integration.hide') : t('integration.view') }}
                </button>
              </td>
            </tr>
            <tr v-if="expandedEvent === evt.id">
              <td colspan="6">
                <div class="payload-container">
                  <div v-if="evt.error_message" class="error-msg">{{ t('integration.error', { message: evt.error_message }) }}</div>
                  <pre class="payload">{{ JSON.stringify(evt.payload, null, 2) }}</pre>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.page { max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h1 { font-size: 1.5rem; margin: 0; }
.description { color: var(--text-secondary, #6b7280); margin-bottom: 24px; font-size: 0.9rem; }

.stats-row { display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }
.stat-card { background: var(--bg-surface); border: 1px solid var(--border, #e5e7eb); border-radius: 12px; padding: 16px 24px; min-width: 120px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--text-primary, #1f2937); }
.stat-label { font-size: 0.8rem; color: var(--text-secondary, #6b7280); margin-top: 4px; }
.stat-success { border-left: 4px solid #16a34a; }
.stat-danger { border-left: 4px solid #dc2626; }
.stat-info { border-left: 4px solid #2563eb; }

.section { margin-bottom: 32px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h2 { margin: 0; }
.section h2 { font-size: 1.15rem; margin-bottom: 16px; }

.add-source-form { background: var(--bg-surface); border: 1px solid var(--border, #e5e7eb); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.add-source-form h3 { margin: 0 0 8px; font-size: 1rem; }
.form-hint { font-size: 0.85rem; color: var(--text-secondary, #6b7280); margin-bottom: 16px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px; color: var(--text-primary, #374151); }
.form-row input { width: 100%; padding: 8px 12px; border: 1px solid var(--border, #d1d5db); border-radius: 6px; font-size: 0.875rem; box-sizing: border-box; }
.form-row input:focus { outline: none; border-color: #4f46e5; box-shadow: 0 0 0 2px rgba(79,70,229,0.15); }
.form-actions { display: flex; gap: 8px; margin-top: 16px; }

.source-actions { margin-top: 10px; }
.btn-primary { background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 0.875rem; }
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger { background: #dc2626; color: white; border: none; cursor: pointer; }
.btn-danger:hover { background: #b91c1c; }

.source-cards { display: flex; gap: 16px; flex-wrap: wrap; }
.source-card { background: var(--bg-surface); border: 1px solid var(--border, #e5e7eb); border-radius: 12px; padding: 16px; min-width: 250px; flex: 1; }
.source-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.source-system { font-weight: 700; font-size: 0.95rem; }
.source-detail { font-size: 0.85rem; color: var(--text-secondary, #6b7280); margin-bottom: 4px; }

.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th { text-align: left; padding: 8px 12px; background: var(--bg-secondary, #f9fafb); border-bottom: 2px solid var(--border, #e5e7eb); font-weight: 600; }
.table td { padding: 8px 12px; border-bottom: 1px solid var(--border, #e5e7eb); }
.table code { background: var(--bg-tertiary, #f3f4f6); padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }

.event-type { font-weight: 500; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.badge-success { background: #dcfce7; color: #166534; }
.badge-danger { background: #fee2e2; color: #991b1b; }
.badge-info { background: #dbeafe; color: #1e40af; }
.badge-secondary { background: var(--bg-tertiary, #f3f4f6); color: var(--text-secondary, #6b7280); }

.payload-container { padding: 12px; background: var(--bg-secondary, #f9fafb); border-radius: 8px; }
.payload { font-size: 0.8rem; max-height: 300px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; }
.error-msg { color: #dc2626; font-weight: 500; margin-bottom: 8px; font-size: 0.85rem; }

.loading { text-align: center; padding: 40px; color: var(--text-secondary); }
.empty { text-align: center; padding: 40px; color: var(--text-secondary); }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 500; }
.btn-secondary { background: var(--bg-secondary, #f3f4f6); color: var(--text-primary, #374151); border: 1px solid var(--border, #d1d5db); }
.btn-sm { padding: 4px 8px; font-size: 0.8rem; }

@media (max-width: 768px) {
  .stats-row { flex-direction: column; }
  .source-cards { flex-direction: column; }
  .table { font-size: 0.8rem; }
  .table th, .table td { padding: 6px 8px; }
}
</style>
