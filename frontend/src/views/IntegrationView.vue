<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { integrationApi, type IntegrationSource, type IntegrationEvent } from '../api/integration'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const sources = ref<IntegrationSource[]>([])
const events = ref<IntegrationEvent[]>([])
const loading = ref(false)
const page = ref(1)
const expandedEvent = ref<string | null>(null)

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
    case 'payroll.run.completed': return 'Payroll Completed'
    case 'payroll.run.reversed': return 'Payroll Reversed'
    case 'employee.upserted': return 'Employee Synced'
    case 'employee.terminated': return 'Employee Terminated'
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
    toast.error('Failed to load integration data')
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

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>HR Integration</h1>
      <button class="btn btn-secondary" @click="fetchData()" :disabled="loading">Refresh</button>
    </div>

    <p class="description">
      Integration with AIGoNHR for automated payroll journal entries and tax form generation.
    </p>

    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total Events</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">{{ stats.processed }}</div>
        <div class="stat-label">Processed</div>
      </div>
      <div class="stat-card stat-danger" v-if="stats.failed > 0">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">Failed</div>
      </div>
      <div class="stat-card stat-info" v-if="stats.pending > 0">
        <div class="stat-value">{{ stats.pending }}</div>
        <div class="stat-label">Pending</div>
      </div>
    </div>

    <!-- Sources -->
    <section class="section" v-if="sources.length > 0">
      <h2>Connected Sources</h2>
      <div class="source-cards">
        <div v-for="src in sources" :key="src.id" class="source-card">
          <div class="source-header">
            <span class="source-system">{{ src.source_system.toUpperCase() }}</span>
            <span :class="['badge', src.status === 'active' ? 'badge-success' : 'badge-secondary']">{{ src.status }}</span>
          </div>
          <div class="source-detail">Remote Company: {{ src.remote_company_id }}</div>
          <div class="source-detail">Last Event: {{ formatDate(src.last_event_at) }}</div>
          <div class="source-detail">Connected: {{ formatDate(src.created_at) }}</div>
        </div>
      </div>
    </section>

    <!-- Events -->
    <section class="section">
      <h2>Event History</h2>
      <div v-if="loading" class="loading">Loading events...</div>
      <div v-else-if="events.length === 0" class="empty">
        <p>No integration events received yet. Connect AIGoNHR and run a payroll to see events here.</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Event Type</th>
            <th>Event ID</th>
            <th>Status</th>
            <th>Received</th>
            <th>Processed</th>
            <th>Details</th>
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
                  {{ expandedEvent === evt.id ? 'Hide' : 'View' }}
                </button>
              </td>
            </tr>
            <tr v-if="expandedEvent === evt.id">
              <td colspan="6">
                <div class="payload-container">
                  <div v-if="evt.error_message" class="error-msg">Error: {{ evt.error_message }}</div>
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
.stat-card { background: white; border: 1px solid var(--border, #e5e7eb); border-radius: 12px; padding: 16px 24px; min-width: 120px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--text-primary, #1f2937); }
.stat-label { font-size: 0.8rem; color: var(--text-secondary, #6b7280); margin-top: 4px; }
.stat-success { border-left: 4px solid #16a34a; }
.stat-danger { border-left: 4px solid #dc2626; }
.stat-info { border-left: 4px solid #2563eb; }

.section { margin-bottom: 32px; }
.section h2 { font-size: 1.15rem; margin-bottom: 16px; }

.source-cards { display: flex; gap: 16px; flex-wrap: wrap; }
.source-card { background: white; border: 1px solid var(--border, #e5e7eb); border-radius: 12px; padding: 16px; min-width: 250px; flex: 1; }
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
