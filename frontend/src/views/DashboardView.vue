<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { client } from '../api/client'
import { reportsApi } from '../api/reports'
import { healthApi, type AIHealthStatus } from '../api/health'
import { dashboardApi, type MonthlyTrend, type ActivityItem, type FinancialSummary } from '../api/dashboard'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
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
  pending_approvals: number
  unmatched_transactions: number
  low_confidence_count: number
  draft_reports: number
}

interface CalendarEvent {
  form: string
  name: string
  period: string
  deadline: string
  days_remaining: number
  status: 'overdue' | 'upcoming' | 'scheduled'
}

const stats = ref<DashboardStats | null>(null)
const financials = ref<FinancialSummary | null>(null)
const recentReports = ref<ReportSummary[]>([])
const deadlines = ref<CalendarEvent[]>([])
const aiHealth = ref<AIHealthStatus | null>(null)
const trends = ref<MonthlyTrend[]>([])
const activities = ref<ActivityItem[]>([])
const loading = ref(true)

const urgentDeadlines = computed(() =>
  deadlines.value.filter(d => d.status === 'overdue' || d.status === 'upcoming').slice(0, 5)
)

const nextDeadlines = computed(() =>
  deadlines.value.filter(d => d.status === 'scheduled').slice(0, 5)
)

