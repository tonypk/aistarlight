<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import {
  NButton, NDataTable, NSpace, NModal, NForm, NFormItem,
  NInput, NInputNumber, NPopconfirm, NEmpty,
} from 'naive-ui'
import { expenseApproverApi } from '../../api/expenses'
import type { ExpenseApprover } from '../../types/expense'

const approvers = ref<ExpenseApprover[]>([])
const loading = ref(false)

const showModal = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)

const emptyForm = {
  approver_user_id: '',
  department_name: '',
  max_amount: null as number | null,
  priority: 1,
}

const form = ref({ ...emptyForm })

const modalTitle = computed(() => editingId.value ? 'Edit Approver' : 'Add Approver')

function formatAmount(amount: number | null): string {
  if (amount === null || amount === undefined) return 'Unlimited'
  return `\u20B1${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const columns = [
  {
    title: 'Name',
    key: 'approver_name',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Email',
    key: 'approver_email',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Department',
    key: 'department_name',
    width: 160,
  },
  {
    title: 'Max Amount',
    key: 'max_amount',
    width: 140,
    render: (row: ExpenseApprover) => formatAmount(row.max_amount),
  },
  {
    title: 'Priority',
    key: 'priority',
    width: 90,
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 160,
    render: (row: ExpenseApprover) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, {
            size: 'small',
            onClick: () => openEdit(row),
          }, { default: () => 'Edit' }),
          h(NPopconfirm, {
            onPositiveClick: () => handleDelete(row.id),
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
            }, { default: () => 'Delete' }),
            default: () => 'Are you sure you want to remove this approver?',
          }),
        ],
      }),
  },
]

onMounted(() => fetchApprovers())

async function fetchApprovers() {
  loading.value = true
  try {
    const { data } = await expenseApproverApi.list()
    approvers.value = data.data || []
  } catch {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.value = { ...emptyForm }
  showModal.value = true
}

function openEdit(approver: ExpenseApprover) {
  editingId.value = approver.id
  form.value = {
    approver_user_id: approver.approver_user_id,
    department_name: approver.department_name,
    max_amount: approver.max_amount,
    priority: approver.priority,
  }
  showModal.value = true
}

async function handleSave() {
  if (!form.value.approver_user_id.trim() || !form.value.department_name.trim()) return
  saving.value = true
  try {
    const payload = {
      approver_user_id: form.value.approver_user_id,
      department_name: form.value.department_name,
      max_amount: form.value.max_amount,
      priority: form.value.priority,
    }
    if (editingId.value) {
      await expenseApproverApi.update(editingId.value, payload)
    } else {
      await expenseApproverApi.create(payload)
    }
    showModal.value = false
    await fetchApprovers()
  } catch {
    // Error handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await expenseApproverApi.delete(id)
    await fetchApprovers()
  } catch {
    // Error handled by interceptor
  }
}
</script>

<template>
  <div class="approver-manage-view">
    <div class="page-header">
      <h2>Expense Approvers</h2>
      <NButton type="primary" @click="openAdd">
        + Add Approver
      </NButton>
    </div>

    <NDataTable
      :columns="columns"
      :data="approvers"
      :loading="loading"
      :bordered="false"
      striped
    />

    <NEmpty
      v-if="!loading && approvers.length === 0"
      description="No expense approvers configured"
      style="margin-top: 40px"
    />

    <NModal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="max-width: 480px"
      :mask-closable="false"
    >
      <NForm label-placement="top">
        <NFormItem label="Approver User ID" required>
          <NInput
            v-model:value="form.approver_user_id"
            placeholder="UUID of the approver user"
            :disabled="!!editingId"
          />
        </NFormItem>

        <NFormItem label="Department" required>
          <NInput
            v-model:value="form.department_name"
            placeholder="e.g. Engineering, Finance"
          />
        </NFormItem>

        <NFormItem label="Max Approval Amount (PHP)">
          <NInputNumber
            v-model:value="form.max_amount"
            :min="0"
            :precision="2"
            placeholder="Unlimited"
            style="width: 100%"
          >
            <template #prefix>&#8369;</template>
          </NInputNumber>
        </NFormItem>

        <NFormItem label="Priority">
          <NInputNumber
            v-model:value="form.priority"
            :min="1"
            :max="100"
            style="width: 100%"
          />
        </NFormItem>
      </NForm>

      <template #footer>
        <NSpace justify="end">
          <NButton @click="showModal = false">Cancel</NButton>
          <NButton
            type="primary"
            :loading="saving"
            :disabled="!form.approver_user_id.trim() || !form.department_name.trim()"
            @click="handleSave"
          >
            {{ editingId ? 'Update' : 'Create' }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.approver-manage-view {
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
