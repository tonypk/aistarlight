<script setup lang="ts">
import { ref, watch } from 'vue'
const emit = defineEmits<{
  (e: 'update', filters: Record<string, string | number | null>): void
}>()

const vatType = ref<string>('')
const category = ref<string>('')
const minConfidence = ref<string>('')
const search = ref<string>('')

let debounceTimer: ReturnType<typeof setTimeout>

function emitFilters() {
  emit('update', {
    vat_type: vatType.value || null,
    category: category.value || null,
    min_confidence: minConfidence.value ? parseFloat(minConfidence.value) : null,
    search: search.value || null,
  })
}

watch([vatType, category, minConfidence], emitFilters)

watch(search, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(emitFilters, 300)
})

function reset() {
  vatType.value = ''
  category.value = ''
  minConfidence.value = ''
  search.value = ''
  emitFilters()
}
</script>

<template>
  <div class="filters-bar">
    <select v-model="vatType">
      <option value="">All VAT Types</option>
      <option value="vatable">VATable</option>
      <option value="exempt">Exempt</option>
      <option value="zero_rated">Zero Rated</option>
      <option value="government">Government</option>
    </select>

    <select v-model="category">
      <option value="">All Categories</option>
      <option value="goods">Goods</option>
      <option value="services">Services</option>
      <option value="capital">Capital</option>
      <option value="imports">Imports</option>
      <option value="sale">Sale</option>
    </select>

    <select v-model="minConfidence">
      <option value="">All Confidence</option>
      <option value="0.8">High (80%+)</option>
      <option value="0.5">Medium (50%+)</option>
      <option value="0">Low (All)</option>
    </select>

    <input
      v-model="search"
      type="text"
      placeholder="Search description..."
      class="search-input"
    />

    <button class="reset-btn" @click="reset">Clear</button>
  </div>
</template>

<style scoped>
.filters-bar {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  align-items: center;
  flex-wrap: wrap;
}
select, .search-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}
.search-input { flex: 1; min-width: 180px; }
.reset-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
}
.reset-btn:hover { background: #f3f4f6; }
</style>
