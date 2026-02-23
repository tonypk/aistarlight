<script setup lang="ts">
import { onMounted } from 'vue'
import { useReportStore } from '../../stores/report'

const props = defineProps<{
  reportId: string
}>()

const reportStore = useReportStore()

onMounted(() => {
  reportStore.fetchAuditLogs(props.reportId)
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

function actionLabel(action: string): string {
  const labels: Record<string, string> = {
    create: 'Created',
    edit: 'Edited',
    transition: 'Status Changed',
    download: 'Downloaded',
  }
  return labels[action] || action
}

function actionColor(action: string): string {
  const colors: Record<string, string> = {
    create: '#22c55e',
    edit: '#3b82f6',
    transition: '#f59e0b',
    download: '#94a3b8',
  }
  return colors[action] || '#6b7280'
}
</script>

<template>
  <div class="audit-trail" v-if="reportStore.auditLogs.length">
    <h4>Audit Trail</h4>
    <div class="timeline">
      <div
        v-for="log in reportStore.auditLogs"
        :key="log.id"
        class="timeline-item"
      >
        <div class="dot" :style="{ background: actionColor(log.action) }"></div>
        <div class="content">
          <div class="header">
            <span class="action-badge" :style="{ background: actionColor(log.action) + '20', color: actionColor(log.action) }">
              {{ actionLabel(log.action) }}
            </span>
            <span class="time">{{ formatDate(log.created_at) }}</span>
          </div>
          <div v-if="log.comment" class="comment">{{ log.comment }}</div>
          <div v-if="log.changes" class="changes">
            <div v-for="(change, field) in log.changes" :key="field" class="change-item">
              <span class="field-name">{{ field }}:</span>
              <span v-if="(change as any).old" class="old-val">{{ (change as any).old }}</span>
              <span class="arrow">&rarr;</span>
              <span class="new-val">{{ (change as any).new }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audit-trail {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  margin-top: 16px;
}
h4 { margin-bottom: 16px; font-size: 15px; }
.timeline { position: relative; padding-left: 24px; }
.timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: #e5e7eb;
}
.timeline-item {
  position: relative;
  padding-bottom: 16px;
}
.timeline-item:last-child { padding-bottom: 0; }
.dot {
  position: absolute;
  left: -20px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #e5e7eb;
}
.content { padding-left: 4px; }
.header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.action-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}
.time { font-size: 12px; color: #94a3b8; }
.comment { font-size: 13px; color: #555; margin-bottom: 4px; font-style: italic; }
.changes { font-size: 12px; }
.change-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}
.field-name { color: #6b7280; font-weight: 500; }
.old-val { color: #ef4444; text-decoration: line-through; }
.arrow { color: #94a3b8; }
.new-val { color: #22c55e; font-weight: 500; }
</style>
