<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton, NDataTable, NSpace, NTag, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NSwitch, NPopconfirm, NEmpty,
} from 'naive-ui'
import { expensePolicyApi } from '../../api/expenses'
import type { ExpensePolicy } from '../../types/expense'

const { t } = useI18n()

const policies = ref<ExpensePolicy[]>([])
const loading = ref(false)

const showModal = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)

const emptyForm = {
  name: '',
  category: 'meals' as string,
  max_amount: null as number | null,
  requires_receipt_above: null as number | null,
  auto_approve_below: null as number | null,
  ai_auto_approve: false,
  description: '',
}

const form = ref({ ...emptyForm })

const categoryOptions = [
  { label: 'Meals', value: 'meals' },
  { label: 'Transport', value: 'transport' },
  { label: 'Office Supplies', value: 'office_supplies' },
  { label: 'Travel', value: 'travel' },
  { label: 'Entertainment', value: 'entertainment' },
  { label: 'Other', value: 'other' },
]

const modalTitle = computed(() => editingId.value ? 'Edit Policy' : 'Add Policy')

function formatAmount(amount: number | null): string {
  if (amount === null || amount === undefined) return '-'
  return `\u20B1${Number(amount).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function categoryLabel(val: string): string {
  const opt = categoryOptions.find(o => o.value === val)
  return opt ? opt.label : val
}

const columns = [
  {
    title: 'Name',
    key: 'name',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Category',
    key: 'category',
    width: 140,
    render: (row: ExpensePolicy) => categoryLabel(row.category),
  },
  {
    title: 'Max Amount',
    key: 'max_amount',
    width: 130,
    render: (row: ExpensePolicy) => formatAmount(row.max_amount),
  },
  {
    title: 'Receipt Above',
    key: 'requires_receipt_above',
    width: 130,
    render: (row: ExpensePolicy) => formatAmount(row.requires_receipt_above),
  },
  {
    title: 'Auto-Approve Below',
    key: 'auto_approve_below',
    width: 150,
    render: (row: ExpensePolicy) => formatAmount(row.auto_approve_below),
  },
  {
    title: 'AI Auto',
    key: 'ai_auto_approve',
    width: 90,
    render: (row: ExpensePolicy) =>
      h(NTag, {
        type: row.ai_auto_approve ? 'success' : 'default',
        size: 'small',
        round: true,
      }, { default: () => row.ai_auto_approve ? 'Yes' : 'No' }),
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 160,
    render: (row: ExpensePolicy) =>
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
            default: () => 'Are you sure you want to delete this policy?',
          }),
        ],
      }),
  },
]

onMounted(() => fetchPolicies())

async function fetchPolicies() {
  loading.value = true
  try {
    const { data } = await expensePolicyApi.list()
    policies.value = data.data || []
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

function openEdit(policy: ExpensePolicy) {
  editingId.value = policy.id
  form.value = {
    name: policy.name,
    category: policy.category,
    max_amount: policy.max_amount,
    requires_receipt_above: policy.requires_receipt_above,
    auto_approve_below: policy.auto_approve_below,
    ai_auto_approve: policy.ai_auto_approve,
    description: policy.description || '',
  }
  showModal.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      category: form.value.category,
      max_amount: form.value.max_amount,
      requires_receipt_above: form.value.requires_receipt_above,
      auto_approve_below: form.value.auto_approve_below,
      ai_auto_approve: form.value.ai_auto_approve,
      description: form.value.description || null,
    }
    if (editingId.value) {
      await expensePolicyApi.update(editingId.value, payload)
    } else {
      await expensePolicyApi.create(payload)
    }
    showModal.value = false
    await fetchPolicies()
  } catch {
    // Error handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await expensePolicyApi.delete(id)
    await fetchPolicies()
  } catch {
    // Error handled by interceptor
  }
}
</script>

<template>
  <div class="policy-manage-view">
    <div class="page-header">
      <h2>Expense Policies</h2>
      <NButton type="primary" @click="openAdd">
        + Add Policy
      </NButton>
    </div>

    <NDataTable
      :columns="columns"
      :data="policies"
      :loading="loading"
      :bordered="false"
      striped
    />

    <NEmpty
      v-if="!loading && policies.length === 0"
      description="No expense policies configured"
      style="margin-top: 40px"
    />

    <NModal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="max-width: 520px"
      :mask-closable="false"
    >
      <NForm label-placement="top">
        <NFormItem label="Name" required>
          <NInput v-model:value="form.name" placeholder="Policy name" />
        </NFormItem>

        <NFormItem label="Category">
          <NSelect
            v-model:value="form.category"
            :options="categoryOptions"
            placeholder="Select category"
          />
        </NFormItem>

        <NFormItem label="Max Amount (PHP)">
          <NInputNumber
            v-model:value="form.max_amount"
            :min="0"
            :precision="2"
            placeholder="No limit"
            style="width: 100%"
          >
            <template #prefix>&#8369;</template>
          </NInputNumber>
        </NFormItem>

        <NFormItem label="Requires Receipt Above (PHP)">
          <NInputNumber
            v-model:value="form.requires_receipt_above"
            :min="0"
            :precision="2"
            placeholder="No threshold"
            style="width: 100%"
          >
            <template #prefix>&#8369;</template>
          </NInputNumber>
        </NFormItem>

        <NFormItem label="Auto-Approve Below (PHP)">
          <NInputNumber
            v-model:value="form.auto_approve_below"
            :min="0"
            :precision="2"
            placeholder="No auto-approve"
            style="width: 100%"
          >
            <template #prefix>&#8369;</template>
          </NInputNumber>
        </NFormItem>

        <NFormItem label="AI Auto-Approve">
          <NSwitch v-model:value="form.ai_auto_approve" />
        </NFormItem>

        <NFormItem label="Description">
          <NInput
            v-model:value="form.description"
            type="textarea"
            placeholder="Optional description"
            :rows="3"
          />
        </NFormItem>
      </NForm>

      <template #footer>
        <NSpace justify="end">
          <NButton @click="showModal = false">Cancel</NButton>
          <NButton
            type="primary"
            :loading="saving"
            :disabled="!form.name.trim()"
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
.policy-manage-view {
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
