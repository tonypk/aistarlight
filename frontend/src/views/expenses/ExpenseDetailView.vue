<script setup lang="ts">
import { ref, h, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NCard, NSpace, NTag, NDataTable, NDescriptions,
  NDescriptionsItem, NPopconfirm, NTimeline, NTimelineItem,
  useMessage,
} from 'naive-ui'
import { expenseReportApi } from '../../api/expenses'
import type { ExpenseReport, ExpenseItem, ExpenseAudit } from '../../types/expense'
import RiskBadge from '../../components/expenses/RiskBadge.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const reportId = computed(() => route.params.id as string)
const loading = ref(false)
const report = ref<ExpenseReport | null>(null)
const items = ref<ExpenseItem[]>([])
const auditLog = ref<ExpenseAudit[]>([])

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

function statusLabel(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatAmount(amount: number | string): string {
  return `₱${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const isDraft = computed(() => report.value?.status === 'draft')
const isRejected = computed(() => report.value?.status === 'rejected')

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
    key: 'receipt_url',
    width: 100,
    render: (row: ExpenseItem) => {
      if (row.receipt_url) {
        return h('a', {
          href: row.receipt_url,
          target: '_blank',
          style: 'color: var(--brand-primary); text-decoration: none;',
        }, 'View')
      }
      return '-'
    },
  },
]

function auditTimelineType(action: string): 'default' | 'success' | 'error' | 'warning' | 'info' {
  const map: Record<string, 'default' | 'success' | 'error' | 'warning' | 'info'> = {
    created: 'info',
    submitted: 'info',
    ai_reviewed: 'warning',
    approved: 'success',
    rejected: 'error',
    paid: 'success',
    reverted: 'warning',
  }
  return map[action] || 'default'
}

onMounted(() => loadReport())

async function loadReport() {
  loading.value = true
  try {
    const { data } = await expenseReportApi.get(reportId.value)
    const r = data.data as ExpenseReport
    report.value = r
    items.value = r.items || []
    auditLog.value = r.audit_log || []
  } catch {
    message.error('Failed to load report')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  try {
    await expenseReportApi.submit(reportId.value)
    message.success('Report submitted')
    await loadReport()
  } catch {
    message.error('Failed to submit')
  }
}

async function handleDelete() {
  try {
    await expenseReportApi.delete(reportId.value)
    message.success('Report deleted')
    router.push({ name: 'expenses' })
  } catch {
    message.error('Failed to delete')
  }
}

async function handleRevert() {
  try {
    await expenseReportApi.revert(reportId.value)
    message.success('Report reverted to draft')
    await loadReport()
  } catch {
    message.error('Failed to revert')
  }
}
</script>

<template>
  <div class="expense-detail-view">
    <div class="page-header">
      <h2>Expense Report</h2>
      <NButton @click="router.push({ name: 'expenses' })">Back to List</NButton>
    </div>

    <div v-if="loading" class="loading-state">Loading...</div>

    <template v-if="report && !loading">
      <!-- Report Header -->
      <NCard style="margin-bottom: 20px">
        <NDescriptions :column="2" label-placement="left" bordered>
          <NDescriptionsItem label="Report #">
            {{ report.report_number }}
          </NDescriptionsItem>
          <NDescriptionsItem label="Status">
            <NTag :type="statusType(report.status)" round>
              {{ statusLabel(report.status) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="Title">
            {{ report.title }}
          </NDescriptionsItem>
          <NDescriptionsItem label="Total Amount">
            <strong>{{ formatAmount(report.total_amount) }}</strong>
          </NDescriptionsItem>
          <NDescriptionsItem label="Currency">
            {{ report.currency }}
          </NDescriptionsItem>
          <NDescriptionsItem label="Created">
            {{ formatDate(report.created_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.submitted_at" label="Submitted">
            {{ formatDateTime(report.submitted_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.notes" label="Notes" :span="2">
            {{ report.notes }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- AI Review Section -->
      <NCard
        v-if="report.ai_reviewed_at"
        title="AI Review"
        style="margin-bottom: 20px"
      >
        <NDescriptions :column="2" label-placement="left" bordered>
          <NDescriptionsItem label="Risk Score">
            <RiskBadge :score="report.ai_risk_score" />
          </NDescriptionsItem>
          <NDescriptionsItem label="Decision">
            <NTag
              v-if="report.ai_decision"
              :type="report.ai_decision === 'approve' ? 'success' : report.ai_decision === 'reject' ? 'error' : 'warning'"
              size="small"
            >
              {{ report.ai_decision }}
            </NTag>
            <span v-else>-</span>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.ai_decision_reason" label="Reason" :span="2">
            {{ report.ai_decision_reason }}
          </NDescriptionsItem>
          <NDescriptionsItem label="Reviewed At">
            {{ formatDateTime(report.ai_reviewed_at) }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- Approval Info -->
      <NCard
        v-if="report.approved_at || report.rejection_reason"
        title="Approval"
        style="margin-bottom: 20px"
      >
        <NDescriptions :column="2" label-placement="left" bordered>
          <NDescriptionsItem v-if="report.approved_at" label="Approved At">
            {{ formatDateTime(report.approved_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.rejection_reason" label="Rejection Reason" :span="2">
            <span class="rejection-text">{{ report.rejection_reason }}</span>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.paid_at" label="Paid At">
            {{ formatDateTime(report.paid_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="report.payment_reference" label="Payment Ref">
            {{ report.payment_reference }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- Items Table -->
      <NCard title="Items" style="margin-bottom: 20px">
        <NDataTable
          :columns="itemColumns"
          :data="items"
          :bordered="false"
          size="small"
        />
      </NCard>

      <!-- Audit Log -->
      <NCard v-if="auditLog.length > 0" title="Audit Log" style="margin-bottom: 20px">
        <NTimeline>
          <NTimelineItem
            v-for="entry in auditLog"
            :key="entry.id"
            :type="auditTimelineType(entry.action)"
            :title="entry.action.replace(/_/g, ' ').toUpperCase()"
            :content="`${entry.actor_name} (${entry.actor_type})`"
            :time="formatDateTime(entry.created_at)"
          />
        </NTimeline>
      </NCard>

      <!-- Action Buttons -->
      <NSpace>
        <NButton
          v-if="isDraft"
          type="primary"
          @click="router.push({ name: 'expense-edit', params: { id: report.id } })"
        >
          Edit
        </NButton>
        <NPopconfirm v-if="isDraft" @positive-click="handleDelete">
          <template #trigger>
            <NButton type="error">Delete</NButton>
          </template>
          Delete this report permanently?
        </NPopconfirm>
        <NButton
          v-if="isDraft && items.length > 0"
          type="success"
          @click="handleSubmit"
        >
          Submit
        </NButton>
        <NButton v-if="isRejected" type="warning" @click="handleRevert">
          Revert to Draft
        </NButton>
      </NSpace>
    </template>
  </div>
</template>

<style scoped>
.expense-detail-view {
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

.loading-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.rejection-text {
  color: #dc2626;
}
</style>
