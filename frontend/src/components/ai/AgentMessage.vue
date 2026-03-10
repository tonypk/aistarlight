<script setup lang="ts">
import type { AgentMessage } from '../../stores/agent'

defineProps<{ message: AgentMessage }>()
</script>

<template>
  <div class="agent-msg" :class="message.role">
    <div class="msg-bubble">
      <div class="msg-content" v-html="message.content"></div>
      <div v-if="message.streaming" class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
      <div v-if="message.sources?.length" class="msg-sources">
        <span v-for="(src, i) in message.sources" :key="i" class="source-badge" :title="src.text">
          {{ src.section || src.law || src.category || 'Source' }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-msg {
  display: flex;
  margin-bottom: 12px;
}
.agent-msg.user {
  justify-content: flex-end;
}
.agent-msg.assistant {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}
.user .msg-bubble {
  background: #4f46e5;
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .msg-bubble {
  background: #f3f4f6;
  color: #1f2937;
  border-bottom-left-radius: 4px;
}
.msg-content { white-space: pre-wrap; }
.msg-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.source-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(79, 70, 229, 0.1);
  color: #4f46e5;
  cursor: help;
}
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typing 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}
</style>
