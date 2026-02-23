<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { reportsApi } from '../api/reports'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

interface ReportSummary {
  id: string
  report_type: string
  period: string
  status: string
  created_at: string
}

const recentReports = ref<ReportSummary[]>([])

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  try {
    const res = await reportsApi.list(1, 5)
    recentReports.value = res.data.data || []
  } catch {
    // First time user, no reports yet
  }
})
</script>

<template>
  <div class="dashboard">
    <h2>Welcome, {{ auth.user?.full_name || 'User' }}</h2>
    <p class="company">{{ auth.user?.company_name }}</p>

    <div class="cards">
      <router-link to="/upload" class="card">
        <span class="card-icon">📤</span>
        <h3>Upload Data</h3>
        <p>Upload sales & purchase records</p>
      </router-link>
      <router-link to="/reports" class="card">
        <span class="card-icon">📋</span>
        <h3>Generate Report</h3>
        <p>Create BIR 2550M and more</p>
      </router-link>
      <router-link to="/chat" class="card">
        <span class="card-icon">💬</span>
        <h3>AI Assistant</h3>
        <p>Ask tax questions</p>
      </router-link>
      <router-link to="/knowledge" class="card">
        <span class="card-icon">📚</span>
        <h3>Knowledge Base</h3>
        <p>Tax rules & regulations</p>
      </router-link>
      <router-link to="/memory" class="card">
        <span class="card-icon">🧠</span>
        <h3>AI Memory</h3>
        <p>Preferences & corrections</p>
      </router-link>
      <router-link to="/settings" class="card">
        <span class="card-icon">⚙️</span>
        <h3>Settings</h3>
        <p>TIN, RDO, company info</p>
      </router-link>
    </div>

    <div class="recent" v-if="recentReports.length">
      <h3>Recent Reports</h3>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Period</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in recentReports" :key="r.id">
            <td>{{ r.report_type }}</td>
            <td>{{ r.period }}</td>
            <td><span class="badge" :class="r.status">{{ r.status }}</span></td>
            <td>{{ new Date(r.created_at).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dashboard h2 { margin-bottom: 4px; }
.company { color: #888; margin-bottom: 24px; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}
.card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.card-icon { font-size: 32px; }
.card h3 { margin: 8px 0 4px; }
.card p { color: #888; font-size: 13px; }
.recent { background: #fff; padding: 24px; border-radius: 12px; border: 1px solid #e5e7eb; }
.recent h3 { margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px; color: #888; font-size: 13px; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px; border-bottom: 1px solid #f3f4f6; }
.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.badge.draft { background: #fef3c7; color: #92400e; }
.badge.confirmed { background: #d1fae5; color: #065f46; }
</style>
