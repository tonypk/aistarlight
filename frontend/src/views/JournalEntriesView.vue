<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccountingStore } from '../stores/accounting'
import { currencyLocale } from '@/utils/currency'
import InlineAIHint from '../components/ai/InlineAIHint.vue'

const route = useRoute()
const router = useRouter()
const store = useAccountingStore()
const statusFilter = ref('')
const page = ref(1)
const selectedEntry = ref<string | null>(null)
const highlightId = ref<string | null>(null)

onMounted(async () => {
  if (route.query.highlight) {
    highlightId.value = route.query.highlight as string
  }
  await loadEntries()
  // Auto-expand highlighted entry
  if (highlightId.value) {
    viewEntry(highlightId.value)
  }
})

async function loadEntries() {
  await store.fetchJournalEntries(page.value, 20, statusFilter.value || undefined)
}

function viewEntry(id: string) {
  selectedEntry.value = id
  store.fetchJournalEntry(id)
}

function closeDetail() {
  selectedEntry.value = null
  store.currentJournal = null
}

async function postEntry(id: string) {
  await store.postJournalEntry(id)
  if (selectedEntry.value === id) {
    store.fetchJournalEntry(id)
  }
}

async function reverseEntry(id: string) {
  if (!confirm('Reverse this journal entry?')) return
  await store.reverseJournalEntry(id)
  if (selectedEntry.value === id) {
    store.fetchJournalEntry(id)
  }
}

