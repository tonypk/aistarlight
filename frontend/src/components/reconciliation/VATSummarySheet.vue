<script setup lang="ts">
import { computed } from 'vue'
import type { VatSummary } from '../../types/transaction'
import { currencyLocale } from '@/utils/currency'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

const props = defineProps<{
  summary: VatSummary
}>()

const validationWarnings = computed(() => props.summary.validation_warnings ?? [])
const hasErrors = computed(() => validationWarnings.value.some(w => w.severity === 'error'))

function fmt(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(n)) return '0.00'
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function severityIcon(severity: string): string {
  switch (severity) {
    case 'error': return '!!'
    case 'warning': return '!'
    default: return 'i'
  }
}
</script>

<template>
  <div class="vat-sheet">
    <h3>{{ isSG ? 'GST Summary' : 'VAT Summary' }} — {{ summary.period }}</h3>

    <!-- Validation Warnings -->
    <div v-if="validationWarnings.length" class="validation-panel" :class="{ 'has-errors': hasErrors }">
      <div class="validation-header">
        <span class="validation-title-icon" :class="hasErrors ? 'error' : 'warning'">
          {{ hasErrors ? '!!' : '!' }}
        </span>
        <strong>AI Validation: {{ validationWarnings.length }} issue(s) detected</strong>
      </div>
      <div
        v-for="(w, idx) in validationWarnings"
        :key="idx"
        class="validation-item"
        :class="w.severity"
      >
        <span class="severity-icon" :class="w.severity">{{ severityIcon(w.severity) }}</span>
        <span class="validation-msg">{{ w.message }}</span>
      </div>
    </div>

    <!-- Singapore GST layout -->
    <template v-if="isSG">
      <div class="section">
        <div class="section-title">Supplies</div>
        <div class="row"><span>Box 1: Standard-Rated Supplies</span><span class="val">{{ fmt(summary.vatable_sales) }}</span></div>
        <div class="row"><span>Box 2: Zero-Rated Supplies</span><span class="val">{{ fmt(summary.zero_rated_sales) }}</span></div>
        <div class="row"><span>Box 3: Exempt Supplies</span><span class="val">{{ fmt(summary.vat_exempt_sales) }}</span></div>
        <div class="row total"><span>Box 4: Total Supplies</span><span class="val">{{ fmt(summary.total_sales) }}</span></div>
      </div>

      <div class="section">
        <div class="section-title">Tax</div>
        <div class="row"><span>Box 6: Output Tax (9%)</span><span class="val">{{ fmt(summary.output_vat) }}</span></div>
        <div class="row"><span>Box 7: Input Tax</span><span class="val">{{ fmt(summary.total_input_vat) }}</span></div>
      </div>

      <div class="section net">
        <div class="row total"><span>Box 8: Net GST (Output - Input)</span><span class="val">{{ fmt(summary.net_vat) }}</span></div>
      </div>
    </template>

    <!-- Philippines VAT layout -->
    <template v-else>
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
    </template>

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

/* Validation warnings */
.validation-panel {
  border: 1px solid #f59e0b;
  background: #fffbeb;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 16px;
}
.validation-panel.has-errors {
  border-color: #ef4444;
  background: #fef2f2;
}
.validation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.validation-header strong {
  font-size: 14px;
  color: #92400e;
}
.validation-panel.has-errors .validation-header strong {
  color: #991b1b;
}
.validation-title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.validation-title-icon.error { background: #ef4444; }
.validation-title-icon.warning { background: #f59e0b; }
.validation-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  line-height: 1.4;
}
.validation-item + .validation-item {
  border-top: 1px solid rgba(0,0,0,0.06);
}
.severity-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  margin-top: 1px;
}
.severity-icon.error { background: #ef4444; }
.severity-icon.warning { background: #f59e0b; }
.severity-icon.info { background: #3b82f6; }
.validation-msg { color: #374151; }
.validation-item.error .validation-msg { color: #991b1b; }
.validation-item.warning .validation-msg { color: #78350f; }
.validation-item.info .validation-msg { color: #1e3a5f; }
</style>
