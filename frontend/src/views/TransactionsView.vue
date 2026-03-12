<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { transactionsApi } from '../api/transactions'

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
  created_at?: string
}

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

onMounted(fetchTransactions)
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
            <th>Date</th>
            <th>Description</th>
            <th class="text-right">Amount</th>
            <th>Category</th>
            <th>Source</th>
            <th>Submitted By</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="txn in transactions" :key="txn.id">
            <td class="nowrap">{{ formatDate(txn.date) }}</td>
            <td class="description-cell">{{ txn.description || '-' }}</td>
            <td class="text-right nowrap">{{ formatAmount(txn.amount) }}</td>
            <td>
              <span v-if="txn.category" class="badge category">{{ txn.category }}</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <span class="badge source" :class="txn.source_type">
                {{ sourceTypeLabels[txn.source_type] || txn.source_type }}
              </span>
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
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
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
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #4f46e5;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn:hover {
  background: #4338ca;
}
.btn.secondary {
  background: #fff;
  color: #374151;
}
.btn.secondary:hover {
  background: #f3f4f6;
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
  color: #6b7280;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
thead {
  background: #f9fafb;
}
th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #1f2937;
}
tbody tr:hover {
  background: #f9fafb;
}

.text-right {
  text-align: right;
}
.nowrap {
  white-space: nowrap;
}
.text-muted {
  color: #9ca3af;
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

.image-link {
  color: #4f46e5;
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
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.pagination button:hover:not(:disabled) {
  background: #f3f4f6;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-info {
  color: #6b7280;
  font-size: 14px;
}
</style>
