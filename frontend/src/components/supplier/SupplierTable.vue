<script setup lang="ts">
import { computed } from 'vue'
import type { Supplier } from '../../types/withholding'

const props = defineProps<{
  suppliers: Supplier[]
  jurisdiction?: string
}>()

const isSG = computed(() => props.jurisdiction === 'SG')
const emit = defineEmits<{
  edit: [supplier: Supplier]
  delete: [id: string]
}>()
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>{{ isSG ? 'UEN' : 'TIN' }}</th>
          <th>Name</th>
          <th>Type</th>
          <th>{{ isSG ? 'WHT Nature' : 'Default ATC' }}</th>
          <th>{{ isSG ? 'WHT Rate' : 'EWT Rate' }}</th>
          <th>{{ isSG ? 'GST Reg.' : 'VAT Reg.' }}</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="suppliers.length === 0">
          <td colspan="7" class="empty">No suppliers yet</td>
        </tr>
        <tr v-for="s in suppliers" :key="s.id">
          <td class="mono">{{ s.tin }}</td>
          <td>{{ s.name }}</td>
          <td>
            <span class="badge" :class="s.supplier_type">{{ s.supplier_type }}</span>
          </td>
          <td>{{ s.default_atc_code || '-' }}</td>
          <td>{{ s.default_ewt_rate != null ? `${(s.default_ewt_rate * 100).toFixed(1)}%` : '-' }}</td>
          <td>{{ s.is_vat_registered ? 'Yes' : 'No' }}</td>
          <td class="actions">
            <button class="btn-sm" @click="emit('edit', s)">Edit</button>
            <button class="btn-sm danger" @click="emit('delete', s.id)">Delete</button>
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
  font-size: 14px;
}
.mono { font-family: monospace; font-size: 13px; }
.empty { text-align: center; color: #9ca3af; padding: 40px 0; }
.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.badge.corporation { background: #dbeafe; color: #1e40af; }
.badge.individual { background: #fef3c7; color: #92400e; }
.actions { display: flex; gap: 6px; }
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}
.btn-sm:hover { background: #f3f4f6; }
.btn-sm.danger { color: #ef4444; border-color: #fca5a5; }
.btn-sm.danger:hover { background: #fef2f2; }
</style>
