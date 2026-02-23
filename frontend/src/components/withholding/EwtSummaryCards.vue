<script setup lang="ts">
import type { EwtSummary } from '../../types/withholding'

defineProps<{
  summary: EwtSummary
}>()

function fmt(n: number): string {
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="ewt-cards">
    <div class="card">
      <div class="card-label">Period</div>
      <div class="card-value">{{ summary.period }}</div>
    </div>
    <div class="card">
      <div class="card-label">Total Certificates</div>
      <div class="card-value">{{ summary.total_certificates }}</div>
    </div>
    <div class="card">
      <div class="card-label">Total Income Subject to EWT</div>
      <div class="card-value">PHP {{ fmt(summary.total_income) }}</div>
    </div>
    <div class="card accent">
      <div class="card-label">Total Tax Withheld</div>
      <div class="card-value">PHP {{ fmt(summary.total_tax_withheld) }}</div>
    </div>
  </div>
</template>

<style scoped>
.ewt-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}
.card.accent {
  background: #f0f4ff;
  border-color: #2563eb;
}
.card-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.card-value {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
}
.card.accent .card-value { color: #2563eb; }
</style>
