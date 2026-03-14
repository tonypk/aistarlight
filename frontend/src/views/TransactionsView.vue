<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { transactionsApi } from '../api/transactions'
import { useTagStore } from '../stores/tags'
import type { Tag } from '../api/tags'

interface Transaction {
  id: string
  source_type: string
  source_file_id: string
  date: string | null
  description: string | null
  amount: number
  vat_amount: number
  category: string
  submitted_by_name: string | null
  receipt_image_url: string | null
  journal_entry_id?: string | null
  journal_entry_num?: number | null
  created_at?: string
}

const route = useRoute()
const router = useRouter()
const tagStore = useTagStore()
const highlightId = ref<string | null>(null)

// Tag state
const transactionTags = ref<Record<string, Tag[]>>({})
const showTagModal = ref(false)
const tagModalTxnId = ref('')
const selectedTagIds = ref<string[]>([])

const transactions = ref<Transaction[]>([])
const loading = ref(false)
const error = ref('')
const total = ref(0)
const page = ref(1)
const limit = ref(20)

// Filters
const sourceType = ref('')
const category = ref('')
const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')

const sourceTypes = ['', 'receipt', 'telegram_bot', 'forex', 'manual', 'csv', 'excel']
const sourceTypeLabels: Record<string, string> = {
  '': 'All Sources',
  receipt: 'Receipt',
  telegram_bot: 'Telegram Bot',
  forex: 'Forex',
  manual: 'Manual',
  csv: 'CSV',
  excel: 'Excel',
}

const totalPages = ref(0)

async function fetchTransactions() {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, any> = {
      page: page.value,
      limit: limit.value,
    }
    if (sourceType.value) params.source_type = sourceType.value
    if (category.value) params.category = category.value
    if (search.value) params.search = search.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value

    const { data } = await transactionsApi.list(params)
    transactions.value = data.data || []
    total.value = data.meta?.total || 0
    totalPages.value = Math.ceil(total.value / limit.value)
    loadTagsForTransactions(transactions.value)
  } catch (e: any) {
    error.value = e?.response?.data?.error || 'Failed to load transactions'
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  fetchTransactions()
}

function clearFilters() {
  sourceType.value = ''
  category.value = ''
  search.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  page.value = 1
  fetchTransactions()
}

function goToPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  fetchTransactions()
}

function formatAmount(amount: number): string {
  return new Intl.NumberFormat('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function formatDate(date: string | null): string {
  if (!date) return '-'
  return date
}

async function loadTagsForTransactions(txns: Transaction[]) {
  for (const txn of txns) {
    try {
      const tags = await tagStore.getTransactionTags(txn.id)
      transactionTags.value = { ...transactionTags.value, [txn.id]: tags }
    } catch {
      // Silently skip tag loading failures
    }
  }
}

function openTagModal(txnId: string) {
  tagModalTxnId.value = txnId
  const existing = transactionTags.value[txnId] || []
  selectedTagIds.value = existing.map(t => t.id)
  showTagModal.value = true
}

async function saveTransactionTags() {
  try {
    const updated = await tagStore.setTransactionTags(tagModalTxnId.value, selectedTagIds.value)
    transactionTags.value = { ...transactionTags.value, [tagModalTxnId.value]: updated }
    showTagModal.value = false
  } catch (e: any) {
    error.value = e?.response?.data?.error || 'Failed to update tags'
  }
}

function toggleTagSelection(tagId: string) {
  if (selectedTagIds.value.includes(tagId)) {
    selectedTagIds.value = selectedTagIds.value.filter(id => id !== tagId)
  } else {
    selectedTagIds.value = [...selectedTagIds.value, tagId]
  }
}

onMounted(() => {
  if (route.query.highlight) {
    highlightId.value = route.query.highlight as string
  }
  tagStore.fetchTags(1, 200)
  fetchTransactions()
})
</script>

<template>
  <div class="transactions-view">
    <div class="view-header">
      <h2>Transactions Overview</h2>
      <span class="total-badge">{{ total }} records</span>
    </div>

    <!-- Filters -->
    <div class="filters">
      <select v-model="sourceType" @change="applyFilters">
        <option v-for="st in sourceTypes" :key="st" :value="st">
          {{ sourceTypeLabels[st] || st }}
        </option>
      </select>

      <input
        v-model="category"
        placeholder="Category..."
        @keyup.enter="applyFilters"
      />

      <input
        v-model="search"
        placeholder="Search description..."
        @keyup.enter="applyFilters"
      />

      <input type="date" v-model="dateFrom" @change="applyFilters" title="From date" />
      <input type="date" v-model="dateTo" @change="applyFilters" title="To date" />

      <button class="btn" @click="applyFilters">Search</button>
      <button class="btn secondary" @click="clearFilters">Clear</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Loading -->
    <div v-if="loading" class="loading">Loading...</div>

    <!-- Table -->
    <div v-else-if="transactions.length > 0" class="table-container">
      <table>
        <thead>
          <tr>
            <th class="text-center">#</th>
            <th>Date</th>
            <th>Description</th>
            <th class="text-right">Amount</th>
            <th>Category</th>
            <th>Tags</th>
            <th>Source</th>
            <th>Journal</th>
            <th>Submitted By</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(txn, idx) in transactions" :key="txn.id" :class="{ 'highlight-row': highlightId === txn.id }">
            <td class="text-center row-number">{{ (page - 1) * limit + idx + 1 }}</td>
            <td class="nowrap">{{ formatDate(txn.date) }}</td>
            <td class="description-cell" :title="txn.description ?? ''">{{ txn.description || '-' }}</td>
            <td class="text-right nowrap">{{ formatAmount(txn.amount) }}</td>
            <td>
              <span v-if="txn.category" class="badge category">{{ txn.category }}</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td class="tags-cell">
              <span
                v-for="tag in (transactionTags[txn.id] || [])"
                :key="tag.id"
                class="tag-chip"
                :style="{ background: tag.color + '20', color: tag.color, borderColor: tag.color }"
              >{{ tag.name }}</span>
              <button class="tag-add-btn" @click.stop="openTagModal(txn.id)" title="Manage tags">+</button>
            </td>
            <td>
              <span class="badge source" :class="txn.source_type">
                {{ sourceTypeLabels[txn.source_type] || txn.source_type }}
              </span>
            </td>
            <td>
              <span
                v-if="txn.journal_entry_id"
                class="badge journal-linked"
                @click.stop="router.push({ path: '/journal-entries', query: { highlight: txn.journal_entry_id } })"
              >JE #{{ txn.journal_entry_num || '?' }}</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td>{{ txn.submitted_by_name || '-' }}</td>
            <td>
              <a
                v-if="txn.receipt_image_url"
                :href="txn.receipt_image_url"
                target="_blank"
                class="image-link"
                title="View receipt"
              >View</a>
              <span v-else class="text-muted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty">
      No transactions found. Try adjusting your filters.
    </div>

    <!-- Tag Assignment Modal -->
    <div v-if="showTagModal" class="modal-overlay" @click.self="showTagModal = false">
      <div class="modal">
        <h3>Manage Tags</h3>
        <div v-if="tagStore.tags.length === 0" class="empty-tags">
          No tags created yet. Go to Tag Management to create tags.
        </div>
        <div v-else class="tag-selector">
          <button
            v-for="tag in tagStore.tags"
            :key="tag.id"
            type="button"
            class="tag-option"
            :class="{ selected: selectedTagIds.includes(tag.id) }"
            :style="{
              background: selectedTagIds.includes(tag.id) ? tag.color + '20' : '#f9fafb',
              color: selectedTagIds.includes(tag.id) ? tag.color : '#6b7280',
              borderColor: selectedTagIds.includes(tag.id) ? tag.color : 'var(--border-default)',
            }"
            @click="toggleTagSelection(tag.id)"
          >{{ tag.name }}</button>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showTagModal = false">Cancel</button>
          <button class="btn primary" @click="saveTransactionTags">Save</button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="goToPage(page - 1)">Prev</button>
      <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="goToPage(page + 1)">Next</button>
    </div>
  </div>
