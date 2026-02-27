<script setup lang="ts">
import type { VatSummary } from '../../types/transaction'
import { currencyLocale } from '@/utils/currency'

defineProps<{
  summary: VatSummary
}>()

function fmt(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(n)) return '0.00'
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="vat-sheet">
    <h3>VAT Summary — {{ summary.period }}</h3>
    <div class="section">
      <div class="section-title">Part II — Sales/Receipts</div>
      <div class="row"><span>Line 1: Vatable Sales</span><span class="val">{{ fmt(summary.vatable_sales) }}</span></div>
      <div class="row"><span>Line 2: Sales to Government</span><span class="val">{{ fmt(summary.sales_to_government) }}</span></div>
      <div class="row"><span>Line 3: Zero Rated Sales</span><span class="val">{{ fmt(summary.zero_rated_sales) }}</span></div>
      <div class="row"><span>Line 4: VAT Exempt Sales</span><span class="val">{{ fmt(summary.vat_exempt_sales) }}</span></div>
      <div class="row total"><span>Line 5: Total Sales</span><span class="val">{{ fmt(summary.total_sales) }}</span></div>
    </div>

    <div class="section">
      <div class="section-title">Part III — Output Tax</div>
      <div class="row"><span>Line 6: Output VAT (12%)</span><span class="val">{{ fmt(summary.output_vat) }}</span></div>
      <div class="row"><span>Line 6A: Output VAT (Govt 5%)</span><span class="val">{{ fmt(summary.output_vat_government) }}</span></div>
      <div class="row total"><span>Line 6B: Total Output VAT</span><span class="val">{{ fmt(summary.total_output_vat) }}</span></div>
    </div>

    <div class="section">
      <div class="section-title">Part IV — Input Tax</div>
      <div class="row"><span>Line 7: Input VAT — Goods</span><span class="val">{{ fmt(summary.input_vat_goods) }}</span></div>
      <div class="row"><span>Line 8: Input VAT — Capital</span><span class="val">{{ fmt(summary.input_vat_capital) }}</span></div>
      <div class="row"><span>Line 9: Input VAT — Services</span><span class="val">{{ fmt(summary.input_vat_services) }}</span></div>
      <div class="row"><span>Line 10: Input VAT — Imports</span><span class="val">{{ fmt(summary.input_vat_imports) }}</span></div>
      <div class="row total"><span>Line 11: Total Input VAT</span><span class="val">{{ fmt(summary.total_input_vat) }}</span></div>
    </div>

    <div class="section net">
      <div class="row total"><span>Net VAT (Output - Input)</span><span class="val">{{ fmt(summary.net_vat) }}</span></div>
    </div>

    <div class="stats">
      <span>{{ summary.transaction_count }} transactions classified</span>
    </div>
  </div>
</template>

<style scoped>
.vat-sheet {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}
h3 { margin: 0 0 16px; font-size: 18px; color: #111827; }
.section { margin-bottom: 16px; }
.section-title {
  font-weight: 600;
  font-size: 13px;
  color: #6b7280;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 4px;
}
.row {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  font-size: 14px;
}
.row.total {
  font-weight: 600;
  background: #f9fafb;
  border-radius: 4px;
}
.val { font-variant-numeric: tabular-nums; }
.net .row.total { background: #eef2ff; color: #4f46e5; font-size: 16px; }
.stats { font-size: 12px; color: #9ca3af; text-align: right; padding-top: 8px; }
</style>
