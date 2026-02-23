<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: Record<string, string> | null
  reportType: string
}>()

interface LineItem {
  key: string
  lineNo: string
  label: string
  value: string
  section: string
}

const sections = computed(() => {
  if (!props.data) return []

  const sectionDefs = [
    { prefix: 'line_1_', section: 'Sales / Receipts', through: 'line_5_' },
    { prefix: 'line_6', section: 'Output Tax', through: 'line_6b_' },
    { prefix: 'line_7_', section: 'Allowable Input Tax', through: 'line_11_' },
    { prefix: 'line_12_', section: 'Tax Due', through: 'line_16_' },
  ]

  const items: LineItem[] = []
  for (const [key, value] of Object.entries(props.data)) {
    if (!key.startsWith('line_')) continue

    // Parse line number: "line_6a_..." → "6A"
    const parts = key.split('_')
    const lineNo = (parts[1] || '').toUpperCase()
    const label = parts.slice(2).join(' ')

    let section = 'Other'
    for (const sd of sectionDefs) {
      const num = parseInt(parts[1])
      const sdStart = parseInt(sd.prefix.split('_')[1])
      const sdEnd = parseInt(sd.through.split('_')[1])
      if (num >= sdStart && num <= sdEnd) {
        section = sd.section
        break
      }
    }

    items.push({ key, lineNo, label, value, section })
  }

  // Group by section
  const grouped: { name: string; items: LineItem[] }[] = []
  let currentSection = ''
  for (const item of items) {
    if (item.section !== currentSection) {
      currentSection = item.section
      grouped.push({ name: currentSection, items: [] })
    }
    grouped[grouped.length - 1].items.push(item)
  }

  return grouped
})

const taxCredit = computed(() => props.data?.tax_credit_carried_forward || '0')

function formatAmount(val: string): string {
  try {
    const num = parseFloat(val)
    return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  } catch {
    return val
  }
}

function isTotal(key: string): boolean {
  return key.includes('total') || key.includes('line_16') || key.includes('line_5_') || key.includes('line_6b_') || key.includes('line_11_')
}
</script>

<template>
  <div class="preview" v-if="data">
    <h3>{{ reportType }} Preview</h3>

    <div v-for="section in sections" :key="section.name" class="section">
      <div class="section-header">{{ section.name }}</div>
      <table>
        <tbody>
          <tr v-for="item in section.items" :key="item.key" :class="{ total: isTotal(item.key) }">
            <td class="line-no">{{ item.lineNo }}</td>
            <td class="label">{{ item.label }}</td>
            <td class="value">PHP {{ formatAmount(item.value) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="parseFloat(taxCredit) > 0" class="credit-note">
      Excess Input VAT / Tax Credit Carried Forward: PHP {{ formatAmount(taxCredit) }}
    </div>
  </div>
</template>

<style scoped>
.preview {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}
h3 { margin-bottom: 16px; }
.section { margin-bottom: 16px; }
.section-header {
  background: #f1f5f9;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #475569;
  border-radius: 6px;
  margin-bottom: 4px;
}
table { width: 100%; }
td { padding: 6px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.line-no { width: 40px; color: #94a3b8; font-weight: 500; }
.label { text-transform: capitalize; color: #555; }
.value { text-align: right; font-family: monospace; white-space: nowrap; }
tr.total { background: #f8fafc; }
tr.total .label, tr.total .value { font-weight: 700; }
.credit-note {
  margin-top: 12px;
  padding: 8px 12px;
  background: #fef3c7;
  border-radius: 6px;
  font-size: 13px;
  color: #92400e;
}
</style>