</template>

<style scoped>
.transactions-view {
  padding: 24px;
  max-width: 1400px;
}

.view-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.view-header h2 {
  margin: 0;
}
.total-badge {
  background: #e0e7ff;
  color: #3730a3;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}
.filters select,
.filters input {
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-surface);
}
.filters select {
  min-width: 140px;
}
.filters input[type="text"],
.filters input:not([type]) {
  min-width: 150px;
}
.filters input[type="date"] {
  min-width: 140px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  background: var(--brand-primary);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn:hover {
  background: var(--brand-primary-hover);
}
.btn.secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
}
.btn.secondary:hover {
  background: var(--bg-surface-hover);
}

.error {
  color: #dc2626;
  background: #fef2f2;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.table-container {
  overflow-x: auto;
  border: 1px solid var(--border-default);
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
thead {
  background: var(--bg-surface-alt);
}
th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-default);
  white-space: nowrap;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: var(--text-primary);
}
tbody tr:hover {
  background: var(--bg-surface-alt);
}

.text-right {
  text-align: right;
}
.text-center {
  text-align: center;
}
.row-number {
  color: var(--text-muted);
  font-size: 13px;
}
.nowrap {
  white-space: nowrap;
}
.text-muted {
  color: var(--text-muted);
}

.description-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.badge.category {
  background: #ecfdf5;
  color: #065f46;
}
.badge.source {
  background: #eff6ff;
  color: #1e40af;
}
.badge.source.receipt {
  background: #fef3c7;
  color: #92400e;
}
.badge.source.forex {
  background: #ede9fe;
  color: #5b21b6;
}
.badge.source.telegram_bot {
  background: #e0f2fe;
  color: #075985;
}

.badge.journal-linked {
  background: #d1fae5;
  color: #065f46;
  cursor: pointer;
}
.badge.journal-linked:hover {
  background: #a7f3d0;
}

.highlight-row {
  background: #fef9c3 !important;
  animation: highlight-fade 3s ease-out forwards;
}
@keyframes highlight-fade {
  0% { background: #fef9c3; }
  100% { background: transparent; }
}

.image-link {
  color: var(--brand-primary);
  text-decoration: none;
  font-weight: 500;
}
.image-link:hover {
  text-decoration: underline;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 12px 0;
}
.pagination button {
  padding: 6px 14px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 14px;
}
.pagination button:hover:not(:disabled) {
  background: var(--bg-surface-hover);
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-info {
  color: var(--text-secondary);
  font-size: 14px;
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.tag-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid;
  white-space: nowrap;
}
.tag-add-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px dashed var(--border-input);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.tag-add-btn:hover {
  background: var(--bg-surface-hover);
  color: var(--brand-primary);
  border-color: var(--brand-primary);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal {
  background: var(--bg-surface);
  border-radius: 16px;
  padding: 32px;
  width: 440px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 16px; }

.tag-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.tag-option {
  padding: 6px 14px;
  border-radius: 16px;
  border: 1px solid;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
}
.tag-option:hover { opacity: 0.8; }

.empty-tags {
  color: var(--text-muted);
  text-align: center;
  padding: 20px 0;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
