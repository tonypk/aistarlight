<script setup lang="ts">
import { computed } from 'vue'
import type { Transaction } from '../../types/transaction'

const props = defineProps<{
  transactions: Transaction[]
}>()

const stats = computed(() => {
  const txns = props.transactions
  const total = txns.length
  const vatable = txns.filter((t) => t.vat_type === 'vatable').length
  const exempt = txns.filter((t) => t.vat_type === 'exempt').length
  const zeroRated = txns.filter((t) => t.vat_type === 'zero_rated').length
  const government = txns.filter((t) => t.vat_type === 'government').length
  const totalAmount = txns.reduce((sum, t) => sum + t.amount, 0)

  const highConf = txns.filter((t) => t.confidence >= 0.8).length
  const medConf = txns.filter((t) => t.confidence >= 0.5 && t.confidence < 0.8).length
  const lowConf = txns.filter((t) => t.confidence < 0.5).length

  return {
    total,
    totalAmount,
    vatable,
    exempt,
    zeroRated,
    government,
    highConf,
    medConf,
    lowConf,
    highPct: total ? ((highConf / total) * 100).toFixed(0) : '0',
    medPct: total ? ((medConf / total) * 100).toFixed(0) : '0',
    lowPct: total ? ((lowConf / total) * 100).toFixed(0) : '0',
  }
})

function fmt(n: number): string {
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="summary-cards">
    <div class="card">
      <div class="card-label">Total</div>
      <div class="card-value">{{ stats.total }}</div>
      <div class="card-sub">PHP {{ fmt(stats.totalAmount) }}</div>
    </div>
    <div class="card vatable">
      <div class="card-label">VATable</div>
      <div class="card-value">{{ stats.vatable }}</div>
    </div>
    <div class="card exempt">
      <div class="card-label">Exempt</div>
      <div class="card-value">{{ stats.exempt }}</div>
    </div>
    <div class="card zero-rated">
      <div class="card-label">Zero Rated</div>
      <div class="card-value">{{ stats.zeroRated }}</div>
    </div>
  </div>

  <div class="confidence-bar">
    <span class="bar-label">Confidence:</span>
    <div class="bar">
      <div class="seg high" :style="{ width: stats.highPct + '%' }" :title="`High: ${stats.highConf}`"></div>
      <div class="seg med" :style="{ width: stats.medPct + '%' }" :title="`Medium: ${stats.medConf}`"></div>
      <div class="seg low" :style="{ width: stats.lowPct + '%' }" :title="`Low: ${stats.lowConf}`"></div>
    </div>
    <span class="bar-legend">
      <span class="dot high"></span>High {{ stats.highPct }}%
      <span class="dot med"></span>Med {{ stats.medPct }}%
      <span class="dot low"></span>Low {{ stats.lowPct }}%
    </span>
  </div>
</template>

<style scoped>
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.card {
  padding: 16px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}
.card.vatable { border-left: 4px solid #3b82f6; }
.card.exempt { border-left: 4px solid #f59e0b; }
.card.zero-rated { border-left: 4px solid #10b981; }
.card-label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.card-value { font-size: 24px; font-weight: 700; color: #111827; }
.card-sub { font-size: 13px; color: #6b7280; margin-top: 2px; }

.confidence-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 16px;
}
.bar-label { font-size: 13px; color: #6b7280; white-space: nowrap; }
.bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: #e5e7eb;
  display: flex;
  overflow: hidden;
}
.seg { height: 100%; transition: width 0.3s; }
.seg.high { background: #16a34a; }
.seg.med { background: #d97706; }
.seg.low { background: #dc2626; }
.bar-legend { display: flex; gap: 12px; font-size: 12px; color: #6b7280; white-space: nowrap; }
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.dot.high { background: #16a34a; }
.dot.med { background: #d97706; }
.dot.low { background: #dc2626; }
</style>
