<script setup lang="ts">
import { ref, computed } from 'vue'
import { client } from '../api/client'
import { currencySymbol, formatCurrency } from '@/utils/currency'
import { useAuthStore } from '../stores/auth'
import { getReportTypes } from '../config/targetFieldsByReportType'

interface PenaltyResult {
  surcharge: number
  interest: number
  compromise: number
  total_penalty: number
  details: {
    surcharge_rate: string
    interest_rate: string
    surcharge_ref: string
    interest_ref: string
    compromise_ref: string
  }
}

const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

const formType = ref(auth.jurisdiction === 'SG' ? 'IRAS_GST_F5' : 'BIR_2550M')
const period = ref('')
const daysLate = ref(30)
const taxDue = ref(0)
const result = ref<PenaltyResult | null>(null)
const loading = ref(false)
const error = ref('')

const formTypes = computed(() => getReportTypes(auth.jurisdiction).filter(r => r.value !== 'Bank_Statement'))

async function calculate() {
  if (!period.value || daysLate.value <= 0 || taxDue.value <= 0) {
    error.value = 'Please fill in all fields with valid values.'
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await client.post('/compliance/calculate-penalty', {
      form_type: formType.value,
      period: period.value,
      days_late: daysLate.value,
      tax_due: taxDue.value,
    })
    result.value = res.data.data
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Calculation failed'
  } finally {
    loading.value = false
  }
}

function formatPeso(val: number): string {
  return formatCurrency(val)
}
</script>

<template>
  <div class="penalty-calc">
    <h2>Penalty Calculator</h2>
    <p class="subtitle">{{ isSG ? 'Calculate late filing penalties for IRAS returns' : 'Calculate surcharge, interest, and compromise penalties for late BIR filings' }}</p>

    <div class="form-grid">
      <div class="field">
        <label>Form Type</label>
        <select v-model="formType">
          <option v-for="ft in formTypes" :key="ft.value" :value="ft.value">{{ ft.label }}</option>
        </select>
      </div>
      <div class="field">
        <label>Period (YYYY-MM)</label>
        <input v-model="period" type="month" placeholder="2026-01" />
      </div>
      <div class="field">
        <label>Days Late</label>
        <input v-model.number="daysLate" type="number" min="1" />
      </div>
      <div class="field">
        <label>Basic Tax Due ({{ currencySymbol() }})</label>
        <input v-model.number="taxDue" type="number" min="0" step="0.01" />
      </div>
    </div>

    <button class="calc-btn" :disabled="loading" @click="calculate">
      {{ loading ? 'Calculating...' : 'Calculate Penalty' }}
    </button>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="result" class="result-card">
      <h3>Penalty Breakdown</h3>
      <table class="result-table">
        <tbody>
          <tr>
            <td>Surcharge ({{ (parseFloat(result.details.surcharge_rate) * 100).toFixed(0) }}%)</td>
            <td class="amount">{{ formatPeso(result.surcharge) }}</td>
            <td class="ref">{{ result.details.surcharge_ref }}</td>
          </tr>
          <tr>
            <td>Interest ({{ (parseFloat(result.details.interest_rate) * 100).toFixed(0) }}% p.a. x {{ daysLate }} days)</td>
            <td class="amount">{{ formatPeso(result.interest) }}</td>
            <td class="ref">{{ result.details.interest_ref }}</td>
          </tr>
          <tr>
            <td>Compromise Penalty</td>
            <td class="amount">{{ formatPeso(result.compromise) }}</td>
            <td class="ref">{{ result.details.compromise_ref }}</td>
          </tr>
          <tr class="total-row">
            <td><strong>Total Penalty</strong></td>
            <td class="amount"><strong>{{ formatPeso(result.total_penalty) }}</strong></td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.penalty-calc { max-width: 800px; }
.penalty-calc h2 { margin-bottom: 4px; }
.subtitle { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  color: #374151;
}
.field input, .field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}
.calc-btn {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.calc-btn:disabled { opacity: 0.6; }
.error {
  margin-top: 12px;
  color: #dc2626;
  font-size: 14px;
}
.result-card {
  margin-top: 24px;
  padding: 20px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}
.result-card h3 { margin-bottom: 16px; font-size: 16px; }
.result-table {
  width: 100%;
  border-collapse: collapse;
}
.result-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}
.result-table .amount { text-align: right; font-variant-numeric: tabular-nums; }
.result-table .ref { color: #6b7280; font-size: 12px; text-align: right; }
.total-row td {
  border-top: 2px solid #374151;
  border-bottom: none;
  padding-top: 12px;
}
</style>
