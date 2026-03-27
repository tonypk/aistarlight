<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'

const props = defineProps<{
  score: number | null | undefined
}>()

const tagType = computed<'default' | 'success' | 'warning' | 'error'>(() => {
  if (props.score == null) return 'default'
  if (props.score < 30) return 'success'
  if (props.score <= 70) return 'warning'
  return 'error'
})

const label = computed(() => {
  if (props.score == null) return 'N/A'
  return String(props.score)
})
</script>

<template>
  <NTag :type="tagType" size="small" round>
    {{ label }}
  </NTag>
</template>
