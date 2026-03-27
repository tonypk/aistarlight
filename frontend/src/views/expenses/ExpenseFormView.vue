<script setup lang="ts">
import { ref, h, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NInput, NCard, NSpace, NDataTable, NTag,
  NPopconfirm, useMessage,
} from 'naive-ui'
import { expenseReportApi, expenseItemApi } from '../../api/expenses'
import type { ExpenseReport, ExpenseItem } from '../../types/expense'
import ExpenseItemForm from '../../components/expenses/ExpenseItemForm.vue'
import ReceiptUploader from '../../components/expenses/ReceiptUploader.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const reportId = computed(() => route.params.id as string | undefined)
const isEdit = computed(() => !!reportId.value)

const loading = ref(false)
const saving = ref(false)
const submitting = ref(false)

const title = ref('')
const notes = ref('')
const report = ref<ExpenseReport | null>(null)
const items = ref<ExpenseItem[]>([])

// Item form modal state
const showItemForm = ref(false)
const editingItem = ref<ExpenseItem | null>(null)

function formatAmount(amount: number | string): string {
  return `₱${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const itemColumns = [
  {
    title: 'Category',
    key: 'category',
    width: 130,
    render: (row: ExpenseItem) =>
      h(NTag, { size: 'small' }, { default: () => row.category }),
  },
  {
    title: 'Description',
    key: 'description',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Amount',
    key: 'amount',
    width: 120,
    render: (row: ExpenseItem) => formatAmount(row.amount),
  },
  {
    title: 'Merchant',
    key: 'merchant_name',
    width: 140,
    render: (row: ExpenseItem) => row.merchant_name || '-',
  },
  {
    title: 'Date',
    key: 'transaction_date',
    width: 110,
    render: (row: ExpenseItem) => row.transaction_date || '-',
  },
  {
    title: 'Receipt',
    key: 'receipt',
    width: 140,
    render: (row: ExpenseItem) => {
      if (row.receipt_url) {
        return h('a', {
          href: row.receipt_url,
          target: '_blank',
          style: 'color: var(--brand-primary); text-decoration: none;',
        }, 'View')
      }
      return h(ReceiptUploader, {
        itemId: row.id,
        onUploaded: () => loadReport(),
      })
    },
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 140,
    render: (row: ExpenseItem) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'tiny',
            onClick: () => openEditItem(row),
          }, { default: () => 'Edit' }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteItem(row.id),
          }, {
            trigger: () => h(NButton, { size: 'tiny', type: 'error' }, { default: () => 'Del' }),
            default: () => 'Delete this item?',
          }),
        ],
      }),
  },
]

const totalAmount = computed(() => {
  return items.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const isDraft = computed(() => !report.value || report.value.status === 'draft')

onMounted(async () => {
  if (isEdit.value) {
    await loadReport()
  }
})

async function loadReport() {
  if (!reportId.value) return
  loading.value = true
  try {
    const { data } = await expenseReportApi.get(reportId.value)
    const r = data.data as ExpenseReport
    report.value = r
    title.value = r.title
    notes.value = r.notes || ''
    items.value = r.items || []
  } catch {
    message.error('Failed to load report')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!title.value.trim()) {
    message.warning('Title is required')
    return
  }

  saving.value = true
  try {
    if (isEdit.value && reportId.value) {
      await expenseReportApi.update(reportId.value, {
        title: title.value.trim(),
        notes: notes.value.trim() || undefined,
      })
      message.success('Report updated')
      await loadReport()
    } else {
      const { data } = await expenseReportApi.create({
        title: title.value.trim(),
        notes: notes.value.trim() || undefined,
      })
      const created = data.data as ExpenseReport
      message.success('Report created')
      router.replace({ name: 'expense-edit', params: { id: created.id } })
    }
  } catch {
    message.error('Failed to save report')
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  if (!reportId.value) return
  if (items.value.length === 0) {
    message.warning('Add at least one item before submitting')
    return
  }
  submitting.value = true
  try {
    await expenseReportApi.submit(reportId.value)
    message.success('Report submitted for approval')
    router.push({ name: 'expense-detail', params: { id: reportId.value } })
  } catch {
    message.error('Failed to submit report')
  } finally {
    submitting.value = false
  }
}

function openAddItem() {
  editingItem.value = null
  showItemForm.value = true
}

function openEditItem(item: ExpenseItem) {
  editingItem.value = item
  showItemForm.value = true
}

async function deleteItem(itemId: string) {
  try {
    await expenseItemApi.delete(itemId)
    message.success('Item deleted')
    await loadReport()
  } catch {
    message.error('Failed to delete item')
  }
}

function onItemSaved() {
  loadReport()
}
</script>

<template>
  <div class="expense-form-view">
    <div class="page-header">
      <h2>{{ isEdit ? 'Edit Expense Report' : 'New Expense Report' }}</h2>
      <NButton @click="router.push({ name: 'expenses' })">Back to List</NButton>
    </div>

    <NCard title="Report Details" style="margin-bottom: 20px">
      <div class="form-grid">
        <div class="form-field">
          <label>Title *</label>
          <NInput
            v-model:value="title"
            placeholder="e.g. March Business Travel"
            :disabled="!isDraft"
          />
        </div>
        <div class="form-field">
          <label>Notes</label>
          <NInput
            v-model:value="notes"
            type="textarea"
            placeholder="Additional notes (optional)"
            :rows="3"
            :disabled="!isDraft"
          />
        </div>
      </div>

      <NSpace style="margin-top: 16px">
        <NButton
          type="primary"
          :loading="saving"
          :disabled="!isDraft"
          @click="handleSave"
        >
          {{ isEdit ? 'Update Report' : 'Create Report' }}
        </NButton>
      </NSpace>
    </NCard>

    <NCard v-if="isEdit" title="Expense Items" style="margin-bottom: 20px">
      <template #header-extra>
        <NSpace align="center">
          <span class="total-label">
            Total: <strong>{{ formatAmount(totalAmount) }}</strong>
          </span>
          <NButton
            v-if="isDraft"
            type="primary"
            size="small"
            @click="openAddItem"
          >
            + Add Item
          </NButton>
        </NSpace>
      </template>

      <NDataTable
        :columns="itemColumns"
        :data="items"
        :loading="loading"
        :bordered="false"
        size="small"
      />

      <div v-if="isDraft && items.length > 0" style="margin-top: 20px; text-align: right">
        <NButton
          type="success"
          :loading="submitting"
          @click="handleSubmit"
        >
          Submit for Approval
        </NButton>
      </div>
    </NCard>

    <ExpenseItemForm
      v-if="reportId"
      v-model="showItemForm"
      :report-id="reportId"
      :item="editingItem"
      @saved="onItemSaved"
    />
  </div>
</template>

<style scoped>
.expense-form-view {
  padding: 24px;
  max-width: 1000px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.total-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.total-label strong {
  color: var(--text-primary);
  font-size: 16px;
}
</style>
