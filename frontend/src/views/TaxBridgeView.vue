<script setup lang="ts">
import { ref } from 'vue'
import { useAccountingStore } from '../stores/accounting'
import { currencyLocale } from '@/utils/currency'

const store = useAccountingStore()

const formType = ref('BIR_2550M')
const periodMonth = ref(new Date().toISOString().slice(0, 7))
const year = ref(new Date().getFullYear())

const formTypes = [
  { value: 'BIR_2550M', label: 'BIR 2550M - Monthly VAT', period: 'month' },
  { value: 'BIR_2550Q', label: 'BIR 2550Q - Quarterly VAT', period: 'month' },
  { value: 'BIR_0619E', label: 'BIR 0619E - Monthly EWT', period: 'month' },
  { value: 'BIR_1701', label: 'BIR 1701 - Annual Individual IT', period: 'year' },
  { value: 'BIR_1702', label: 'BIR 1702 - Annual Corporate IT', period: 'year' },
]

const selectedForm = ref(formTypes[0])

function onFormChange() {
  selectedForm.value = formTypes.find(f => f.value === formType.value) || formTypes[0]
}

function getPeriodDates() {
  if (selectedForm.value.period === 'year') {
    return { start: `${year.value}-01-01`, end: `${year.value}-12-31` }
  }
  const [y, m] = periodMonth.value.split('-').map(Number)
  const start = `${y}-${String(m).padStart(2, '0')}-01`
  const lastDay = new Date(y, m, 0).getDate()
  const end = `${y}-${String(m).padStart(2, '0')}-${lastDay}`
  return { start, end }
}

async function calculate() {
  const { start, end } = getPeriodDates()
  await store.calculateTax(formType.value, start, end)
}

async function exportDAT() {
  await store.exportDAT(formType.value, periodMonth.value)
}

