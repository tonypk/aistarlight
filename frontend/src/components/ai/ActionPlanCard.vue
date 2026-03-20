<script setup lang="ts">
import { ref } from 'vue'
import { useAgentStore } from '../../stores/agent'

interface ActionPlanProps {
  planId: string
  toolName: string
  summary: string
  impact: { affected_count: number; details: string[] }
  status: 'pending' | 'confirming' | 'executed' | 'failed' | 'cancelled' | 'timeout'
  result?: Record<string, unknown>
  error?: string
}

const props = defineProps<ActionPlanProps>()
const agent = useAgentStore()
const confirming = ref(false)

async function confirm() {
  confirming.value = true
  await agent.confirmAction(props.planId)
  confirming.value = false
}

async function cancel() {
  await agent.cancelAction(props.planId)
}
</script>

<template>
  <div class="action-plan-card" :class="status">
    <div class="plan-header">
      <span class="plan-icon">{{ status === 'executed' ? '\u2705' : status === 'failed' ? '\u274C' : status === 'cancelled' ? '\uD83D\uDEAB' : '\u26A1' }}</span>
      <span class="plan-summary">{{ summary }}</span>
    </div>
    <div v-if="impact?.details?.length" class="plan-impact">
      <div v-for="(detail, i) in impact.details" :key="i" class="impact-item">{{ detail }}</div>
    </div>
    <div v-if="status === 'pending'" class="plan-actions">
      <button class="btn-confirm" :disabled="confirming" @click="confirm">
        {{ confirming ? 'Executing...' : 'Confirm' }}
      </button>
      <button class="btn-cancel" :disabled="confirming" @click="cancel">Cancel</button>
    </div>
    <div v-else-if="status === 'executed'" class="plan-result success">Action completed successfully</div>
    <div v-else-if="status === 'failed'" class="plan-result error">Failed: {{ error }}</div>
    <div v-else-if="status === 'cancelled'" class="plan-result cancelled">Action cancelled</div>
  </div>
</template>

<style scoped>
.action-plan-card {
  background: var(--bg-surface-alt, #f8fafc);
  border: 1px solid var(--border-default, #e2e8f0);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 8px 0;
}
.action-plan-card.pending {
  border-color: #f59e0b;
  background: #fffbeb;
}
.action-plan-card.executed {
  border-color: #059669;
  background: #ecfdf5;
}
.action-plan-card.failed {
  border-color: #dc2626;
  background: #fef2f2;
}
.action-plan-card.cancelled {
  border-color: #9ca3af;
  background: #f9fafb;
}
.plan-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.plan-icon {
  font-size: 16px;
}
.plan-impact {
  margin-top: 6px;
  padding-left: 26px;
}
.impact-item {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.plan-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-left: 26px;
}
.btn-confirm {
  padding: 6px 16px;
  background: var(--brand-primary, #4f46e5);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
}
.btn-confirm:hover:not(:disabled) {
  background: var(--brand-primary-hover, #4338ca);
}
.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-cancel {
  padding: 6px 16px;
  background: none;
  border: 1px solid var(--border-default, #e2e8f0);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: inherit;
}
.btn-cancel:hover:not(:disabled) {
  background: var(--bg-surface-hover, #f1f5f9);
}
.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.plan-result {
  margin-top: 8px;
  padding-left: 26px;
  font-size: 12px;
}
.plan-result.success { color: #059669; }
.plan-result.error { color: #dc2626; }
.plan-result.cancelled { color: #6b7280; }
</style>
