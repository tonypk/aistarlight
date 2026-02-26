<script setup lang="ts">
import { ref } from 'vue'
import { client } from '../api/client'

interface ComparisonRow {
  field: string
  period_a: number | null
  period_b: number | null
  diff: number | null
  pct_change: number | null
}

interface CompareResult {
  period_a: string
  period_b: string
  report_type: string
  has_report_a: boolean
  has_report_b: boolean
  comparison: ComparisonRow[]
}

const periodA = ref('')
const periodB = ref('')
const reportType = ref('BIR_2550M')
const loading = ref(false)
const result = ref<CompareResult | null>(null)
const error = ref('')

const reportTypes = [
  { value: 'BIR_2550M', label: 'BIR 2550M — Monthly VAT' },
  { value: 'BIR_2550Q', label: 'BIR 2550Q — Quarterly VAT' },
  { value: 'BIR_1601C', label: 'BIR 1601-C — Withholding Tax' },
  { value: 'BIR_0619E', label: 'BIR 0619-E — Expanded Withholding' },
  { value: 'BIR_1701', label: 'BIR 1701 — Annual ITR (Individual)' },
  { value: 'BIR_1702', label: 'BIR 1702 — Annual ITR (Corporate)' },
]

// Generate recent periods (last 12 months)
function recentPeriods(): string[] {
  const periods: string[] = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    periods.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return periods
}

const periods = recentPeriods()

async function runComparison() {
  if (!periodA.value || !periodB.value) {
    error.value = 'Please select both periods'
    return
  }
  if (periodA.value === periodB.value) {
    error.value = 'Please select two different periods'
    return
  }
  error.value = ''
  loading.value = true
  result.value = null
  try {
    const res = await client.get('/dashboard/compare', {
      params: {
        period_a: periodA.value,
        period_b: periodB.value,
        report_type: reportType.value,
      },
    })
    result.value = res.data.data
  } catch {
    error.value = 'Failed to load comparison data'
  } finally {
    loading.value = false
  }
}

function formatNumber(val: number | null): string {
  if (val === null || val === undefined) return '—'
  return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatPct(val: number | null): string {
  if (val === null || val === undefined) return '—'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

function diffClass(val: number | null): string {
  if (val === null || val === undefined) return ''
  if (val > 0) return 'positive'
  if (val < 0) return 'negative'
  return 'zero'
}

function fieldLabel(field: string): string {
  return field
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="compare-view">
    <h2>Period Comparison</h2>
    <p class="subtitle">Compare report data between two filing periods to identify trends and changes.</p>

    <div class="controls">
      <div class="control-group">
        <label>Report Type</label>
        <select v-model="reportType">
          <option v-for="rt in reportTypes" :key="rt.value" :value="rt.value">{{ rt.label }}</option>
        </select>
      </div>
      <div class="control-group">
        <label>Period A (Base)</label>
        <select v-model="periodA">
          <option value="" disabled>Select period...</option>
          <option v-for="p in periods" :key="'a-' + p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="control-group">
        <label>Period B (Compare)</label>
        <select v-model="periodB">
          <option value="" disabled>Select period...</option>
          <option v-for="p in periods" :key="'b-' + p" :value="p">{{ p }}</option>
        </select>
      </div>
      <button class="compare-btn" :disabled="loading" @click="runComparison">
        {{ loading ? 'Comparing...' : 'Compare' }}
      </button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="result" class="result-section">
      <div class="result-header">
        <div class="result-meta">
          <span class="meta-item">
            <strong>{{ result.report_type.replace('_', ' ') }}</strong>
          </span>
          <span class="meta-item" :class="{ missing: !result.has_report_a }">
            Period A: {{ result.period_a }} {{ result.has_report_a ? '' : '(no data)' }}
          </span>
          <span class="meta-item" :class="{ missing: !result.has_report_b }">
            Period B: {{ result.period_b }} {{ result.has_report_b ? '' : '(no data)' }}
          </span>
        </div>
      </div>

      <div v-if="result.comparison.length === 0" class="empty">
        No numeric fields to compare between these periods.
      </div>

      <table v-else class="compare-table">
        <thead>
          <tr>
            <th>Field</th>
            <th class="num">{{ result.period_a }}</th>
            <th class="num">{{ result.period_b }}</th>
            <th class="num">Difference</th>
            <th class="num">% Change</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in result.comparison" :key="row.field">
            <td class="field-name">{{ fieldLabel(row.field) }}</td>
            <td class="num">{{ formatNumber(row.period_a) }}</td>
            <td class="num">{{ formatNumber(row.period_b) }}</td>
            <td class="num" :class="diffClass(row.diff)">
              {{ row.diff !== null ? (row.diff > 0 ? '+' : '') + formatNumber(row.diff) : '—' }}
            </td>
            <td class="num" :class="diffClass(row.pct_change)">
              {{ formatPct(row.pct_change) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.compare-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { margin: 0 0 4px; }
.subtitle { color: #64748b; font-size: 14px; margin: 0 0 24px; }

.controls {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}
.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.control-group label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}
.control-group select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-width: 180px;
}
.compare-btn {
  padding: 8px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  height: 38px;
}
.compare-btn:hover { background: #4338ca; }
.compare-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.error-msg {
  color: #dc2626;
  background: #fef2f2;
  padding: 10px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.result-section { margin-top: 8px; }
.result-header { margin-bottom: 16px; }
.result-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.meta-item {
  font-size: 14px;
  color: #374151;
}
.meta-item.missing { color: #d97706; }

.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.compare-table th {
  text-align: left;
  padding: 10px 14px;
  background: #f8fafc;
  font-weight: 500;
  color: #64748b;
  font-size: 13px;
}
.compare-table th.num { text-align: right; }
.compare-table td {
  padding: 10px 14px;
  border-top: 1px solid #f1f5f9;
}
.compare-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.field-name {
  font-weight: 500;
  color: #1e293b;
}
.positive { color: #dc2626; font-weight: 500; }
.negative { color: #16a34a; font-weight: 500; }
.zero { color: #64748b; }

.empty {
  text-align: center;
  padding: 48px;
  color: #94a3b8;
}
</style>
