<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number | null
}>()

const scoreClass = computed(() => {
  if (props.score === null) return 'no-score'
  if (props.score >= 80) return 'score-good'
  if (props.score >= 60) return 'score-warning'
  return 'score-danger'
})

const scoreLabel = computed(() => {
  if (props.score === null) return 'Not Validated'
  if (props.score >= 80) return 'Compliant'
  if (props.score >= 60) return 'Needs Review'
  return 'Non-Compliant'
})
</script>

<template>
  <span class="compliance-badge" :class="scoreClass">
    <span v-if="score !== null" class="score-number">{{ score }}</span>
    <span class="score-label">{{ scoreLabel }}</span>
  </span>
</template>

<style scoped>
.compliance-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.score-number {
  font-size: 14px;
  font-weight: 700;
}
.score-good {
  background: #d1fae5;
  color: #065f46;
}
.score-warning {
  background: #fef3c7;
  color: #92400e;
}
.score-danger {
  background: #fee2e2;
  color: #991b1b;
}
.no-score {
  background: #f3f4f6;
  color: #6b7280;
}
</style>
