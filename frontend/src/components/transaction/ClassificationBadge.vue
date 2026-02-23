<script setup lang="ts">
import type { VatType } from '../../types/transaction'

defineProps<{
  vatType: VatType
  confidence: number
  source?: string
}>()

const vatColors: Record<string, { bg: string; text: string }> = {
  vatable: { bg: '#dbeafe', text: '#1e40af' },
  exempt: { bg: '#fef3c7', text: '#92400e' },
  zero_rated: { bg: '#d1fae5', text: '#065f46' },
  government: { bg: '#ede9fe', text: '#5b21b6' },
}

const vatLabels: Record<string, string> = {
  vatable: 'VATable',
  exempt: 'Exempt',
  zero_rated: 'Zero Rated',
  government: 'Government',
}

function confidenceColor(c: number): string {
  if (c >= 0.8) return '#16a34a'
  if (c >= 0.5) return '#d97706'
  return '#dc2626'
}

function confidenceLabel(c: number): string {
  if (c >= 0.8) return 'High'
  if (c >= 0.5) return 'Medium'
  return 'Low'
}
</script>

<template>
  <span class="badge-group">
    <span
      class="vat-badge"
      :style="{
        background: vatColors[vatType]?.bg ?? '#f3f4f6',
        color: vatColors[vatType]?.text ?? '#374151',
      }"
    >
      {{ vatLabels[vatType] ?? vatType }}
    </span>
    <span
      class="confidence-badge"
      :style="{ color: confidenceColor(confidence) }"
      :title="`Confidence: ${(confidence * 100).toFixed(0)}% (${source ?? 'ai'})`"
    >
      {{ confidenceLabel(confidence) }} {{ (confidence * 100).toFixed(0) }}%
    </span>
  </span>
</template>

<style scoped>
.badge-group { display: inline-flex; gap: 6px; align-items: center; }
.vat-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.confidence-badge {
  font-size: 11px;
  font-weight: 500;
}
</style>
