<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NDataTable, NSpace, NTag, NModal, NInput, NEmpty,
} from 'naive-ui'
import { expenseApprovalApi, expenseReportApi } from '../../api/expenses'
import type { ExpenseReport } from '../../types/expense'

const router = useRouter()

const reports = ref<ExpenseReport[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

const showRejectModal = ref(false)
const rejectReason = ref('')
const rejectTargetId = ref<string | null>(null)
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

function riskTagType(score: number | null): 'success' | 'warning' | 'error' | 'default' {
  if (score === null || score === undefined) return 'default'
  if (score < 30) return 'success'
  if (score <= 70) return 'warning'
  return 'error'
}

function riskLabel(score: number | null): string {
  if (score === null || score === undefined) return 'N/A'
  return String(score)
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
    title: 'Submitter',
    key: 'submitter_user_id',
    width: 130,
    ellipsis: { tooltip: true },
    render: (row: ExpenseReport) => row.submitter_user_id?.substring(0, 8) + '...',
  },
  {
    title: 'Amount',
    key: 'total_amount',
    width: 130,
    render: (row: ExpenseReport) => formatAmount(row.total_amount),
  },
  {
    title: 'Submitted',
    key: 'submitted_at',
    width: 130,
    render: (row: ExpenseReport) => formatDate(row.submitted_at),
  },
  {
    title: 'Risk Score',
    key: 'ai_risk_score',
    width: 110,
    render: (row: ExpenseReport) =>
      h(NTag, { type: riskTagType(row.ai_risk_score), size: 'small', round: true }, {
        default: () => riskLabel(row.ai_risk_score),
      }),
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 200,
    render: (row: ExpenseReport) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, {
            type: 'success',
            size: 'small',
            loading: actionLoading.value === `approve-${row.id}`,
            onClick: (e: Event) => {
              e.stopPropagation()
              handleApprove(row.id)
            },
          }, { default: () => 'Approve' }),
          h(NButton, {
            type: 'error',
            size: 'small',
            onClick: (e: Event) => {
              e.stopPropagation()
              openRejectModal(row.id)
            },
          }, { default: () => 'Reject' }),
        ],
      }),
  },
]

onMounted(() => fetchPending())

async function fetchPending() {
  loading.value = true
  try {
    const { data } = await expenseApprovalApi.listPending({
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

async function handleApprove(id: string) {
  actionLoading.value = `approve-${id}`
  try {
    await expenseReportApi.approve(id)
    await fetchPending()
  } catch {
    // Error handled by interceptor
  } finally {
    actionLoading.value = null
  }
}

function openRejectModal(id: string) {
  rejectTargetId.value = id
  rejectReason.value = ''
  showRejectModal.value = true
}

async function confirmReject() {
  if (!rejectTargetId.value) return
  actionLoading.value = `reject-${rejectTargetId.value}`
  showRejectModal.value = false
  try {
    await expenseReportApi.reject(rejectTargetId.value, { reason: rejectReason.value })
    await fetchPending()
  } catch {
    // Error handled by interceptor
  } finally {
    actionLoading.value = null
    rejectTargetId.value = null
  }
}

function onPageChange(p: number) {
  page.value = p
  fetchPending()
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
  <div class="approval-queue-view">
    <div class="page-header">
      <h2>Approval Queue</h2>
    </div>

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
    />

    <NEmpty
      v-if="!loading && reports.length === 0"
      description="No reports pending approval"
      style="margin-top: 40px"
    />

    <NModal
      v-model:show="showRejectModal"
      preset="dialog"
      title="Reject Report"
      positive-text="Reject"
      negative-text="Cancel"
      type="error"
      @positive-click="confirmReject"
    >
      <div style="margin-top: 12px">
        <p style="margin: 0 0 8px; color: var(--text-secondary)">
          Please provide a reason for rejection:
        </p>
        <NInput
          v-model:value="rejectReason"
          type="textarea"
          placeholder="Reason for rejection"
          :rows="3"
        />
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.approval-queue-view {
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
