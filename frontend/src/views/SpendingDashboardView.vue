<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { spendingApi, type SpendingDashboard } from '../api/spending'

const loading = ref(true)
const data = ref<SpendingDashboard | null>(null)

// Default: current year
const now = new Date()
const fromDate = ref(new Date(now.getFullYear(), 0, 1).toISOString().slice(0, 10))
const toDate = ref(now.toISOString().slice(0, 10))

const totalExpense = computed(() => {
  const exp = data.value?.income_expense?.find(i => i.type === 'expense')
  return exp ? parseFloat(exp.total) : 0
})

const totalIncome = computed(() => {
  const inc = data.value?.income_expense?.find(i => i.type === 'income')
  return inc ? parseFloat(inc.total) : 0
})

const netAmount = computed(() => totalIncome.value - totalExpense.value)

const maxCategoryAmount = computed(() => {
  if (!data.value?.by_category?.length) return 1
  return Math.max(...data.value.by_category.map(c => parseFloat(c.total)))
})

const maxVendorAmount = computed(() => {
  if (!data.value?.by_vendor?.length) return 1
  return Math.max(...data.value.by_vendor.map(v => parseFloat(v.total)))
})

const maxMonthAmount = computed(() => {
  if (!data.value?.by_month?.length) return 1
  return Math.max(...data.value.by_month.map(m => parseFloat(m.total)))
})

function formatAmount(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function barPercent(val: string, max: number): number {
  return Math.max((parseFloat(val) / max) * 100, 2)
}

const categoryColors = ['var(--brand-primary)', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1']

async function fetchData() {
  loading.value = true
  try {
    const res = await spendingApi.getDashboard(fromDate.value, toDate.value)
    data.value = res.data.data
  } catch {
    // handled by client interceptor
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="spending-dashboard">
    <div class="page-header">
      <h2>Spending Dashboard</h2>
      <div class="date-filters">
        <input type="date" v-model="fromDate" @change="fetchData" />
        <span class="date-sep">to</span>
        <input type="date" v-model="toDate" @change="fetchData" />
      </div>
    </div>

    <div v-if="loading" class="loading">Loading spending data...</div>

    <template v-else-if="data">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card income">
          <div class="summary-icon">📈</div>
          <div class="summary-info">
            <div class="summary-value">{{ formatAmount(totalIncome) }}</div>
            <div class="summary-label">Total Income</div>
          </div>
        </div>
        <div class="summary-card expense">
          <div class="summary-icon">📉</div>
          <div class="summary-info">
            <div class="summary-value">{{ formatAmount(totalExpense) }}</div>
            <div class="summary-label">Total Expenses</div>
          </div>
        </div>
        <div class="summary-card" :class="netAmount >= 0 ? 'positive' : 'negative'">
          <div class="summary-icon">{{ netAmount >= 0 ? '✅' : '⚠️' }}</div>
          <div class="summary-info">
            <div class="summary-value">{{ formatAmount(Math.abs(netAmount)) }}</div>
            <div class="summary-label">{{ netAmount >= 0 ? 'Net Surplus' : 'Net Deficit' }}</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon">🧾</div>
          <div class="summary-info">
            <div class="summary-value">{{ data.income_expense.reduce((s, i) => s + i.count, 0) }}</div>
            <div class="summary-label">Total Transactions</div>
          </div>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- By Category -->
        <div class="chart-card">
          <h3>Spending by Category</h3>
          <div v-if="data.by_category.length" class="bar-chart">
            <div v-for="(cat, i) in data.by_category" :key="cat.category" class="bar-row">
              <div class="bar-label">{{ cat.category || 'Uncategorized' }}</div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barPercent(cat.total, maxCategoryAmount) + '%', backgroundColor: categoryColors[i % categoryColors.length] }"
                ></div>
              </div>
              <div class="bar-value">{{ formatAmount(cat.total) }}</div>
              <div class="bar-count">{{ cat.count }}x</div>
            </div>
          </div>
          <div v-else class="empty-state">No category data for this period</div>
        </div>

        <!-- By Vendor -->
        <div class="chart-card">
          <h3>Top Vendors by Amount</h3>
          <div v-if="data.by_vendor.length" class="bar-chart">
            <div v-for="(v, i) in data.by_vendor.slice(0, 10)" :key="v.vendor" class="bar-row">
              <div class="bar-label" :title="v.vendor">{{ v.vendor.length > 25 ? v.vendor.slice(0, 22) + '...' : v.vendor }}</div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barPercent(v.total, maxVendorAmount) + '%', backgroundColor: categoryColors[i % categoryColors.length] }"
                ></div>
              </div>
              <div class="bar-value">{{ formatAmount(v.total) }}</div>
              <div class="bar-count">{{ v.count }}x</div>
            </div>
          </div>
          <div v-else class="empty-state">No vendor data for this period</div>
        </div>

        <!-- By Month -->
        <div class="chart-card full-width">
          <h3>Monthly Trend</h3>
          <div v-if="data.by_month.length" class="month-chart">
            <div v-for="m in data.by_month" :key="m.month" class="month-bar-col">
              <div class="month-amount">{{ formatAmount(m.total) }}</div>
              <div class="month-bar-wrapper">
                <div
                  class="month-bar-fill"
                  :style="{ height: barPercent(m.total, maxMonthAmount) + '%' }"
                ></div>
              </div>
              <div class="month-label">{{ m.month }}</div>
              <div class="month-count">{{ m.count }} txns</div>
            </div>
          </div>
          <div v-else class="empty-state">No monthly data for this period</div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">No spending data available</div>
  </div>
</template>

<style scoped>
.spending-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.date-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-filters input {
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-primary);
}

.date-sep {
  color: var(--text-secondary);
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-card.income { border-left: 4px solid #22c55e; }
.summary-card.expense { border-left: 4px solid #ef4444; }
.summary-card.positive { border-left: 4px solid #22c55e; }
.summary-card.negative { border-left: 4px solid #f59e0b; }

.summary-icon { font-size: 28px; }

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 20px;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-card h3 {
  margin: 0 0 16px;
  font-size: 15px;
  color: var(--text-primary);
}

/* Horizontal Bar Chart */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-row {
  display: grid;
  grid-template-columns: 120px 1fr 90px 40px;
  align-items: center;
  gap: 8px;
}

.bar-label {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  height: 20px;
  background: var(--bg-surface-hover);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
  min-width: 4px;
}

.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: right;
}

.bar-count {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
}

/* Vertical Month Chart */
.month-chart {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  min-height: 200px;
  padding-top: 20px;
}

.month-bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.month-amount {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.month-bar-wrapper {
  width: 100%;
  max-width: 40px;
  height: 140px;
  background: var(--bg-surface-hover);
  border-radius: 4px 4px 0 0;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.month-bar-fill {
  width: 100%;
  background: var(--brand-primary);
  border-radius: 4px 4px 0 0;
  transition: height 0.5s ease;
  min-height: 4px;
}

.month-label {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.month-count {
  font-size: 11px;
  color: var(--text-muted);
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 14px;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .bar-row {
    grid-template-columns: 80px 1fr 70px 32px;
  }

  .summary-cards {
    grid-template-columns: 1fr 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
