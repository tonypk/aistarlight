<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NCard, NGrid, NGi, NDataTable, NDatePicker, NStatistic, NSpace, NEmpty,
} from 'naive-ui'
import { expenseAnalyticsApi } from '../../api/expenses'
import type { ExpenseSpendSummary, SpendByCategory, SpendByDepartment } from '../../types/expense'

const { t } = useI18n()

const loading = ref(false)

const summary = ref<ExpenseSpendSummary>({
  approved_count: 0,
  paid_count: 0,
  pending_count: 0,
  total_approved: 0,
  total_paid: 0,
  total_pending: 0,
})

const byCategory = ref<SpendByCategory[]>([])
const byDepartment = ref<SpendByDepartment[]>([])

// Default to current month
function getDefaultRange(): [number, number] {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)
  return [start.getTime(), end.getTime()]
}

const dateRange = ref<[number, number]>(getDefaultRange())

function formatAmount(amount: number | string): string {
  return `\u20B1${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDateParam(ts: number): string {
  const d = new Date(ts)
  return d.toISOString().split('T')[0]
}

function categoryLabel(val: string): string {
  const labels: Record<string, string> = {
    meals: 'Meals',
    transport: 'Transport',
    office_supplies: 'Office Supplies',
    travel: 'Travel',
    entertainment: 'Entertainment',
    other: 'Other',
  }
  return labels[val] || val.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const categoryColumns = [
  {
    title: 'Category',
    key: 'category',
    render: (row: SpendByCategory) => categoryLabel(row.category),
  },
  {
    title: 'Total Amount',
    key: 'total_amount',
    width: 160,
    render: (row: SpendByCategory) => formatAmount(row.total_amount),
  },
  {
    title: 'Item Count',
    key: 'item_count',
    width: 120,
  },
]

const departmentColumns = [
  {
    title: 'Department',
    key: 'department',
  },
  {
    title: 'Total Amount',
    key: 'total_amount',
    width: 160,
    render: (row: SpendByDepartment) => formatAmount(row.total_amount),
  },
  {
    title: 'Report Count',
    key: 'report_count',
    width: 120,
  },
]

onMounted(() => fetchAnalytics())

async function fetchAnalytics() {
  loading.value = true
  try {
    const params: { from?: string; to?: string } = {}
    if (dateRange.value) {
      params.from = formatDateParam(dateRange.value[0])
      params.to = formatDateParam(dateRange.value[1])
    }
    const { data } = await expenseAnalyticsApi.get(params)
    const result = data.data
    summary.value = result.summary || summary.value
    byCategory.value = result.by_category || []
    byDepartment.value = result.by_department || []
  } catch {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

function onDateRangeChange(val: [number, number] | null) {
  if (val) {
    dateRange.value = val
  } else {
    dateRange.value = getDefaultRange()
  }
  fetchAnalytics()
}
</script>

<template>
  <div class="expense-analytics-view">
    <div class="page-header">
      <h2>Expense Analytics</h2>
      <NDatePicker
        type="daterange"
        :value="dateRange"
        clearable
        @update:value="onDateRangeChange"
        style="width: 300px"
      />
    </div>

    <!-- Summary Cards -->
    <NGrid :x-gap="16" :y-gap="16" :cols="3" style="margin-bottom: 24px">
      <NGi>
        <NCard size="small">
          <NStatistic label="Approved" :value="summary.approved_count">
            <template #suffix>reports</template>
          </NStatistic>
          <div class="stat-amount">{{ formatAmount(summary.total_approved) }}</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard size="small">
          <NStatistic label="Paid" :value="summary.paid_count">
            <template #suffix>reports</template>
          </NStatistic>
          <div class="stat-amount">{{ formatAmount(summary.total_paid) }}</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard size="small">
          <NStatistic label="Pending" :value="summary.pending_count">
            <template #suffix>reports</template>
          </NStatistic>
          <div class="stat-amount">{{ formatAmount(summary.total_pending) }}</div>
        </NCard>
      </NGi>
    </NGrid>

    <!-- Category Breakdown -->
    <NCard title="Spend by Category" size="small" style="margin-bottom: 24px">
      <NDataTable
        :columns="categoryColumns"
        :data="byCategory"
        :loading="loading"
        :bordered="false"
        striped
        size="small"
      />
      <NEmpty
        v-if="!loading && byCategory.length === 0"
        description="No category data for this period"
        style="padding: 24px 0"
      />
    </NCard>

    <!-- Department Breakdown -->
    <NCard title="Spend by Department" size="small">
      <NDataTable
        :columns="departmentColumns"
        :data="byDepartment"
        :loading="loading"
        :bordered="false"
        striped
        size="small"
      />
      <NEmpty
        v-if="!loading && byDepartment.length === 0"
        description="No department data for this period"
        style="padding: 24px 0"
      />
    </NCard>
  </div>
</template>

<style scoped>
.expense-analytics-view {
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

.stat-amount {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
