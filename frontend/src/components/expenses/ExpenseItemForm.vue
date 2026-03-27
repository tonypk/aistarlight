<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  NModal, NForm, NFormItem, NInput, NInputNumber,
  NSelect, NDatePicker, NButton, NSpace, useMessage,
} from 'naive-ui'
import type { FormRules, FormInst } from 'naive-ui'
import { expenseItemApi } from '../../api/expenses'
import type { ExpenseItem } from '../../types/expense'

const props = defineProps<{
  modelValue: boolean
  reportId: string
  item?: ExpenseItem | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const message = useMessage()
const formRef = ref<FormInst | null>(null)
const saving = ref(false)

const categoryOptions = [
  { label: 'Meals', value: 'meals' },
  { label: 'Transport', value: 'transport' },
  { label: 'Office Supplies', value: 'office_supplies' },
  { label: 'Travel', value: 'travel' },
  { label: 'Entertainment', value: 'entertainment' },
  { label: 'Other', value: 'other' },
]

const isEdit = computed(() => !!props.item?.id)

const formData = ref({
  category: '',
  description: '',
  amount: 0 as number | null,
  merchant_name: '',
  transaction_date: null as number | null,
  gl_account_id: '',
  policy_id: '',
})

const rules: FormRules = {
  category: { required: true, message: 'Category is required', trigger: 'change' },
  description: { required: true, message: 'Description is required', trigger: 'blur' },
  amount: { type: 'number', required: true, min: 0.01, message: 'Amount must be greater than 0', trigger: 'blur' },
  transaction_date: { type: 'number', required: true, message: 'Date is required', trigger: 'change' },
}

watch(() => props.modelValue, (visible) => {
  if (visible) {
    if (props.item) {
      formData.value = {
        category: props.item.category,
        description: props.item.description,
        amount: Number(props.item.amount),
        merchant_name: props.item.merchant_name || '',
        transaction_date: props.item.transaction_date
          ? new Date(props.item.transaction_date).getTime()
          : null,
        gl_account_id: props.item.gl_account_id || '',
        policy_id: props.item.policy_id || '',
      }
    } else {
      formData.value = {
        category: '',
        description: '',
        amount: null,
        merchant_name: '',
        transaction_date: null,
        gl_account_id: '',
        policy_id: '',
      }
    }
  }
})

function close() {
  emit('update:modelValue', false)
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const payload = {
      category: formData.value.category,
      description: formData.value.description,
      amount: formData.value.amount,
      merchant_name: formData.value.merchant_name || undefined,
      transaction_date: formData.value.transaction_date
        ? new Date(formData.value.transaction_date).toISOString().split('T')[0]
        : undefined,
      gl_account_id: formData.value.gl_account_id || undefined,
      policy_id: formData.value.policy_id || undefined,
    }

    if (isEdit.value && props.item) {
      await expenseItemApi.update(props.item.id, payload)
      message.success('Item updated')
    } else {
      await expenseItemApi.add(props.reportId, payload)
      message.success('Item added')
    }

    emit('saved')
    close()
  } catch {
    message.error('Failed to save item')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <NModal
    :show="modelValue"
    preset="card"
    :title="isEdit ? 'Edit Item' : 'Add Item'"
    :bordered="false"
    style="width: 520px; max-width: 95vw"
    @update:show="(v: boolean) => emit('update:modelValue', v)"
  >
    <NForm ref="formRef" :model="formData" :rules="rules" label-placement="top">
      <NFormItem label="Category" path="category">
        <NSelect
          v-model:value="formData.category"
          :options="categoryOptions"
          placeholder="Select category"
        />
      </NFormItem>

      <NFormItem label="Description" path="description">
        <NInput
          v-model:value="formData.description"
          placeholder="What was this expense for?"
        />
      </NFormItem>

      <NFormItem label="Amount" path="amount">
        <NInputNumber
          v-model:value="formData.amount"
          :min="0.01"
          :precision="2"
          placeholder="0.00"
          style="width: 100%"
        >
          <template #prefix>₱</template>
        </NInputNumber>
      </NFormItem>

      <NFormItem label="Merchant" path="merchant_name">
        <NInput
          v-model:value="formData.merchant_name"
          placeholder="Merchant name (optional)"
        />
      </NFormItem>

      <NFormItem label="Date" path="transaction_date">
        <NDatePicker
          v-model:value="formData.transaction_date"
          type="date"
          placeholder="Select date"
          style="width: 100%"
        />
      </NFormItem>

      <NFormItem label="GL Account ID" path="gl_account_id">
        <NInput
          v-model:value="formData.gl_account_id"
          placeholder="GL account UUID (optional)"
        />
      </NFormItem>

      <NFormItem label="Policy ID" path="policy_id">
        <NInput
          v-model:value="formData.policy_id"
          placeholder="Policy UUID (optional)"
        />
      </NFormItem>
    </NForm>

    <template #action>
      <NSpace justify="end">
        <NButton @click="close">Cancel</NButton>
        <NButton type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? 'Update' : 'Add' }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>