// Financial helpers
function fmtCompact(val: string | undefined): string {
  if (!val) return '0'
  const n = parseFloat(val)
  if (isNaN(n)) return '0'
  const abs = Math.abs(n)
  if (abs >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (abs >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toFixed(2)
}

function isPositive(val: string | undefined): boolean {
  return parseFloat(val || '0') > 0
}

function isNegative(val: string | undefined): boolean {
  return parseFloat(val || '0') < 0
}

// P&L trend chart (SVG)
const plMaxValue = computed(() => {
  if (!financials.value?.monthly_pl?.length) return 1
  const vals = financials.value.monthly_pl.flatMap(p => [
    Math.abs(parseFloat(p.revenue || '0')),
    Math.abs(parseFloat(p.expenses || '0')),
    Math.abs(parseFloat(p.net || '0'))
  ])
  return Math.max(...vals, 1)
})

function plPoints(field: 'revenue' | 'expenses' | 'net'): string {
  const pts = financials.value?.monthly_pl
  if (!pts?.length) return ''
  const w = 400, h = 140, pad = 20
  const stepX = pts.length > 1 ? (w - 2 * pad) / (pts.length - 1) : 0
  return pts.map((p, i) => {
    const x = pad + i * stepX
    const v = parseFloat(p[field] || '0')
    const y = h - pad - ((Math.abs(v) / plMaxValue.value) * (h - 2 * pad))
    return `${x},${y}`
  }).join(' ')
}

// Donut chart from reports_by_status
const donutSegments = computed(() => {
  if (!stats.value?.reports_by_status) return []
  const entries = Object.entries(stats.value.reports_by_status)
  const total = entries.reduce((sum, [, v]) => sum + v, 0)
  if (total === 0) return []
  const colors: Record<string, string> = {
    draft: '#f59e0b', review: '#3b82f6', approved: '#10b981',
    filed: '#059669', confirmed: '#059669', archived: '#9ca3af', rejected: '#ef4444',
  }
  let offset = 0
  return entries.map(([status, count]) => {
    const pct = (count / total) * 100
    const seg = { status, count, pct, offset, color: colors[status] || '#6b7280' }
    offset += pct
    return seg
  })
})

const donutGradient = computed(() => {
  const segs = donutSegments.value
  if (!segs.length) return 'conic-gradient(var(--border-default) 0% 100%)'
  const stops = segs.map(s => `${s.color} ${s.offset}% ${s.offset + s.pct}%`)
  return `conic-gradient(${stops.join(', ')})`
})

// Monthly reports trend chart (legacy)
const trendMaxValue = computed(() => {
  if (!trends.value.length) return 1
  return Math.max(...trends.value.map(t => t.total_reports), 1)
})

const trendPoints = computed(() => {
  const pts = trends.value
  if (!pts.length) return ''
  const w = 400, h = 120, pad = 10
  const stepX = pts.length > 1 ? (w - 2 * pad) / (pts.length - 1) : 0
  return pts.map((t, i) => {
    const x = pad + i * stepX
    const y = h - pad - ((t.total_reports / trendMaxValue.value) * (h - 2 * pad))
    return `${x},${y}`
  }).join(' ')
})

const trendFillPath = computed(() => {
  const pts = trends.value
  if (!pts.length) return ''
  const w = 400, h = 120, pad = 10
  const stepX = pts.length > 1 ? (w - 2 * pad) / (pts.length - 1) : 0
  const coords = pts.map((t, i) => {
    const x = pad + i * stepX
    const y = h - pad - ((t.total_reports / trendMaxValue.value) * (h - 2 * pad))
    return `${x},${y}`
  })
  return `M${pad},${h - pad} L${coords.join(' L')} L${pad + (pts.length - 1) * stepX},${h - pad} Z`
})

// Smart quick actions — sorted by pending items
const quickActions = computed(() => {
  const s = stats.value
  const actions = [
    {
      to: '/upload', icon: '📤', title: t('dashboard.uploadData'),
      desc: t('dashboard.uploadDataDesc'),
      badge: 0,
    },
    {
      to: '/classification', icon: '🏷️', title: t('dashboard.classifyTransactions'),
      desc: t('dashboard.classifyDesc'),
      badge: s?.low_confidence_count || 0,
    },
    {
      to: '/reports', icon: '📋', title: t('dashboard.generateReport'),
      desc: auth.jurisdiction === 'SG' ? t('dashboard.generateReportDescSG') : auth.jurisdiction === 'LK' ? t('dashboard.generateReportDescLK') : t('dashboard.generateReportDescPH'),
      badge: s?.draft_reports || 0,
    },
    {
      to: '/bank-reconciliation', icon: '🏦', title: t('dashboard.bankReconAction'),
      desc: t('dashboard.bankReconDesc'),
      badge: s?.unmatched_transactions || 0,
    },
    {
      to: '/approvals', icon: '✅', title: t('dashboard.approvals'),
      desc: t('dashboard.approvalsDesc'),
      badge: s?.pending_approvals || 0,
    },
    {
      to: '/chat', icon: '💬', title: t('dashboard.aiAssistant'),
      desc: t('dashboard.aiAssistantDesc'),
      badge: 0,
    },
  ]
  // Sort: items with badges first
  return actions.sort((a, b) => (b.badge > 0 ? 1 : 0) - (a.badge > 0 ? 1 : 0))
})

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  try {
    const [statsRes, finRes, reportsRes, calendarRes, aiRes, trendsRes, activityRes] = await Promise.all([
      client.get('/dashboard/stats'),
      dashboardApi.getFinancialSummary().catch(() => null),
      reportsApi.list(1, 5),
      client.get('/dashboard/calendar', { params: { months_ahead: 3 } }),
      healthApi.getAIHealth().catch(() => null),
      dashboardApi.getTrends(6).catch(() => ({ data: { data: [] } })),
      dashboardApi.getActivity(10).catch(() => ({ data: { data: [] } })),
    ])
    stats.value = statsRes.data.data
    if (finRes) financials.value = finRes.data.data
    recentReports.value = reportsRes.data.data || []
    deadlines.value = calendarRes.data.data || []
    if (aiRes) aiHealth.value = aiRes.data.data
    trends.value = trendsRes.data?.data || []
    activities.value = activityRes.data?.data || []
  } catch {
    // First time user or API error
  } finally {
    loading.value = false
  }
})

function statusLabel(status: string): string {
  const key = `dashboard.status${status.charAt(0).toUpperCase() + status.slice(1)}` as string
  const translated = t(key)
  return translated !== key ? translated : status
}

