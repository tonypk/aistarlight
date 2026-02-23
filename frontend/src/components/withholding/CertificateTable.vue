<script setup lang="ts">
import type { WithholdingCertificate } from '../../types/withholding'

defineProps<{
  certificates: WithholdingCertificate[]
}>()
const emit = defineEmits<{
  download: [certId: string]
}>()

function fmt(n: number): string {
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const statusColors: Record<string, string> = {
  draft: '#fef3c7',
  generated: '#d1fae5',
  sent: '#dbeafe',
}
const statusTextColors: Record<string, string> = {
  draft: '#92400e',
  generated: '#065f46',
  sent: '#1e40af',
}
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Supplier</th>
          <th>Quarter</th>
          <th>ATC Code</th>
          <th>Income Type</th>
          <th>Income Amount</th>
          <th>Rate</th>
          <th>Tax Withheld</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="certificates.length === 0">
          <td colspan="9" class="empty">No certificates yet</td>
        </tr>
        <tr v-for="c in certificates" :key="c.id">
          <td>{{ c.supplier_name || c.supplier_id.slice(0, 8) }}</td>
          <td>{{ c.quarter }}</td>
          <td class="mono">{{ c.atc_code }}</td>
          <td>{{ c.income_type }}</td>
          <td class="num">PHP {{ fmt(c.income_amount) }}</td>
          <td class="num">{{ (c.ewt_rate * 100).toFixed(1) }}%</td>
          <td class="num bold">PHP {{ fmt(c.tax_withheld) }}</td>
          <td>
            <span
              class="status-badge"
              :style="{
                background: statusColors[c.status] ?? '#f3f4f6',
                color: statusTextColors[c.status] ?? '#374151',
              }"
            >
              {{ c.status }}
            </span>
          </td>
          <td>
            <button
              v-if="c.file_path"
              class="btn-sm"
              @click="emit('download', c.id)"
            >
              Download PDF
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th {
  text-align: left;
  padding: 10px 12px;
  font-size: 12px;
  color: #6b7280;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}
.mono { font-family: monospace; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.bold { font-weight: 600; }
.empty { text-align: center; color: #9ca3af; padding: 40px 0; }
.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}
.btn-sm:hover { background: #f3f4f6; }
</style>
