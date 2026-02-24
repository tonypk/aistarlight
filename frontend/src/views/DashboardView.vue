<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { client } from '../api/client'
import { reportsApi } from '../api/reports'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

interface ReportSummary {
  id: string
  report_type: string
  period: string
  status: string
  created_at: string
  compliance_score?: number | null
}

interface DashboardStats {
  total_reports: number
  reports_by_status: Record<string, number>
  compliance_score: number | null
  session_count: number
  bank_recon_count: number
  receipt_count: number
  knowledge_count: number
}

const stats = ref<DashboardStats | null>(null)
const recentReports = ref<ReportSummary[]>([])
const loading = ref(true)

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  try {
    const [statsRes, reportsRes] = await Promise.all([
      client.get('/dashboard/stats'),
      reportsApi.list(1, 5),
    ])
    stats.value = statsRes.data.data
    recentReports.value = reportsRes.data.data || []
  } catch {
    // First time user or API error
  } finally {
    loading.value = false
  }
})

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'Draft',
    review: 'In Review',
    approved: 'Approved',
    filed: 'Filed',
    archived: 'Archived',
    confirmed: 'Confirmed',
  }
  return labels[status] || status
}
</script>

<template>
  <div class="dashboard">
    <div class="welcome-section">
      <div>
        <h2>Welcome, {{ auth.user?.full_name || 'User' }}</h2>
        <p class="company">{{ auth.user?.company_name }}</p>
      </div>
    </div>

    <!-- Stats cards -->
    <div v-if="stats" class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_reports }}</div>
          <div class="stat-label">Total Reports</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ (stats.reports_by_status['filed'] || 0) + (stats.reports_by_status['approved'] || 0) }}</div>
          <div class="stat-label">Filed / Approved</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-value">{{ (stats.reports_by_status['draft'] || 0) + (stats.reports_by_status['review'] || 0) }}</div>
          <div class="stat-label">Pending Review</div>
        </div>
      </div>
      <div class="stat-card" :class="{ highlight: stats.compliance_score && stats.compliance_score >= 80 }">
        <div class="stat-icon">🛡️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.compliance_score != null ? stats.compliance_score.toFixed(0) + '%' : '—' }}</div>
          <div class="stat-label">Compliance Score</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔍</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.session_count }}</div>
          <div class="stat-label">Recon Sessions</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏦</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.bank_recon_count }}</div>
          <div class="stat-label">Bank Recon</div>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <h3 class="section-title">Quick Actions</h3>
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
      <router-link to="/bank-reconciliation" class="card">
        <span class="card-icon">🏦</span>
        <h3>Bank Recon</h3>
        <p>Auto-reconcile bank & billing</p>
      </router-link>
      <router-link to="/receipts" class="card">
        <span class="card-icon">🧾</span>
        <h3>Receipt Scanner</h3>
        <p>OCR receipt processing</p>
      </router-link>
      <router-link to="/chat" class="card">
        <span class="card-icon">💬</span>
        <h3>AI Assistant</h3>
        <p>Ask tax questions</p>
      </router-link>
      <router-link to="/withholding" class="card">
        <span class="card-icon">📑</span>
        <h3>Withholding Tax</h3>
        <p>EWT, BIR 2307 & SAWT</p>
      </router-link>
    </div>

    <!-- Recent reports -->
    <div class="recent" v-if="recentReports.length">
      <h3 class="section-title">Recent Reports</h3>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Period</th>
            <th>Status</th>
            <th>Compliance</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in recentReports" :key="r.id">
            <td>{{ r.report_type }}</td>
            <td>{{ r.period }}</td>
            <td><span class="badge" :class="r.status">{{ statusLabel(r.status) }}</span></td>
            <td>
              <span v-if="r.compliance_score != null" class="compliance-pill"
                :class="{ good: r.compliance_score >= 80, warn: r.compliance_score >= 50 && r.compliance_score < 80, bad: r.compliance_score < 50 }">
                {{ r.compliance_score.toFixed(0) }}%
              </span>
              <span v-else class="muted">—</span>
            </td>
            <td>{{ new Date(r.created_at).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="loading" class="loading-state">Loading dashboard...</div>
  </div>
</template>

<style scoped>
.dashboard h2 { margin-bottom: 4px; }
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.company { color: #888; }

/* Stats row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e5e7eb;
}
.stat-card.highlight { border-color: #22c55e; background: #f0fdf4; }
.stat-icon { font-size: 28px; }
.stat-value { font-size: 22px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; margin-top: 2px; }

.section-title { font-size: 16px; margin-bottom: 12px; color: #374151; }

/* Quick actions cards */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.card {
  background: #fff;
  padding: 20px;
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.card-icon { font-size: 28px; }
.card h3 { margin: 6px 0 4px; font-size: 15px; }
.card p { color: #888; font-size: 13px; margin: 0; }

/* Recent reports */
.recent {
  background: #fff;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px; color: #888; font-size: 13px; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px; border-bottom: 1px solid #f3f4f6; font-size: 14px; }
.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.badge.draft { background: #fef3c7; color: #92400e; }
.badge.review { background: #dbeafe; color: #2563eb; }
.badge.approved { background: #d1fae5; color: #065f46; }
.badge.filed { background: #d1fae5; color: #065f46; }
.badge.confirmed { background: #d1fae5; color: #065f46; }
.badge.archived { background: #f3f4f6; color: #6b7280; }

.compliance-pill {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.compliance-pill.good { background: #dcfce7; color: #16a34a; }
.compliance-pill.warn { background: #fef9c3; color: #ca8a04; }
.compliance-pill.bad { background: #fef2f2; color: #dc2626; }

.muted { color: #94a3b8; }
.loading-state { text-align: center; padding: 40px; color: #64748b; }
</style>