function fmt(val: string | undefined) {
  if (!val || val === '0') return '0.00'
  const n = parseFloat(val)
  if (isNaN(n)) return val
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// Display key fields based on form type
const resultDisplayConfig: Record<string, { label: string; key: string }[]> = {
  BIR_2550M: [
    { label: 'Line 1 - Vatable Sales', key: 'line_1_vatable_sales' },
    { label: 'Line 2 - Sales to Government', key: 'line_2_sales_to_government' },
    { label: 'Line 3 - Zero-Rated Sales', key: 'line_3_zero_rated_sales' },
    { label: 'Line 4 - Exempt Sales', key: 'line_4_exempt_sales' },
    { label: 'Line 5 - Total Sales', key: 'line_5_total_sales' },
    { label: 'Line 6 - Output VAT', key: 'line_6_output_vat' },
    { label: 'Line 11 - Total Input VAT', key: 'line_11_total_input_vat' },
    { label: 'Line 12 - VAT Payable', key: 'line_12_vat_payable' },
    { label: 'Line 14 - Net VAT Payable', key: 'line_14_net_vat_payable' },
    { label: 'Line 16 - Total Amount Due', key: 'line_16_total_amount_due' },
  ],
  BIR_0619E: [
    { label: 'Total Income Payments', key: 'total_income_payments' },
    { label: 'Total Taxes Withheld', key: 'total_taxes_withheld' },
    { label: 'Net EWT Due', key: 'net_ewt_due' },
    { label: 'Total Amount Due', key: 'total_amount_due' },
  ],
  BIR_1701: [
    { label: 'Gross Sales/Receipts', key: 'gross_sales_receipts' },
    { label: 'Cost of Sales', key: 'cost_of_sales' },
    { label: 'Gross Profit', key: 'gross_income' },
    { label: 'Itemized Deductions', key: 'total_deductions' },
    { label: 'Net Taxable Income', key: 'net_taxable_income' },
    { label: 'Tax Due', key: 'tax_due' },
    { label: 'Total Amount Due', key: 'total_amount_due' },
  ],
  BIR_1702: [
    { label: 'Gross Income', key: 'gross_income' },
    { label: 'Cost of Sales', key: 'cost_of_sales' },
    { label: 'Gross Profit', key: 'gross_profit' },
    { label: 'Operating Expenses', key: 'total_deductions' },
    { label: 'Net Taxable Income', key: 'net_taxable_income' },
    { label: 'RCIT', key: 'rcit' },
    { label: 'MCIT', key: 'mcit' },
    { label: 'Tax Due', key: 'tax_due' },
    { label: 'Total Amount Due', key: 'total_amount_due' },
  ],
}

function getDisplayFields() {
  return resultDisplayConfig[formType.value] || resultDisplayConfig['BIR_2550M']
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Tax Calculation from GL</h1>
      <p class="subtitle">Auto-populate BIR tax forms from General Ledger balances</p>
    </div>

    <div class="form-card">
      <div class="form-row">
        <label>
          BIR Form
          <select v-model="formType" @change="onFormChange" class="select">
            <option v-for="f in formTypes" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </label>

        <label v-if="selectedForm.period === 'month'">
          Period
          <input type="month" v-model="periodMonth" class="input" />
        </label>
        <label v-else>
          Year
          <input type="number" v-model="year" min="2020" max="2030" class="input" />
        </label>

        <button class="btn btn-primary" @click="calculate" :disabled="store.loading">
          {{ store.loading ? 'Calculating...' : 'Calculate from GL' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="store.taxResult" class="result-card">
      <div class="result-header">
        <h2>{{ store.taxResult.form_type }} Calculation Result</h2>
        <div class="result-actions">
          <button v-if="formType === 'BIR_2550M'" class="btn btn-secondary" @click="exportDAT">
            Export DAT File
          </button>
        </div>
      </div>

      <div class="result-meta">
        Period: {{ store.taxResult.period_start?.slice(0, 10) }} to {{ store.taxResult.period_end?.slice(0, 10) }}
        <span v-if="store.taxResult.result?.gl_source" class="gl-badge">From GL</span>
      </div>

      <table class="result-table">
        <tbody>
          <tr v-for="field in getDisplayFields()" :key="field.key" :class="{ highlight: field.key.includes('total') || field.key.includes('due') }">
            <td>{{ field.label }}</td>
            <td class="right mono">{{ fmt(store.taxResult.result?.[field.key]) }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Raw result expandable -->
      <details class="raw-section">
        <summary>View all fields</summary>
        <table class="result-table raw">
          <tbody>
            <tr v-for="(val, key) in store.taxResult.result" :key="key">
              <td>{{ key }}</td>
              <td class="right mono">{{ fmt(val) }}</td>
            </tr>
          </tbody>
        </table>
      </details>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 900px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; margin: 0; }
.subtitle { color: #6b7280; margin-top: 4px; font-size: 14px; }
.form-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
.form-row { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.form-row label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #374151; font-weight: 500; }
.input, .select { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
.select { min-width: 280px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn-secondary { background: #e5e7eb; color: #111; }
.btn-secondary:hover { background: #d1d5db; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.result-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.result-header h2 { margin: 0; font-size: 18px; }
.result-actions { display: flex; gap: 8px; }
.result-meta { font-size: 14px; color: #6b7280; margin-bottom: 16px; }
.gl-badge { display: inline-block; padding: 2px 8px; background: #dbeafe; color: #1d4ed8; border-radius: 4px; font-size: 12px; margin-left: 8px; }
.result-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.result-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; }
.result-table .highlight td { background: #f0f4ff; font-weight: 500; }
.right { text-align: right; }
.mono { font-family: monospace; }
.raw-section { margin-top: 16px; }
.raw-section summary { cursor: pointer; font-size: 13px; color: #6b7280; padding: 8px 0; }
.result-table.raw td { font-size: 13px; padding: 6px 12px; }
</style>
