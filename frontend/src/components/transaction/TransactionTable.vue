<script setup lang="ts">
import { ref } from 'vue'
import type { Transaction, VatType, Category } from '../../types/transaction'
import ClassificationBadge from './ClassificationBadge.vue'

const props = defineProps<{
  transactions: Transaction[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update', txnId: string, data: { vat_type?: string; category?: string }): void
  (e: 'select', ids: string[]): void
}>()

const selectedIds = ref<Set<string>>(new Set())
const editingId = ref<string | null>(null)
const editVatType = ref<VatType>('vatable')
const editCategory = ref<Category>('goods')

const vatTypes: VatType[] = ['vatable', 'exempt', 'zero_rated', 'government']
const categories: Category[] = ['goods', 'services', 'capital', 'imports', 'sale']

function toggleSelect(id: string) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
  emit('select', [...next])
}

function toggleAll() {
  if (selectedIds.value.size === props.transactions.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(props.transactions.map((t) => t.id))
  }
  emit('select', [...selectedIds.value])
}

function startEdit(txn: Transaction) {
  editingId.value = txn.id
  editVatType.value = txn.vat_type
  editCategory.value = txn.category
}

function saveEdit(txnId: string) {
  emit('update', txnId, {
    vat_type: editVatType.value,
    category: editCategory.value,
  })
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
}

function formatAmount(amount: number): string {
  return amount.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="table-wrapper">
    <div v-if="loading" class="loading">Loading transactions...</div>
    <table v-else>
      <thead>
        <tr>
          <th class="check-col"><input type="checkbox" @change="toggleAll" /></th>
          <th>Date</th>
          <th>Description</th>
          <th class="amount-col">Amount</th>
          <th>VAT Type</th>
          <th>Category</th>
          <th>Confidence</th>
          <th>TIN</th>
          <th class="action-col"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="txn in transactions" :key="txn.id" :class="{ 'low-conf': txn.confidence < 0.5 }">
          <td class="check-col">
            <input type="checkbox" :checked="selectedIds.has(txn.id)" @change="toggleSelect(txn.id)" />
          </td>
          <td>{{ txn.date ?? '—' }}</td>
          <td class="desc-col" :title="txn.description ?? ''">{{ txn.description ?? '—' }}</td>
          <td class="amount-col">{{ formatAmount(txn.amount) }}</td>
          <td>
            <template v-if="editingId === txn.id">
              <select v-model="editVatType" class="inline-select">
                <option v-for="vt in vatTypes" :key="vt" :value="vt">{{ vt }}</option>
              </select>
            </template>
            <template v-else>
              <ClassificationBadge :vat-type="txn.vat_type" :confidence="txn.confidence" :source="txn.classification_source" />
            </template>
          </td>
          <td>
            <template v-if="editingId === txn.id">
              <select v-model="editCategory" class="inline-select">
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </template>
            <template v-else>
              <span class="category-label">{{ txn.category }}</span>
            </template>
          </td>
          <td>
            <span :style="{ color: txn.confidence >= 0.8 ? '#16a34a' : txn.confidence >= 0.5 ? '#d97706' : '#dc2626' }">
              {{ (txn.confidence * 100).toFixed(0) }}%
            </span>
          </td>
          <td>{{ txn.tin ?? '—' }}</td>
          <td class="action-col">
            <template v-if="editingId === txn.id">
              <button class="save-btn" @click="saveEdit(txn.id)">Save</button>
              <button class="cancel-btn" @click="cancelEdit">Cancel</button>
            </template>
            <template v-else>
              <button class="edit-btn" @click="startEdit(txn)">Edit</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && transactions.length === 0" class="empty">
      No transactions found.
    </div>
  </div>
</template>

<style scoped>
.table-wrapper {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow-x: auto;
}
.loading, .empty {
  text-align: center;
  padding: 32px;
  color: #6b7280;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th {
  text-align: left;
  padding: 12px 16px;
  background: #f9fafb;
  font-weight: 600;
  font-size: 13px;
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}
td {
  padding: 10px 16px;
  border-bottom: 1px solid #f3f4f6;
}
tr.low-conf { background: #fffbeb; }
.check-col { width: 40px; text-align: center; }
.amount-col { text-align: right; font-variant-numeric: tabular-nums; }
.desc-col {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.category-label { text-transform: capitalize; font-size: 13px; }
.action-col { width: 100px; white-space: nowrap; }
.inline-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
}
.edit-btn, .save-btn, .cancel-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.edit-btn { background: #e5e7eb; color: #374151; }
.edit-btn:hover { background: #d1d5db; }
.save-btn { background: #4f46e5; color: #fff; margin-right: 4px; }
.cancel-btn { background: #e5e7eb; color: #374151; }
</style>
