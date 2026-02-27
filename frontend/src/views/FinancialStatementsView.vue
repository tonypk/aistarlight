<script setup lang="ts">
import { ref } from 'vue'
import { useAccountingStore } from '../stores/accounting'
import { currencyLocale } from '@/utils/currency'

const store = useAccountingStore()
const activeTab = ref<'balance-sheet' | 'income-statement'>('balance-sheet')
const bsDate = ref(new Date().toISOString().slice(0, 10))
const isFrom = ref(new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10))
const isTo = ref(new Date().toISOString().slice(0, 10))

function loadBS() {
  store.fetchBalanceSheet(bsDate.value)
}

function loadIS() {
  store.fetchIncomeStatement(isFrom.value, isTo.value)
}

function fmt(val: string | undefined) {
  const n = parseFloat(val || '0')
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Financial Statements</h1>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'balance-sheet' }" @click="activeTab = 'balance-sheet'">Balance Sheet</button>
      <button :class="{ active: activeTab === 'income-statement' }" @click="activeTab = 'income-statement'">Income Statement</button>
    </div>

    <!-- Balance Sheet -->
    <div v-if="activeTab === 'balance-sheet'">
      <div class="filters">
        <label>As of <input type="date" v-model="bsDate" class="input" /></label>
        <button class="btn btn-primary" @click="loadBS" :disabled="store.loading">Generate</button>
      </div>

      <div v-if="store.loading" class="loading">Generating balance sheet...</div>

      <div v-else-if="store.balanceSheet" class="statement">
        <h2 class="statement-title">Balance Sheet as of {{ store.balanceSheet.as_of_date?.slice(0, 10) }}</h2>

        <div class="statement-grid">
          <div class="section">
            <h3>Assets</h3>
            <table class="stmt-table">
              <tbody>
                <tr v-for="a in store.balanceSheet.assets" :key="a.account_id">
                  <td>{{ a.account_code }} {{ a.account_name }}</td>
                  <td class="right mono">{{ fmt(a.balance) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="total-row"><td><strong>Total Assets</strong></td><td class="right mono bold">{{ fmt(store.balanceSheet.total_assets) }}</td></tr>
              </tfoot>
            </table>
          </div>

          <div class="section">
            <h3>Liabilities</h3>
            <table class="stmt-table">
              <tbody>
                <tr v-for="l in store.balanceSheet.liabilities" :key="l.account_id">
                  <td>{{ l.account_code }} {{ l.account_name }}</td>
                  <td class="right mono">{{ fmt(l.balance) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="total-row"><td><strong>Total Liabilities</strong></td><td class="right mono bold">{{ fmt(store.balanceSheet.total_liabilities) }}</td></tr>
              </tfoot>
            </table>

            <h3>Equity</h3>
            <table class="stmt-table">
              <tbody>
                <tr v-for="e in store.balanceSheet.equity" :key="e.account_id">
                  <td>{{ e.account_code }} {{ e.account_name }}</td>
                  <td class="right mono">{{ fmt(e.balance) }}</td>
                </tr>
                <tr>
                  <td>Retained Earnings (Current Period)</td>
                  <td class="right mono">{{ fmt(store.balanceSheet.retained_earnings) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="total-row"><td><strong>Total Equity</strong></td><td class="right mono bold">{{ fmt(store.balanceSheet.total_equity) }}</td></tr>
                <tr class="grand-total"><td><strong>Total Liabilities + Equity</strong></td><td class="right mono bold">{{ fmt((parseFloat(store.balanceSheet.total_liabilities || '0') + parseFloat(store.balanceSheet.total_equity || '0')).toString()) }}</td></tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div class="balance-check" :class="{ balanced: store.balanceSheet.is_balanced, unbalanced: !store.balanceSheet.is_balanced }">
          {{ store.balanceSheet.is_balanced ? 'Balanced' : 'UNBALANCED - Assets do not equal Liabilities + Equity' }}
        </div>
      </div>
    </div>

    <!-- Income Statement -->
    <div v-if="activeTab === 'income-statement'">
      <div class="filters">
        <label>From <input type="date" v-model="isFrom" class="input" /></label>
        <label>To <input type="date" v-model="isTo" class="input" /></label>
        <button class="btn btn-primary" @click="loadIS" :disabled="store.loading">Generate</button>
      </div>

      <div v-if="store.loading" class="loading">Generating income statement...</div>

      <div v-else-if="store.incomeStatement" class="statement">
        <h2 class="statement-title">Income Statement: {{ store.incomeStatement.period_start?.slice(0, 10) }} to {{ store.incomeStatement.period_end?.slice(0, 10) }}</h2>

        <table class="stmt-table wide">
          <tbody>
            <tr class="section-header"><td colspan="2"><strong>Revenue</strong></td></tr>
            <tr v-for="r in store.incomeStatement.revenue" :key="r.account_id">
              <td class="indent">{{ r.account_code }} {{ r.account_name }}</td>
              <td class="right mono">{{ fmt(r.balance) }}</td>
            </tr>
            <tr class="subtotal"><td>Total Revenue</td><td class="right mono bold">{{ fmt(store.incomeStatement.total_revenue) }}</td></tr>

            <tr class="section-header"><td colspan="2"><strong>Cost of Sales</strong></td></tr>
            <tr v-for="c in store.incomeStatement.cogs" :key="c.account_id">
              <td class="indent">{{ c.account_code }} {{ c.account_name }}</td>
              <td class="right mono">{{ fmt(c.balance) }}</td>
            </tr>
            <tr class="subtotal"><td>Total Cost of Sales</td><td class="right mono bold">{{ fmt(store.incomeStatement.total_cogs) }}</td></tr>
            <tr class="highlight"><td><strong>Gross Profit</strong></td><td class="right mono bold">{{ fmt(store.incomeStatement.gross_profit) }}</td></tr>

            <tr class="section-header"><td colspan="2"><strong>Operating Expenses</strong></td></tr>
            <tr v-for="e in store.incomeStatement.expenses" :key="e.account_id">
              <td class="indent">{{ e.account_code }} {{ e.account_name }}</td>
              <td class="right mono">{{ fmt(e.balance) }}</td>
            </tr>
            <tr class="subtotal"><td>Total Operating Expenses</td><td class="right mono bold">{{ fmt(store.incomeStatement.total_expenses) }}</td></tr>
          </tbody>
          <tfoot>
            <tr class="grand-total"><td><strong>Net Income</strong></td><td class="right mono bold">{{ fmt(store.incomeStatement.net_income) }}</td></tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 900px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; margin: 0; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #e5e7eb; }
.tabs button { padding: 10px 20px; border: none; background: transparent; cursor: pointer; font-size: 14px; color: #6b7280; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.tabs button.active { color: #4f46e5; border-bottom-color: #4f46e5; font-weight: 600; }
.filters { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.filters label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #374151; }
.input { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn:disabled { opacity: 0.5; }
.loading { text-align: center; padding: 40px; color: #666; }
.statement { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; }
.statement-title { font-size: 18px; margin: 0 0 20px; text-align: center; color: #111; }
.statement-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.section h3 { font-size: 15px; color: #374151; margin: 16px 0 8px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }
.stmt-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.stmt-table td { padding: 6px 8px; }
.stmt-table.wide { max-width: 700px; margin: 0 auto; }
.right { text-align: right; }
.mono { font-family: monospace; }
.bold { font-weight: 600; }
.indent { padding-left: 24px !important; }
.total-row td { border-top: 1px solid #e5e7eb; padding-top: 8px; }
.subtotal td { border-top: 1px solid #f3f4f6; color: #374151; }
.highlight td { background: #f0f4ff; }
.grand-total td { border-top: 2px solid #111; font-size: 15px; padding-top: 10px; }
.section-header td { padding-top: 16px; color: #374151; }
.balance-check { text-align: center; padding: 12px; margin-top: 20px; border-radius: 6px; font-weight: 600; }
.balanced { background: #d1fae5; color: #065f46; }
.unbalanced { background: #fee2e2; color: #991b1b; }
</style>
