<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { client } from '../api/client'

interface FilingEvent {
  form: string
  name: string
  period: string
  deadline: string
  days_remaining: number
  status: 'overdue' | 'upcoming' | 'scheduled'
}

const events = ref<FilingEvent[]>([])
const loading = ref(true)
const monthsAhead = ref(3)

onMounted(() => loadCalendar())

async function loadCalendar() {
  loading.value = true
  try {
    const res = await client.get('/dashboard/calendar', {
      params: { months_ahead: monthsAhead.value },
    })
    events.value = res.data.data || []
  } catch { /* handled by toast */ } finally {
    loading.value = false
  }
}

const overdueEvents = computed(() => events.value.filter(e => e.status === 'overdue'))
const upcomingEvents = computed(() => events.value.filter(e => e.status === 'upcoming'))
const scheduledEvents = computed(() => events.value.filter(e => e.status === 'scheduled'))

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function daysLabel(days: number): string {
  if (days < 0) return `${Math.abs(days)}d overdue`
  if (days === 0) return 'Due today'
  if (days === 1) return 'Tomorrow'
  return `${days} days`
}
</script>

<template>
  <div class="calendar-view">
    <div class="header">
      <h2>Filing Calendar</h2>
      <div class="controls">
        <select v-model="monthsAhead" @change="loadCalendar()">
          <option :value="1">1 month</option>
          <option :value="3">3 months</option>
          <option :value="6">6 months</option>
          <option :value="12">12 months</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading calendar...</div>

    <template v-else>
      <!-- Overdue -->
      <div v-if="overdueEvents.length" class="section">
        <h3 class="section-title overdue-title">Overdue ({{ overdueEvents.length }})</h3>
        <div class="event-list">
          <div v-for="e in overdueEvents" :key="e.form + e.deadline" class="event-card overdue">
            <div class="event-left">
              <span class="event-form">{{ e.form }}</span>
              <span class="event-name">{{ e.name }}</span>
            </div>
            <div class="event-right">
              <span class="event-period">{{ e.period }}</span>
              <span class="event-deadline">{{ formatDate(e.deadline) }}</span>
              <span class="event-days overdue">{{ daysLabel(e.days_remaining) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Upcoming (within 7 days) -->
      <div v-if="upcomingEvents.length" class="section">
        <h3 class="section-title upcoming-title">Due This Week ({{ upcomingEvents.length }})</h3>
        <div class="event-list">
          <div v-for="e in upcomingEvents" :key="e.form + e.deadline" class="event-card upcoming">
            <div class="event-left">
              <span class="event-form">{{ e.form }}</span>
              <span class="event-name">{{ e.name }}</span>
            </div>
            <div class="event-right">
              <span class="event-period">{{ e.period }}</span>
              <span class="event-deadline">{{ formatDate(e.deadline) }}</span>
              <span class="event-days upcoming">{{ daysLabel(e.days_remaining) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Scheduled -->
      <div v-if="scheduledEvents.length" class="section">
        <h3 class="section-title">Upcoming Deadlines ({{ scheduledEvents.length }})</h3>
        <table class="calendar-table">
          <thead>
            <tr>
              <th>Form</th>
              <th>Description</th>
              <th>Period</th>
              <th>Deadline</th>
              <th>Days Left</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in scheduledEvents" :key="e.form + e.deadline">
              <td class="form-cell">{{ e.form }}</td>
              <td>{{ e.name }}</td>
              <td>{{ e.period }}</td>
              <td>{{ formatDate(e.deadline) }}</td>
              <td class="days-cell">{{ daysLabel(e.days_remaining) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!events.length" class="empty">
        No filing deadlines found for the selected period.
      </div>
    </template>
  </div>
</template>

<style scoped>
.calendar-view {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header h2 { margin: 0; }
.controls select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.section { margin-bottom: 24px; }
.section-title {
  font-size: 16px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}
.overdue-title { color: #dc2626; border-color: #dc2626; }
.upcoming-title { color: #d97706; border-color: #d97706; }

/* Event cards (for overdue/upcoming) */
.event-list { display: flex; flex-direction: column; gap: 8px; }
.event-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-radius: 10px;
  border-left: 4px solid;
}
.event-card.overdue {
  background: #fef2f2;
  border-color: #dc2626;
}
.event-card.upcoming {
  background: #fffbeb;
  border-color: #d97706;
}

.event-left { display: flex; flex-direction: column; gap: 2px; }
.event-form { font-weight: 600; font-size: 15px; color: #1e293b; }
.event-name { font-size: 13px; color: #64748b; }

.event-right { display: flex; align-items: center; gap: 16px; text-align: right; }
.event-period { font-size: 13px; color: #64748b; }
.event-deadline { font-size: 14px; color: #374151; }
.event-days {
  font-weight: 600;
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 12px;
}
.event-days.overdue { background: #fecaca; color: #dc2626; }
.event-days.upcoming { background: #fef3c7; color: #92400e; }

/* Table (for scheduled) */
.calendar-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.calendar-table th {
  text-align: left;
  padding: 10px 14px;
  background: #f8fafc;
  font-weight: 500;
  color: #64748b;
  font-size: 13px;
}
.calendar-table td {
  padding: 10px 14px;
  border-top: 1px solid #f1f5f9;
}
.form-cell { font-weight: 600; color: #4f46e5; }
.days-cell { color: #16a34a; font-weight: 500; }

.loading { text-align: center; padding: 48px; color: #64748b; }
.empty { text-align: center; padding: 48px; color: #94a3b8; }
</style>
