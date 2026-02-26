<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import type { FieldCandidate } from '../api/data'
import type { TargetField } from '../config/targetFieldsByReportType'

interface GroupedFields {
  label: string
  fields: TargetField[]
}

const props = defineProps<{
  modelValue: string
  groups: GroupedFields[]
  usedFields?: Set<string>
  candidates?: FieldCandidate[]
  isConflict?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isOpen = ref(false)
const search = ref('')
const containerRef = ref<HTMLDivElement>()

const selectedLabel = computed(() => {
  if (!props.modelValue || props.modelValue === '') return '-- Select --'
  if (props.modelValue === '_skip') return '-- Skip --'
  for (const g of props.groups) {
    const f = g.fields.find(f => f.value === props.modelValue)
    if (f) return f.label
  }
  return props.modelValue
})

const filteredGroups = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return props.groups

  return props.groups
    .map(g => ({
      label: g.label,
      fields: g.fields.filter(f =>
        f.label.toLowerCase().includes(q) ||
        f.value.toLowerCase().includes(q)
      ),
    }))
    .filter(g => g.fields.length > 0)
})

function select(value: string) {
  emit('update:modelValue', value)
  isOpen.value = false
  search.value = ''
}

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    search.value = ''
  }
}

function isUsed(fieldValue: string): boolean {
  if (!props.usedFields) return false
  return props.usedFields.has(fieldValue) && fieldValue !== props.modelValue
}

function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false
    search.value = ''
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div ref="containerRef" class="searchable-select" :class="{ conflict: isConflict }">
    <button class="select-trigger" @click="toggle" type="button">
      <span class="trigger-label">{{ selectedLabel }}</span>
      <span class="trigger-arrow">{{ isOpen ? '\u25B2' : '\u25BC' }}</span>
    </button>

    <div v-if="isOpen" class="dropdown">
      <input
        v-model="search"
        class="search-input"
        placeholder="Search fields..."
        @click.stop
        ref="searchInput"
        autofocus
      />

      <div class="options-list">
        <!-- Special options -->
        <div class="option" :class="{ active: modelValue === '' }" @click="select('')">
          -- Select --
        </div>
        <div class="option" :class="{ active: modelValue === '_skip' }" @click="select('_skip')">
          -- Skip --
        </div>

        <!-- AI candidates section -->
        <template v-if="candidates && candidates.length > 0 && !search">
          <div class="group-header ai-header">AI Suggestions</div>
          <div
            v-for="c in candidates"
            :key="'ai-' + c.target_field"
            class="option ai-option"
            :class="{ active: modelValue === c.target_field, used: isUsed(c.target_field) }"
            @click="select(c.target_field)"
          >
            <span class="option-label">{{ c.target_field }}</span>
            <span class="ai-conf">{{ Math.round(c.confidence * 100) }}%</span>
            <span v-if="isUsed(c.target_field)" class="used-tag">used</span>
            <div v-if="c.reason" class="ai-reason">{{ c.reason }}</div>
          </div>
        </template>

        <!-- Grouped fields -->
        <template v-for="group in filteredGroups" :key="group.label">
          <div class="group-header">{{ group.label }}</div>
          <div
            v-for="f in group.fields"
            :key="f.value"
            class="option"
            :class="{ active: modelValue === f.value, used: isUsed(f.value) }"
            @click="select(f.value)"
          >
            <span class="option-label">{{ f.label }}</span>
            <span v-if="isUsed(f.value)" class="used-tag">used</span>
          </div>
        </template>

        <div v-if="filteredGroups.length === 0 && search" class="no-results">
          No fields matching "{{ search }}"
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.searchable-select {
  position: relative;
  min-width: 200px;
}

.select-trigger {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  text-align: left;
}
.select-trigger:hover {
  border-color: #9ca3af;
}
.conflict .select-trigger {
  border-color: #ef4444;
  background: #fef2f2;
}

.trigger-arrow {
  font-size: 10px;
  color: #9ca3af;
  margin-left: 8px;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  margin-top: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 320px;
  display: flex;
  flex-direction: column;
}

.search-input {
  padding: 8px 12px;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  outline: none;
  font-size: 14px;
  border-radius: 8px 8px 0 0;
}
.search-input::placeholder {
  color: #9ca3af;
}

.options-list {
  overflow-y: auto;
  max-height: 260px;
}

.group-header {
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  position: sticky;
  top: 0;
}
.ai-header {
  background: #f5f3ff;
  color: #7c3aed;
}

.option {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.option:hover {
  background: #f3f4f6;
}
.option.active {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 500;
}
.option.used {
  opacity: 0.5;
}

.ai-option {
  background: #faf5ff;
}
.ai-conf {
  font-size: 11px;
  color: #7c3aed;
  font-weight: 600;
}
.ai-reason {
  width: 100%;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.used-tag {
  font-size: 10px;
  background: #fef3c7;
  color: #92400e;
  padding: 1px 6px;
  border-radius: 4px;
}

.no-results {
  padding: 16px 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
</style>
