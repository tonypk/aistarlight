<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NDataTable, NTabs, NTabPane, NTag, NEmpty,
} from 'naive-ui'
import { expenseReportApi } from '../../api/expenses'
import type { ExpenseReport } from '../../types/expense'

const router = useRouter()

const reports = ref<ExpenseReport[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)
const activeTab = ref('')

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Pending', value: 'pending_approval' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Paid', value: 'paid' },
]

function statusType(s: string): 'default' | 'info' | 'warning' | 'success' | 'error' {
  const map: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
    draft: 'default',
    submitted: 'info',
    pending_approval: 'warning',
    approved: 'success',
    rejected: 'error',
    paid: 'success',
  }
  return map[s] || 'default'
}

function formatAmount(amount: number | string): string {
  return `₱${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function statusLabel(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const columns = [
  {
    title: 'Report #',
    key: 'report_number',
    width: 160,
  },
  {
    title: 'Title',
    key: 'title',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Amount',
    key: 'total_amount',
    width: 130,
    render: (row: ExpenseReport) => formatAmount(row.total_amount),
  },
  {
    title: 'Status',
    key: 'status',
    width: 150,
    render: (row: ExpenseReport) =>
      h(NTag, { type: statusType(row.status), size: 'small', round: true }, {
        default: () => statusLabel(row.status),
      }),
  },
  {
    title: 'Created',
    key: 'created_at',
    width: 130,
    render: (row: ExpenseReport) => formatDate(row.created_at),
  },
]

onMounted(() => fetchReports())

async function fetchReports() {
  loading.value = true
  try {
    const { data } = await expenseReportApi.list({
      status: activeTab.value || undefined,
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

function onTabChange(tab: string) {
  activeTab.value = tab
  page.value = 1
  fetchReports()
}

function onPageChange(p: number) {
  page.value = p
  fetchReports()
}

function onRowClick(row: ExpenseReport) {
  router.push({ name: 'expense-detail', params: { id: row.id } })
}

function rowProps(row: ExpenseReport) {
  return {
    style: 'cursor: pointer',
    onClick: () => onRowClick(row),
  }
}
</script>

<template>
  <div class="expense-list-view">
    <div class="page-header">
      <h2>My Expenses</h2>
      <NButton type="primary" @click="router.push({ name: 'expense-new' })">
        + New Report
      </NButton>
    </div>

    <NTabs
      type="line"
      :value="activeTab"
      @update:value="onTabChange"
    >
      <NTabPane
        v-for="opt in statusOptions"
        :key="opt.value"
        :name="opt.value"
        :tab="opt.label"
      />
    </NTabs>

    <NDataTable
      :columns="columns"
      :data="reports"
      :loading="loading"
      :row-props="rowProps"
      :pagination="{
        page: page,
        pageSize: limit,
        itemCount: total,
        onUpdatePage: onPageChange,
        showSizePicker: false,
      }"
      :bordered="false"
      striped
      style="margin-top: 16px"
    />

    <NEmpty
      v-if="!loading && reports.length === 0"
      description="No expense reports found"
      style="margin-top: 40px"
    />
  </div>
</template>

<style scoped>
.expense-list-view {
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
