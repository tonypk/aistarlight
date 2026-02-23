<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTransactionStore } from '../stores/transaction'
import { useUploadStore } from '../stores/upload'
import TransactionSummaryCards from '../components/transaction/TransactionSummaryCards.vue'
import TransactionFiltersBar from '../components/transaction/TransactionFilters.vue'
import TransactionTable from '../components/transaction/TransactionTable.vue'
import BulkActionBar from '../components/transaction/BulkActionBar.vue'
import type { TransactionFilters } from '../types/transaction'

const router = useRouter()
const route = useRoute()
const store = useTransactionStore()
const uploadStore = useUploadStore()

const page = ref(1)
const selectedIds = ref<string[]>([])
const classifyError = ref('')
const listMode = ref(false)

const sessionId = computed(() => (route.query.session as string) || '')

// Watch for query changes (e.g. when navigating to a session from the list)
watch(sessionId, async (newId) => {
  if (newId) {
    listMode.value = false
    await loadData(newId)
  }
})

onMounted(async () => {
  if (!sessionId.value) {
    // Check if we came from upload flow with file ready
    if (uploadStore.hasFile && uploadStore.hasMappings) {
      // Auto-create session + add file
      const now = new Date()
      const period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
      const session = await store.createSession(period)
      await store.addFile(
        session.id,
        uploadStore.fileId!,
        'sales_record',
        null,
        uploadStore.confirmedMappings
      )
      router.replace({ query: { session: session.id } })
      await loadData(session.id)
    } else {
      // Show session list
      listMode.value = true
      await store.fetchSessions()
    }
  } else {
    await loadData(sessionId.value)
  }
})

async function loadData(sid: string) {
  await store.fetchSession(sid)
  await store.fetchTransactions(sid, page.value)
}

async function classify() {
  if (!sessionId.value) return
  classifyError.value = ''
  try {
    await store.classifyTransactions(sessionId.value)
  } catch (e: any) {
    classifyError.value = e?.response?.data?.error ?? 'Classification failed'
  }
}

async function forceClassify() {
  if (!sessionId.value) return
  classifyError.value = ''
  try {
    await store.classifyTransactions(sessionId.value, true)
  } catch (e: any) {
    classifyError.value = e?.response?.data?.error ?? 'Classification failed'
  }
}

function onFiltersUpdate(filters: TransactionFilters) {
  store.setFilters(filters)
  page.value = 1
  store.fetchTransactions(sessionId.value, 1)
}

async function onTransactionUpdate(txnId: string, data: { vat_type?: string; category?: string }) {
  await store.updateTransaction(sessionId.value, txnId, data)
}

function onSelect(ids: string[]) {
  selectedIds.value = [...ids]
}

function goToReconciliation() {
  router.push({ path: '/reconciliation', query: { session: sessionId.value } })
}

function openSession(id: string) {
  router.push({ query: { session: id } })
}

function deleteSession(id: string) {
  store.deleteSession(id)
}

function goToUpload() {
  router.push('/upload')
}

function changePage(newPage: number) {
  page.value = newPage
  store.fetchTransactions(sessionId.value, newPage)
}

const totalPages = computed(() => Math.ceil(store.transactionTotal / 50))

const statusColors: Record<string, string> = {
  draft: '#fef3c7',
  classifying: '#dbeafe',
  reviewing: '#ede9fe',
  completed: '#d1fae5',
}
const statusTextColors: Record<string, string> = {
  draft: '#92400e',
  classifying: '#1e40af',
  reviewing: '#5b21b6',
  completed: '#065f46',
}
</script>