function formatAmount(val: string) {
  const n = parseFloat(val || '0')
  return n === 0 ? '' : n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const statusColors: Record<string, string> = {
  draft: '#f59e0b',
  posted: '#10b981',
  reversed: '#ef4444',
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Journal Entries</h1>
      <InlineAIHint agent="journal" message="AI can help create and explain journal entries" action-label="Ask Journal Agent" />
    </div>

    <div class="filters">
      <select v-model="statusFilter" @change="loadEntries" class="select">
        <option value="">All Status</option>
        <option value="draft">Draft</option>
        <option value="posted">Posted</option>
        <option value="reversed">Reversed</option>
      </select>
      <span class="count">{{ store.journalTotal }} entries</span>
    </div>

    <!-- Detail Panel -->
    <div v-if="store.currentJournal" class="detail-panel">
      <div class="detail-header">
        <h2>JE #{{ store.currentJournal.entry_number }}</h2>
        <div class="detail-actions">
          <button v-if="store.currentJournal.status === 'draft'" class="btn btn-primary" @click="postEntry(store.currentJournal.id)">Post</button>
          <button v-if="store.currentJournal.status === 'posted'" class="btn btn-danger" @click="reverseEntry(store.currentJournal.id)">Reverse</button>
          <button class="btn btn-secondary" @click="closeDetail">Close</button>
        </div>
      </div>
      <div class="detail-meta">
        <span>Date: {{ store.currentJournal.entry_date?.slice(0, 10) }}</span>
        <span>Status: <span class="status" :style="{ color: statusColors[store.currentJournal.status] }">{{ store.currentJournal.status }}</span></span>
        <span v-if="store.currentJournal.reference">Ref: {{ store.currentJournal.reference }}</span>
        <span v-if="store.currentJournal.description">{{ store.currentJournal.description }}</span>
        <span v-if="store.currentJournal.source_type === 'transaction' && store.currentJournal.source_id">
          Source: <a class="source-link" @click="router.push({ path: '/transactions', query: { highlight: store.currentJournal.source_id } })">Transaction {{ store.currentJournal.source_id.slice(0, 8) }}...</a>
        </span>
      </div>
      <table class="table lines-table">
        <thead>
          <tr><th>Account</th><th>Description</th><th class="right">Debit</th><th class="right">Credit</th></tr>
        </thead>
        <tbody>
          <tr v-for="line in store.currentJournal.lines" :key="line.id">
            <td class="mono">{{ line.account_number }} {{ line.account_name }}</td>
            <td>{{ line.description }}</td>
            <td class="right mono">{{ formatAmount(line.debit) }}</td>
            <td class="right mono">{{ formatAmount(line.credit) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Entry List -->
    <div v-if="store.loading && !store.currentJournal" class="loading">Loading...</div>
    <table v-else class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Date</th>
          <th>Description</th>
          <th>Source</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="je in store.journalEntries" :key="je.id" @click="viewEntry(je.id)" class="clickable" :class="{ 'highlight-row': highlightId === je.id }">
          <td class="mono">{{ je.entry_number }}</td>
          <td>{{ je.entry_date?.slice(0, 10) }}</td>
          <td>{{ je.description || je.reference || '-' }}</td>
          <td>
            <a
              v-if="je.source_type === 'transaction' && je.source_id"
              class="source-link"
              @click.stop="router.push({ path: '/transactions', query: { highlight: je.source_id } })"
            >{{ je.source_type }}</a>
            <span v-else>{{ je.source_type || 'manual' }}</span>
          </td>
          <td>
            <span class="status-badge" :class="'status-' + je.status">{{ je.status }}</span>
          </td>
          <td class="actions" @click.stop>
            <button v-if="je.status === 'draft'" class="btn-sm btn-primary" @click="postEntry(je.id)">Post</button>
            <button v-if="je.status === 'posted'" class="btn-sm btn-danger" @click="reverseEntry(je.id)">Reverse</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination" v-if="store.journalTotal > 20">
      <button :disabled="page <= 1" @click="page--; loadEntries()">Prev</button>
      <span>Page {{ page }}</span>
      <button :disabled="store.journalEntries.length < 20" @click="page++; loadEntries()">Next</button>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 24px; margin: 0; }
.filters { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.select { padding: 8px 12px; border: 1px solid var(--border-default); border-radius: 6px; font-size: 14px; }
.count { color: var(--text-secondary); font-size: 14px; }
.table { width: 100%; border-collapse: collapse; font-size: 14px; }
.table th { text-align: left; padding: 10px 12px; background: var(--bg-surface-alt); border-bottom: 1px solid var(--border-default); font-weight: 600; }
.table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; }
.right { text-align: right; }
.mono { font-family: monospace; }
.clickable { cursor: pointer; }
.clickable:hover { background: var(--bg-surface-alt); }
.loading { text-align: center; padding: 40px; color: #666; }
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; text-transform: capitalize; }
.status-draft { background: #fef3c7; color: #92400e; }
.status-posted { background: #d1fae5; color: #065f46; }
.status-reversed { background: #fee2e2; color: #991b1b; }
.btn, .btn-sm { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-primary { background: var(--brand-primary); color: #fff; }
.btn-primary:hover { background: var(--brand-primary-hover); }
.btn-secondary { background: var(--border-default); color: var(--text-primary); }
.btn-danger { background: #ef4444; color: #fff; }
.btn-danger:hover { background: #dc2626; }
.actions { display: flex; gap: 6px; }
.detail-panel { background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 8px; padding: 20px; margin-bottom: 24px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.detail-header h2 { margin: 0; font-size: 18px; }
.detail-actions { display: flex; gap: 8px; }
.detail-meta { display: flex; gap: 20px; margin-bottom: 16px; font-size: 14px; color: var(--text-secondary); }
.status { font-weight: 600; text-transform: uppercase; }
.lines-table { margin-top: 8px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 20px; }
.pagination button { padding: 6px 14px; border: 1px solid var(--border-default); border-radius: 4px; background: var(--bg-surface); cursor: pointer; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.source-link { color: var(--brand-primary); cursor: pointer; text-decoration: none; font-weight: 500; }
.source-link:hover { text-decoration: underline; }
.highlight-row { background: #fef9c3 !important; animation: highlight-fade 3s ease-out forwards; }
@keyframes highlight-fade { 0% { background: #fef9c3; } 100% { background: transparent; } }
</style>
