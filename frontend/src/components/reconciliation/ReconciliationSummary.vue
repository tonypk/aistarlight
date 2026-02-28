<script setup lang="ts">
import { computed } from 'vue'
import type { ReconciliationComparison } from '../../types/transaction'
import { currencyLocale, currencySymbol } from '@/utils/currency'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

defineProps<{
  comparison: ReconciliationComparison
  matchStats: {
    matched_pairs: number
    unmatched_records: number
    unmatched_bank: number
    match_rate: number
  }
}>()

function fmt(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(n)) return '0.00'
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const lineLabelsPH: Record<string, string> = {
  vatable_sales: 'Line 1 — Vatable Sales',
  sales_to_government: 'Line 2 — Sales to Government',
  zero_rated_sales: 'Line 3 — Zero Rated Sales',
  vat_exempt_sales: 'Line 4 — VAT Exempt Sales',
  total_sales: 'Line 5 — Total Sales',
  output_vat: 'Line 6 — Output VAT',
  output_vat_government: 'Line 6A — Output VAT (Govt)',
  total_output_vat: 'Line 6B — Total Output VAT',
  input_vat_goods: 'Line 7 — Input VAT Goods',
  input_vat_capital: 'Line 8 — Input VAT Capital',
  input_vat_services: 'Line 9 — Input VAT Services',
  input_vat_imports: 'Line 10 — Input VAT Imports',
  total_input_vat: 'Line 11 — Total Input VAT',
}

const lineLabelsSG: Record<string, string> = {
  vatable_sales: 'Box 1 — Standard-Rated Supplies',
  zero_rated_sales: 'Box 2 — Zero-Rated Supplies',
  vat_exempt_sales: 'Box 3 — Exempt Supplies',
  total_sales: 'Box 4 — Total Supplies',
  output_vat: 'Box 6 — Output Tax',
  total_input_vat: 'Box 7 — Input Tax',
}

const lineLabels = computed(() => isSG.value ? lineLabelsSG : lineLabelsPH)
</script>

<template>
  <div class="recon-summary">
    <div class="match-stats">
      <div class="stat">
        <div class="stat-val">{{ matchStats.matched_pairs }}</div>
        <div class="stat-label">Matched</div>
      </div>
      <div class="stat warn">
        <div class="stat-val">{{ matchStats.unmatched_records }}</div>
        <div class="stat-label">Unmatched Records</div>
      </div>
      <div class="stat warn">
        <div class="stat-val">{{ matchStats.unmatched_bank }}</div>
        <div class="stat-label">Unmatched Bank</div>
      </div>
      <div class="stat" :class="{ good: matchStats.match_rate > 0.8 }">
        <div class="stat-val">{{ (matchStats.match_rate * 100).toFixed(1) }}%</div>
        <div class="stat-label">Match Rate</div>
      </div>
    </div>

    <h3>Computed vs Declared</h3>
    <div class="comparison-table">
      <div class="comp-row header">
        <span>Line</span>
        <span class="num">Computed</span>
        <span class="num">Declared</span>
        <span class="num">Difference</span>
        <span class="status-col">Status</span>
      </div>
      <div
        v-for="line in comparison.comparisons"
        :key="line.line"
        class="comp-row"
        :class="{ mismatch: !line.match }"
      >
        <span>{{ lineLabels[line.label] ?? line.label }}</span>
        <span class="num">{{ fmt(line.computed) }}</span>
        <span class="num">{{ fmt(line.declared) }}</span>
        <span class="num" :class="{ 'diff-red': !line.match }">{{ fmt(line.difference) }}</span>
        <span class="status-col">
          <span v-if="line.match" class="match-ok">Match</span>
          <span v-else class="match-diff">Diff</span>
        </span>
      </div>
    </div>

    <div class="totals">
      <span>{{ comparison.matched_lines }}/{{ comparison.total_lines }} lines match</span>
      <span v-if="comparison.fully_matched" class="all-match">All lines match!</span>
      <span v-else class="total-diff">Total difference: {{ currencySymbol() }} {{ fmt(comparison.total_difference) }}</span>
    </div>
  </div>
</template>

<style scoped>
.recon-summary {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}
.match-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.stat {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}
.stat.warn .stat-val { color: #d97706; }
.stat.good .stat-val { color: #16a34a; }
.stat-val { font-size: 24px; font-weight: 700; color: #111827; }
.stat-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

h3 { font-size: 16px; margin: 0 0 12px; }

.comparison-table {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.comp-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 80px;
  padding: 10px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  align-items: center;
}
.comp-row.header {
  background: #f9fafb;
  font-weight: 600;
  font-size: 13px;
  color: #6b7280;
}
.comp-row.mismatch { background: #fef2f2; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.diff-red { color: #dc2626; font-weight: 600; }
.status-col { text-align: center; }
.match-ok { color: #16a34a; font-size: 12px; font-weight: 600; }
.match-diff { color: #dc2626; font-size: 12px; font-weight: 600; }

.totals {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 14px;
  color: #6b7280;
}
.all-match { color: #16a34a; font-weight: 600; }
.total-diff { color: #dc2626; font-weight: 600; }
</style>