<template>
  <div class="classification-view">
    <!-- Session List Mode -->
    <template v-if="listMode">
      <div class="view-header">
        <h2>Transaction Classification</h2>
        <button class="nav-btn" @click="goToUpload">Upload New Data</button>
      </div>

      <div v-if="store.loading" class="loading-msg">Loading sessions...</div>

      <div v-else-if="store.sessions.length === 0" class="empty-state">
        <p>No reconciliation sessions yet.</p>
        <p class="hint">Upload data files to start classifying transactions.</p>
        <button class="nav-btn" @click="goToUpload">Upload Data</button>
      </div>

      <div v-else class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.id"
          class="session-card"
          @click="openSession(s.id)"
        >
          <div class="session-info">
            <div class="session-period">{{ s.period }}</div>
            <span
              class="status-badge"
              :style="{
                background: statusColors[s.status] ?? '#f3f4f6',
                color: statusTextColors[s.status] ?? '#374151',
              }"
            >
              {{ s.status }}
            </span>
          </div>
          <div class="session-meta">
            <span>{{ s.source_files?.length ?? 0 }} files</span>
            <span>Created {{ new Date(s.created_at).toLocaleDateString() }}</span>
          </div>
          <button
            v-if="s.status === 'draft'"
            class="delete-btn"
            @click.stop="deleteSession(s.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </template>

    <!-- Session Detail Mode -->
    <template v-else>
      <div class="view-header">
        <div>
          <h2>Transaction Classification</h2>
          <p class="desc" v-if="store.currentSession">
            Period: {{ store.currentSession.period }}
            | {{ store.transactionTotal }} transactions
            | Status: {{ store.currentSession.status }}
          </p>
        </div>
        <div class="header-actions">
          <button class="btn-back" @click="listMode = true; store.reset()">All Sessions</button>
          <button
            class="ai-btn"
            :disabled="store.classifying"
            @click="classify"
          >
            {{ store.classifying ? 'Classifying...' : 'AI Classify' }}
          </button>
          <button
            v-if="store.sessionStatus === 'reviewing'"
            class="ai-btn secondary"
            :disabled="store.classifying"
            @click="forceClassify"
          >
            Re-classify All
          </button>
          <button class="nav-btn" @click="goToReconciliation">
            Continue to Reconciliation
          </button>
        </div>
      </div>

      <p v-if="classifyError" class="error">{{ classifyError }}</p>

      <TransactionSummaryCards :transactions="store.transactions" />

      <TransactionFiltersBar @update="onFiltersUpdate" />

      <BulkActionBar
        :selected-count="selectedIds.length"
        :total-count="store.transactionTotal"
        @accept-selected="selectedIds = []"
        @accept-high-confidence="selectedIds = []"
        @accept-all="selectedIds = []"
        @clear-selection="selectedIds = []; onSelect([])"
      />

      <TransactionTable
        :transactions="store.transactions"
        :loading="store.loading"
        @update="onTransactionUpdate"
        @select="onSelect"
      />

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page <= 1" @click="changePage(page - 1)">Prev</button>
        <span>Page {{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="changePage(page + 1)">Next</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.classification-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.view-header h2 { margin: 0 0 4px; }
.desc { color: #6b7280; font-size: 14px; margin: 0; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

/* Session List */
.loading-msg { color: #6b7280; text-align: center; padding: 40px 0; }
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}
.empty-state p { margin: 0 0 8px; color: #374151; }
.empty-state .hint { color: #9ca3af; font-size: 14px; margin-bottom: 20px; }
.session-list { display: flex; flex-direction: column; gap: 12px; }
.session-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  position: relative;
}
.session-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.session-info { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.session-period { font-size: 18px; font-weight: 600; color: #111827; }
.status-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.session-meta { font-size: 13px; color: #9ca3af; display: flex; gap: 16px; }
.delete-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 4px 12px;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  background: #fff;
  color: #dc2626;
  font-size: 12px;
  cursor: pointer;
}
.delete-btn:hover { background: #fef2f2; }

/* Detail Mode */
.btn-back {
  padding: 10px 24px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.btn-back:hover { background: #f3f4f6; }
.ai-btn {
  padding: 10px 24px;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.ai-btn:hover { background: #6d28d9; }
.ai-btn:disabled { opacity: 0.6; cursor: default; }
.ai-btn.secondary { background: #6b7280; }
.ai-btn.secondary:hover { background: #4b5563; }
.nav-btn {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.nav-btn:hover { background: #4338ca; }
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}
.pagination button {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: default; }
.pagination span { font-size: 14px; color: #6b7280; }
</style>
