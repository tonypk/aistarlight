<script setup lang="ts">
import { ref } from 'vue'

const mappings = ref<Record<string, string>>({})
const targetFields = [
  { value: 'date', label: 'Date' },
  { value: 'description', label: 'Description' },
  { value: 'amount', label: 'Amount' },
  { value: 'vat_amount', label: 'VAT Amount' },
  { value: 'vat_type', label: 'VAT Type' },
  { value: 'category', label: 'Category' },
  { value: 'tin', label: 'TIN' },
  { value: '_skip', label: '-- Skip --' },
]

// Placeholder columns - will come from upload store in full implementation
const sourceColumns = ref(['Date', 'Customer', 'Description', 'Amount', 'VAT', 'Total'])

function confirmMapping() {
  // TODO: Save mapping and proceed to report generation
  alert('Mapping confirmed! Proceed to report generation.')
}
</script>

<template>
  <div class="mapping-view">
    <h2>Column Mapping</h2>
    <p class="desc">Map your spreadsheet columns to BIR form fields</p>

    <div class="mapping-table">
      <div class="mapping-row header">
        <span>Your Column</span>
        <span>Maps To</span>
      </div>
      <div v-for="col in sourceColumns" :key="col" class="mapping-row">
        <span class="source">{{ col }}</span>
        <select v-model="mappings[col]">
          <option value="">-- Select --</option>
          <option v-for="f in targetFields" :key="f.value" :value="f.value">
            {{ f.label }}
          </option>
        </select>
      </div>
    </div>

    <button class="confirm-btn" @click="confirmMapping">Confirm Mapping</button>
  </div>
</template>

<style scoped>
.mapping-view h2 { margin-bottom: 8px; }
.desc { color: #888; margin-bottom: 24px; }
.mapping-table {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
.mapping-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 12px 20px;
  border-bottom: 1px solid #f3f4f6;
  align-items: center;
}
.mapping-row.header {
  background: #f9fafb;
  font-weight: 600;
  font-size: 13px;
  color: #888;
}
.source { font-weight: 500; }
select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.confirm-btn {
  margin-top: 24px;
  padding: 12px 32px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.confirm-btn:hover { background: #4338ca; }
</style>