function formatDeadline(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
</script>

<template>
  <div class="dashboard">
    <div class="welcome-section" data-testid="dashboard-welcome">
      <div>
        <h2>{{ t('dashboard.welcome', { name: auth.user?.full_name || 'User' }) }}</h2>
        <p class="company">{{ auth.user?.company_name }}</p>
      </div>
    </div>

    <!-- Financial Health Overview -->
    <div v-if="financials" class="financial-overview" data-testid="financial-overview">
      <h3 class="section-title">{{ t('dashboard.financialHealth') }}</h3>
      <div class="finance-cards">
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.revenueThisMonth') }}</div>
          <div class="finance-value" :class="{ positive: isPositive(financials.revenue) }">
            &#8369;{{ fmtCompact(financials.revenue) }}
          </div>
        </div>
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.expenses') }}</div>
          <div class="finance-value expense">
            &#8369;{{ fmtCompact(financials.expenses) }}
          </div>
        </div>
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.netIncome') }}</div>
          <div class="finance-value" :class="{ positive: isPositive(financials.net_income), negative: isNegative(financials.net_income) }">
            &#8369;{{ fmtCompact(financials.net_income) }}
          </div>
        </div>
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.cashBalance') }}</div>
          <div class="finance-value">
            &#8369;{{ fmtCompact(financials.cash_balance) }}
          </div>
        </div>
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.receivables') }}</div>
          <div class="finance-value">
            &#8369;{{ fmtCompact(financials.accounts_receivable) }}
          </div>
        </div>
        <div class="finance-card">
          <div class="finance-label">{{ t('dashboard.payables') }}</div>
          <div class="finance-value">
            &#8369;{{ fmtCompact(financials.accounts_payable) }}
          </div>
        </div>
      </div>

      <!-- P&L Trend Chart -->
      <div v-if="financials.monthly_pl?.length" class="pl-chart-card">
        <h4 class="chart-subtitle">{{ t('dashboard.plTrend') }}</h4>
        <div class="pl-chart">
          <svg viewBox="0 0 400 140" class="pl-svg">
            <!-- Revenue line -->
            <polyline :points="plPoints('revenue')" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <!-- Expenses line -->
            <polyline :points="plPoints('expenses')" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 2" />
            <!-- Net Income line -->
            <polyline :points="plPoints('net')" fill="none" stroke="var(--brand-primary)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <div class="pl-labels">
            <span v-for="p in financials.monthly_pl" :key="p.month" class="trend-label">{{ p.month.slice(5) }}</span>
          </div>
          <div class="pl-legend">
            <span class="legend-item"><span class="legend-line revenue"></span> {{ t('dashboard.revenue') }}</span>
            <span class="legend-item"><span class="legend-line expenses"></span> {{ t('dashboard.expensesLegend') }}</span>
            <span class="legend-item"><span class="legend-line net"></span> {{ t('dashboard.netIncomeLegend') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats cards -->
    <div v-if="stats" class="stats-row" data-testid="dashboard-stats">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_reports }}</div>
          <div class="stat-label">{{ t('dashboard.totalReports') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ (stats.reports_by_status['filed'] || 0) + (stats.reports_by_status['approved'] || 0) }}</div>
          <div class="stat-label">{{ t('dashboard.filedApproved') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-value">{{ (stats.reports_by_status['draft'] || 0) + (stats.reports_by_status['review'] || 0) }}</div>
          <div class="stat-label">{{ t('dashboard.pendingReview') }}</div>
        </div>
      </div>
      <div class="stat-card" :class="{ highlight: stats.compliance_score && stats.compliance_score >= 80 }">
        <div class="stat-icon">🛡️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.compliance_score != null ? stats.compliance_score.toFixed(0) + '%' : '—' }}</div>
          <div class="stat-label">{{ t('dashboard.complianceScore') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔍</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.session_count }}</div>
          <div class="stat-label">{{ t('dashboard.reconSessions') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏦</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.bank_recon_count }}</div>
          <div class="stat-label">{{ t('dashboard.bankRecon') }}</div>
        </div>
      </div>
    </div>

    <!-- Charts Row: Donut + Trend -->
    <div v-if="stats" class="charts-row">
      <!-- Filing Status Donut -->
      <div class="chart-card">
        <h3 class="section-title">{{ t('dashboard.filingStatus') }}</h3>
        <div class="donut-container">
          <div class="donut" :style="{ background: donutGradient }">
            <div class="donut-hole">
              <div class="donut-total">{{ stats.total_reports }}</div>
              <div class="donut-total-label">{{ t('dashboard.total') }}</div>
            </div>
          </div>
          <div class="donut-legend">
            <div v-for="seg in donutSegments" :key="seg.status" class="legend-item">
              <span class="legend-dot" :style="{ background: seg.color }"></span>
              <span class="legend-label">{{ statusLabel(seg.status) }}</span>
              <span class="legend-count">{{ seg.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Trend Chart -->
      <div class="chart-card chart-card-wide">
        <h3 class="section-title">{{ t('dashboard.monthlyReports') }}</h3>
        <div v-if="trends.length" class="trend-chart">
          <svg viewBox="0 0 400 120" class="trend-svg">
            <path :d="trendFillPath" fill="var(--brand-primary)" opacity="0.1" />
            <polyline :points="trendPoints" fill="none" stroke="var(--brand-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle
              v-for="(t, i) in trends"
              :key="t.month"
              :cx="10 + (trends.length > 1 ? i * (380 / (trends.length - 1)) : 0)"
              :cy="110 - ((t.total_reports / trendMaxValue) * 100)"
              r="3"
              :fill="'var(--brand-primary)'"
            />
          </svg>
          <div class="trend-labels">
            <span v-for="t in trends" :key="t.month" class="trend-label">{{ t.month.slice(5) }}</span>
          </div>
        </div>
        <div v-else class="chart-empty">{{ t('dashboard.noTrendData') }}</div>
      </div>
    </div>

    <!-- AI Status Card -->
    <div v-if="aiHealth" class="ai-status-card" :class="{ enabled: aiHealth.ai_enabled, disabled: !aiHealth.ai_enabled }">
      <div class="ai-status-indicator" :class="aiHealth.ai_enabled ? 'green' : 'red'"></div>
      <div class="ai-status-info">
        <strong>{{ aiHealth.ai_enabled ? t('dashboard.aiOnline') : t('dashboard.aiOffline') }}</strong>
        <span v-if="aiHealth.ai_enabled" class="ai-provider">{{ aiHealth.provider }} / {{ aiHealth.model }}</span>
        <span v-else class="ai-warning">{{ t('dashboard.aiKeyMissing') }}</span>
      </div>
      <div v-if="aiHealth.ai_enabled" class="ai-features">
        <span v-for="(on, name) in aiHealth.features" :key="name" class="feature-tag" :class="{ on, off: !on }">
          {{ String(name).replace(/_/g, ' ') }}
        </span>
      </div>
    </div>

    <!-- Deadline Alerts -->
    <div v-if="urgentDeadlines.length" class="deadline-alerts">
      <h3 class="section-title">{{ t('dashboard.upcomingDeadlines') }}</h3>
      <div class="deadline-list">
        <div
          v-for="d in urgentDeadlines"
          :key="d.form + d.deadline"
          class="deadline-item"
          :class="d.status"
        >
          <div class="deadline-badge" :class="d.status">
            {{ d.status === 'overdue' ? t('dashboard.overdue') : d.days_remaining + 'd' }}
          </div>
          <div class="deadline-info">
            <strong>{{ d.form }}</strong>
            <span class="deadline-name">{{ d.name }}</span>
          </div>
          <div class="deadline-date">
            {{ formatDeadline(d.deadline) }}
            <span class="deadline-period">{{ d.period }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Two-column layout: Quick Actions + Activity/Deadlines -->
    <div class="two-col">
      <div class="col-main">
        <h3 class="section-title">{{ t('dashboard.quickActions') }}</h3>
        <div class="cards">
          <router-link
            v-for="action in quickActions"
            :key="action.to"
            :to="action.to"
            class="card"
            :data-testid="action.to === '/upload' ? 'dashboard-quick-upload' : undefined"
          >
            <div class="card-header">
              <span class="card-icon">{{ action.icon }}</span>
              <span v-if="action.badge > 0" class="card-badge">{{ action.badge }}</span>
            </div>
            <h3>{{ action.title }}</h3>
            <p>{{ action.desc }}</p>
          </router-link>
        </div>
      </div>

      <!-- Sidebar: scheduled deadlines + activity feed -->
      <div class="col-side">
        <div v-if="nextDeadlines.length" class="sidebar-section">
          <h3 class="section-title">{{ t('dashboard.scheduled') }}</h3>
          <div class="mini-deadlines">
            <div v-for="d in nextDeadlines" :key="d.form + d.deadline" class="mini-deadline">
              <div class="mini-days">{{ d.days_remaining }}d</div>
              <div>
                <div class="mini-form">{{ d.form }}</div>
                <div class="mini-date">{{ formatDeadline(d.deadline) }} &middot; {{ d.period }}</div>
              </div>
            </div>
          </div>
          <router-link to="/calendar" class="view-all">{{ t('dashboard.viewFullCalendar') }} →</router-link>
        </div>

        <!-- Activity Feed -->
        <div v-if="activities.length" class="sidebar-section activity-section">
          <h3 class="section-title">{{ t('dashboard.recentActivity') }}</h3>
          <div class="activity-feed">
            <div v-for="a in activities" :key="a.id" class="activity-item">
              <span class="activity-dot" :class="a.type"></span>
              <div class="activity-content">
                <div class="activity-desc">{{ a.description }}</div>
                <div class="activity-time">{{ timeAgo(a.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent reports -->
    <div class="recent" v-if="recentReports.length">
      <h3 class="section-title">{{ t('dashboard.recentReports') }}</h3>
      <table>
        <thead>
          <tr>
            <th>{{ t('dashboard.thType') }}</th>
            <th>{{ t('dashboard.thPeriod') }}</th>
            <th>{{ t('dashboard.thStatus') }}</th>
            <th>{{ t('dashboard.thCompliance') }}</th>
            <th>{{ t('dashboard.thCreated') }}</th>
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

    <div v-if="loading" class="loading-state">{{ t('dashboard.loadingDashboard') }}</div>
  </div>
</template>

<style scoped>
.dashboard h2 { margin-bottom: 4px; color: var(--text-primary); }
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.company { color: var(--text-muted); }

/* Financial Health Overview */
.financial-overview {
  margin-bottom: 28px;
}
.finance-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.finance-card {
  background: var(--bg-surface);
  border-radius: 10px;
  padding: 16px;
  border: 1px solid var(--border-default);
}
.finance-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.finance-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.finance-value.positive { color: #16a34a; }
.finance-value.negative { color: #dc2626; }
.finance-value.expense { color: #ea580c; }

/* P&L trend chart */
.pl-chart-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 20px;
}
.chart-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.pl-svg { width: 100%; height: auto; }
.pl-labels {
  display: flex;
  justify-content: space-between;
  padding: 4px 20px 0;
}
.pl-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
.pl-legend .legend-item { display: flex; align-items: center; gap: 6px; }
.legend-line {
  display: inline-block;
  width: 20px;
  height: 2px;
}
.legend-line.revenue { background: #10b981; }
.legend-line.expenses { background: #ef4444; border-top: 2px dashed #ef4444; height: 0; }
.legend-line.net { background: var(--brand-primary); height: 3px; }

/* Stats row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.stat-card {
  background: var(--bg-surface);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--border-default);
}
.stat-card.highlight { border-color: #22c55e; background: #f0fdf4; }
html.dark .stat-card.highlight { background: rgba(34,197,94,0.1); }
.stat-icon { font-size: 28px; }
.stat-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.section-title { font-size: 16px; margin-bottom: 12px; color: var(--text-primary); }

/* Charts Row */
.charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.chart-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 20px;
  min-width: 0;
}
.chart-card-wide { flex: 1; }
.chart-empty { color: var(--text-muted); font-size: 14px; text-align: center; padding: 30px 0; }

/* Donut */
.donut-container {
  display: flex;
  align-items: center;
  gap: 20px;
}
.donut {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  position: relative;
  flex-shrink: 0;
}
.donut-hole {
  position: absolute;
  inset: 20px;
  background: var(--bg-surface);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.donut-total { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.donut-total-label { font-size: 11px; color: var(--text-muted); }
.donut-legend { display: flex; flex-direction: column; gap: 6px; }
.donut-legend .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-label { color: var(--text-secondary); min-width: 70px; }
.legend-count { font-weight: 600; color: var(--text-primary); }

/* Trend chart */
.trend-chart { padding-top: 8px; }
.trend-svg { width: 100%; height: auto; }
.trend-labels {
  display: flex;
  justify-content: space-between;
  padding: 4px 10px 0;
}
.trend-label { font-size: 11px; color: var(--text-muted); }

/* Deadline Alerts */
.deadline-alerts {
  margin-bottom: 24px;
}
.deadline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.deadline-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
}
.deadline-item.overdue {
  background: #fef2f2;
  border-color: #fecaca;
}
html.dark .deadline-item.overdue { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); }
.deadline-item.upcoming {
  background: #fffbeb;
  border-color: #fde68a;
}
html.dark .deadline-item.upcoming { background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3); }
.deadline-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  min-width: 60px;
  text-align: center;
}
.deadline-badge.overdue { background: #fee2e2; color: #dc2626; }
.deadline-badge.upcoming { background: #fef3c7; color: #d97706; }
.deadline-info { flex: 1; }
.deadline-info strong { font-size: 14px; margin-right: 8px; color: var(--text-primary); }
.deadline-name { font-size: 13px; color: var(--text-secondary); }
.deadline-date { text-align: right; font-size: 14px; font-weight: 600; color: var(--text-primary); }
.deadline-period { display: block; font-size: 11px; font-weight: 400; color: var(--text-muted); }

/* Two column layout */
.two-col {
  display: flex;
  gap: 24px;
  margin-bottom: 28px;
}
.col-main { flex: 1; }
.col-side {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.sidebar-section {
  background: var(--bg-surface);
  border-radius: 10px;
  border: 1px solid var(--border-default);
  padding: 16px;
}
.sidebar-section .section-title { margin-bottom: 12px; font-size: 14px; }

/* Mini deadlines in sidebar */
.mini-deadlines {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mini-deadline {
  display: flex;
  gap: 10px;
  align-items: center;
}
.mini-days {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef2ff;
  color: var(--brand-primary);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
html.dark .mini-days { background: rgba(99,102,241,0.15); }
.mini-form { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.mini-date { font-size: 11px; color: var(--text-muted); }
.view-all {
  display: block;
  margin-top: 12px;
  font-size: 13px;
  color: var(--brand-primary);
  text-decoration: none;
}
.view-all:hover { text-decoration: underline; }

/* Activity feed */
.activity-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.activity-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
  background: #9ca3af;
}
.activity-dot.report { background: #3b82f6; }
.activity-dot.upload { background: #10b981; }
.activity-dot.recon { background: #f59e0b; }
.activity-dot.receipt { background: #8b5cf6; }
.activity-content { min-width: 0; }
.activity-desc { font-size: 13px; color: var(--text-primary); line-height: 1.3; }
.activity-time { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* Quick actions cards */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.card {
  background: var(--bg-surface);
  padding: 20px;
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--border-default);
  transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.card-icon { font-size: 28px; }
.card-badge {
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
  line-height: 1.4;
}
.card h3 { margin: 6px 0 4px; font-size: 15px; color: var(--text-primary); }
.card p { color: var(--text-muted); font-size: 13px; margin: 0; }

/* Recent reports */
.recent {
  background: var(--bg-surface);
  padding: 20px;
  border-radius: 10px;
  border: 1px solid var(--border-default);
}
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px; color: var(--text-muted); font-size: 13px; border-bottom: 1px solid var(--border-default); }
td { padding: 8px; border-bottom: 1px solid var(--bg-surface-alt); font-size: 14px; color: var(--text-primary); }
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

/* AI Status Card */
.ai-status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 24px;
  border: 1px solid var(--border-default);
  background: var(--bg-surface);
}
.ai-status-card.enabled { border-color: #86efac; background: #f0fdf4; }
html.dark .ai-status-card.enabled { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.3); }
.ai-status-card.disabled { border-color: #fecaca; background: #fef2f2; }
html.dark .ai-status-card.disabled { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); }
.ai-status-indicator {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.ai-status-indicator.green { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,.4); }
.ai-status-indicator.red { background: #ef4444; }
.ai-status-info { flex: 1; }
.ai-status-info strong { font-size: 14px; color: var(--text-primary); }
.ai-provider { display: block; font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.ai-warning { display: block; font-size: 12px; color: #dc2626; margin-top: 2px; }
.ai-features { display: flex; gap: 6px; flex-wrap: wrap; }
.feature-tag {
  padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: capitalize;
}
.feature-tag.on { background: #dcfce7; color: #16a34a; }
.feature-tag.off { background: var(--bg-surface-alt); color: var(--text-muted); }

.muted { color: var(--text-muted); }
.loading-state { text-align: center; padding: 40px; color: var(--text-muted); }

@media (max-width: 768px) {
  .two-col { flex-direction: column; }
  .col-side { width: 100%; }
  .charts-row { flex-direction: column; }
  .donut-container { flex-direction: column; align-items: center; }
  .finance-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
