<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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

const sessionId = computed(() => (route.query.session as string) || '')

onMounted(async () => {
  if (!sessionId.value) {
    // Create session from upload context
    if (!uploadStore.hasFile || !uploadStore.hasMappings) {
      router.push('/upload')
      return
    }
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

function changePage(newPage: number) {
  page.value = newPage
  store.fetchTransactions(sessionId.value, newPage)
}

const totalPages = computed(() => Math.ceil(store.transactionTotal / 50))
</script>

<template>
  <div class="classification-view">
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
