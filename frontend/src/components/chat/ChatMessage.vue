<script setup lang="ts">
export interface ChatSource {
  text: string
  section?: string
  law?: string
  category?: string
}

defineProps<{
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
}>()
</script>

<template>
  <div class="message" :class="role">
    <div class="avatar">{{ role === 'user' ? '👤' : '🤖' }}</div>
    <div class="content-wrapper">
      <div class="bubble">{{ content }}</div>
      <div v-if="sources && sources.length > 0" class="citations">
        <span class="citations-label">Sources:</span>
        <span
          v-for="(src, i) in sources"
          :key="i"
          class="citation-tag"
          :title="src.text"
        >
          <span v-if="src.law" class="tag-law">{{ src.law }}</span>
          <span v-if="src.section" class="tag-section">§{{ src.section }}</span>
          <span v-if="!src.law && !src.section">{{ src.text }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.message.user { flex-direction: row-reverse; }
.avatar { font-size: 24px; flex-shrink: 0; }
.content-wrapper { max-width: 70%; }
.bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.user .bubble {
  background: #4f46e5;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.assistant .bubble {
  background: #f3f4f6;
  color: #333;
  border-bottom-left-radius: 4px;
}
.citations {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-top: 8px;
  padding: 0 4px;
}
.citations-label {
  font-size: 11px;
  color: #6b7280;
  margin-right: 2px;
}
.citation-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 11px;
  border-radius: 12px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  color: #4338ca;
  cursor: default;
}
.tag-law {
  font-weight: 600;
}
.tag-section {
  color: #6366f1;
}
</style>
