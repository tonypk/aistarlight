<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton, NDataTable, NSpace, NModal, NInput, NEmpty,
} from 'naive-ui'
import { expenseFinanceApi, expenseReportApi } from '../../api/expenses'
import type { ExpenseReport } from '../../types/expense'

const { t } = useI18n()

const reports = ref<ExpenseReport[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

const showPayModal = ref(false)
const paymentReference = ref('')
const payTargetId = ref<string | null>(null)
const actionLoading = ref<string | null>(null)

function formatAmount(amount: number | string): string {
  return `\u20B1${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const columns = [
  {
    title: 'Report #',
    key: 'report_number',
    width: 150,
  },
  {
    title: 'Title',
    key: 'title',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Amount',
    key: 'total_amount',
    width: 140,
    render: (row: ExpenseReport) => formatAmount(row.total_amount),
  },
  {
    title: 'Approved',
    key: 'approved_at',
    width: 130,
    render: (row: ExpenseReport) => formatDate(row.approved_at),
  },
  {
    title: 'Approver',
    key: 'approver_user_id',
    width: 130,
    ellipsis: { tooltip: true },
    render: (row: ExpenseReport) =>
      row.approver_user_id ? row.approver_user_id.substring(0, 8) + '...' : '-',
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 150,
    render: (row: ExpenseReport) =>
      h(NButton, {
        type: 'primary',
        size: 'small',
        loading: actionLoading.value === row.id,
        onClick: (e: Event) => {
          e.stopPropagation()
          openPayModal(row.id)
        },
      }, { default: () => 'Mark Paid' }),
  },
]

onMounted(() => fetchQueue())

async function fetchQueue() {
  loading.value = true
  try {
    const { data } = await expenseFinanceApi.queue({
      page: page.value,
      limit: limit.value,
    })
    reports.value = data.data || []
    total.value = data.meta?.total ?? 0
  } catch {
    // Error handled by axios interceptor
  } finally {
    loading.value = false
  }
}

function openPayModal(id: string) {
  payTargetId.value = id
  paymentReference.value = ''
  showPayModal.value = true
}

async function confirmMarkPaid() {
  if (!payTargetId.value) return
  actionLoading.value = payTargetId.value
  showPayModal.value = false
  try {
    await expenseReportApi.markPaid(payTargetId.value, {
      payment_reference: paymentReference.value || undefined,
    })
    await fetchQueue()
  } catch {
    // Error handled by interceptor
  } finally {
    actionLoading.value = null
    payTargetId.value = null
  }
}

function onPageChange(p: number) {
  page.value = p
  fetchQueue()
}
</script>

<template>
  <div class="finance-queue-view">
    <div class="page-header">
      <h2>Finance Payment Queue</h2>
    </div>

    <NDataTable
      :columns="columns"
      :data="reports"
      :loading="loading"
      :pagination="{
        page: page,
        pageSize: limit,
        itemCount: total,
        onUpdatePage: onPageChange,
        showSizePicker: false,
      }"
      :bordered="false"
      striped
    />

    <NEmpty
      v-if="!loading && reports.length === 0"
      description="No approved reports awaiting payment"
      style="margin-top: 40px"
    />

    <NModal
      v-model:show="showPayModal"
      preset="dialog"
      title="Mark as Paid"
      positive-text="Confirm Payment"
      negative-text="Cancel"
      type="success"
      @positive-click="confirmMarkPaid"
    >
      <div style="margin-top: 12px">
        <p style="margin: 0 0 8px; color: var(--text-secondary)">
          Enter payment reference (optional):
        </p>
        <NInput
          v-model:value="paymentReference"
          placeholder="e.g. Check #1234, Wire ref, etc."
        />
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.finance-queue-view {
  padding: 24px;
  max-width: 1200px;
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
</style>
