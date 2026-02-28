<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Supplier, SupplierCreateData } from '../../types/withholding'

const props = defineProps<{
  supplier?: Supplier | null
  jurisdiction?: string
}>()

const isSG = computed(() => props.jurisdiction === 'SG')
const emit = defineEmits<{
  submit: [data: SupplierCreateData]
  cancel: []
}>()

const form = ref<SupplierCreateData>({
  tin: '',
  name: '',
  address: '',
  supplier_type: 'corporation',
  default_ewt_rate: undefined,
  default_atc_code: '',
  is_vat_registered: true,
})

watch(() => props.supplier, (s) => {
  if (s) {
    form.value = {
      tin: s.tin,
      name: s.name,
      address: s.address || '',
      supplier_type: s.supplier_type,
      default_ewt_rate: s.default_ewt_rate ?? undefined,
      default_atc_code: s.default_atc_code || '',
      is_vat_registered: s.is_vat_registered,
    }
  }
}, { immediate: true })

function handleSubmit() {
  if (!form.value.tin || !form.value.name) return
  emit('submit', { ...form.value })
}
</script>

<template>
  <form class="supplier-form" @submit.prevent="handleSubmit">
    <div class="form-row">
      <label>{{ isSG ? 'UEN *' : 'TIN *' }}</label>
      <input v-model="form.tin" :placeholder="isSG ? 'e.g. 201234567X' : 'e.g. 123-456-789-000'" required />
    </div>
    <div class="form-row">
      <label>Name *</label>
      <input v-model="form.name" placeholder="Supplier name" required />
    </div>
    <div class="form-row">
      <label>Address</label>
      <input v-model="form.address" placeholder="Address (optional)" />
    </div>
    <div class="form-row">
      <label>Type</label>
      <select v-model="form.supplier_type">
        <option value="corporation">Corporation</option>
        <option value="individual">Individual</option>
      </select>
    </div>
    <div class="form-row">
      <label>{{ isSG ? 'Default WHT Rate' : 'Default EWT Rate' }}</label>
      <input v-model.number="form.default_ewt_rate" type="number" step="0.01" min="0" max="1" :placeholder="isSG ? 'e.g. 0.15 for 15%' : 'e.g. 0.02 for 2%'" />
    </div>
    <div class="form-row">
      <label>{{ isSG ? 'Default WHT Nature' : 'Default ATC Code' }}</label>
      <input v-model="form.default_atc_code" :placeholder="isSG ? 'e.g. INT, ROY, TECH' : 'e.g. WC120'" />
    </div>
    <div class="form-row">
      <label>
        <input type="checkbox" v-model="form.is_vat_registered" />
        {{ isSG ? 'GST Registered' : 'VAT Registered' }}
      </label>
    </div>
    <div class="form-actions">
      <button type="button" class="btn ghost" @click="emit('cancel')">Cancel</button>
      <button type="submit" class="btn primary">{{ supplier ? 'Update' : 'Create' }}</button>
    </div>
  </form>
</template>

<style scoped>
.supplier-form { display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: 13px; font-weight: 500; color: #374151; }
.form-row input, .form-row select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.form-row input[type="checkbox"] { width: auto; margin-right: 8px; }
.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn.ghost { border: none; color: #6b7280; }
.btn.primary { background: #4f46e5; color: #fff; border-color: #4f46e5; }
.btn.primary:hover { background: #4338ca; }
</style>
