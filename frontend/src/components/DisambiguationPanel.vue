<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FieldCandidate } from '../api/data'
import type { TargetField } from '../config/targetFieldsByReportType'

const props = defineProps<{
  targetField: string
  targetLabel: string
  competingColumns: string[]
  sampleRows: Record<string, unknown>[]
  candidates: Record<string, FieldCandidate[]>
  allTargetFields: TargetField[]
}>()

const emit = defineEmits<{
  resolve: [selectedColumn: string]
  close: []
}>()

const selected = ref<string | null>(null)

const displayRows = computed(() => props.sampleRows.slice(0, 3))

function getCandidateForColumn(col: string): FieldCandidate | undefined {
  const colCandidates = props.candidates[col]
  if (!colCandidates) return undefined
  return colCandidates.find(c => c.target_field === props.targetField)
}

function confirm() {
  if (selected.value) {
    emit('resolve', selected.value)
  }
}
</script>

<template>
  <div class="disambiguation-overlay" @click.self="emit('close')">
    <div class="disambiguation-panel">
      <div class="panel-header">
        <h3>Resolve Conflict: {{ targetLabel }}</h3>
        <p class="panel-desc">
          Multiple columns are mapped to <strong>{{ targetLabel }}</strong>.
          Select which column should use this field.
        </p>
        <button class="close-btn" @click="emit('close')">&times;</button>
      </div>

      <div class="comparison-table-wrap">
        <table class="comparison-table">
          <thead>
            <tr>
              <th class="row-label"></th>
              <th
                v-for="col in competingColumns"
                :key="col"
                class="col-header"
                :class="{ 'selected-col': selected === col }"
              >
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Sample data rows -->
            <tr v-for="(row, i) in displayRows" :key="'row-' + i">
              <td class="row-label">Row {{ i + 1 }}</td>
              <td
                v-for="col in competingColumns"
                :key="col"
                :class="{ 'selected-col': selected === col }"
              >
                {{ row[col] ?? '--' }}
              </td>
            </tr>

            <!-- AI suggestion row -->
            <tr class="ai-row">
              <td class="row-label">AI Suggestion</td>
              <td
                v-for="col in competingColumns"
                :key="'ai-' + col"
                :class="{ 'selected-col': selected === col }"
              >
                <template v-if="getCandidateForColumn(col)">
                  <span class="ai-target">{{ targetField }}</span>
                  <span class="ai-conf">
                    {{ Math.round((getCandidateForColumn(col)?.confidence ?? 0) * 100) }}%
                  </span>
                </template>
                <span v-else class="ai-none">No suggestion</span>
              </td>
            </tr>

            <!-- AI reason row -->
            <tr class="reason-row">
              <td class="row-label">Reason</td>
              <td
                v-for="col in competingColumns"
                :key="'reason-' + col"
                :class="{ 'selected-col': selected === col }"
              >
                {{ getCandidateForColumn(col)?.reason ?? '--' }}
              </td>
            </tr>

            <!-- Selection row -->
            <tr class="select-row">
              <td class="row-label">Select</td>
              <td
                v-for="col in competingColumns"
                :key="'select-' + col"
                :class="{ 'selected-col': selected === col }"
              >
                <label class="radio-label">
                  <input
                    type="radio"
                    :value="col"
                    v-model="selected"
                    name="disambiguation-choice"
                  />
                  Use this column
                </label>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel-actions">
        <button class="cancel-btn" @click="emit('close')">Cancel</button>
        <button class="confirm-btn" :disabled="!selected" @click="confirm">
          Apply Selection
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.disambiguation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.disambiguation-panel {
  background: #fff;
  border-radius: 12px;
  max-width: 800px;
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.panel-header {
  padding: 20px 24px 12px;
  position: relative;
}
.panel-header h3 {
  margin: 0 0 8px;
  font-size: 18px;
}
.panel-desc {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}
.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #9ca3af;
  line-height: 1;
}
.close-btn:hover {
  color: #374151;
}

.comparison-table-wrap {
  padding: 0 24px;
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.comparison-table th,
.comparison-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  text-align: left;
}
.comparison-table thead th {
  background: #f9fafb;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.row-label {
  font-weight: 500;
  color: #6b7280;
  white-space: nowrap;
  width: 100px;
}

.selected-col {
  background: #eef2ff !important;
}

.col-header {
  min-width: 150px;
}

.ai-row td {
  background: #faf5ff;
}
.ai-target {
  font-weight: 500;
  color: #7c3aed;
}
.ai-conf {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #7c3aed;
  background: #ede9fe;
  padding: 1px 6px;
  border-radius: 4px;
}
.ai-none {
  color: #9ca3af;
  font-style: italic;
}

.reason-row td {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.select-row td {
  padding: 12px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 13px;
}

.panel-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.cancel-btn:hover {
  background: #f9fafb;
}

.confirm-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: #4f46e5;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}
.confirm-btn:hover {
  background: #4338ca;
}
.confirm-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
