<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAccountingStore } from '../stores/accounting'
import { currencyLocale } from '@/utils/currency'

const store = useAccountingStore()
const activeTab = ref<'balance-sheet' | 'income-statement' | 'cash-flow'>('balance-sheet')

// Date controls
const bsDate = ref(new Date().toISOString().slice(0, 10))
const isFrom = ref(new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10))
const isTo = ref(new Date().toISOString().slice(0, 10))
const cfFrom = ref(new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10))
const cfTo = ref(new Date().toISOString().slice(0, 10))

// Comparative mode
const compareEnabled = ref(false)
const bsCompareDate = ref(new Date(new Date().getFullYear() - 1, 11, 31).toISOString().slice(0, 10))
const isPriorFrom = ref(new Date(new Date().getFullYear() - 1, 0, 1).toISOString().slice(0, 10))
const isPriorTo = ref(new Date(new Date().getFullYear() - 1, 11, 31).toISOString().slice(0, 10))

function loadBS() {
  store.fetchBalanceSheet(
    bsDate.value,
    compareEnabled.value ? bsCompareDate.value : undefined
  )
}

function loadIS() {
  store.fetchIncomeStatement(
    isFrom.value,
    isTo.value,
    compareEnabled.value ? isPriorFrom.value : undefined,
    compareEnabled.value ? isPriorTo.value : undefined
  )
}

function loadCF() {
  store.fetchCashFlow(cfFrom.value, cfTo.value)
}

function fmt(val: string | undefined) {
  const n = parseFloat(val || '0')
  return n.toLocaleString(currencyLocale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function num(val: string | undefined): number {
  return parseFloat(val || '0')
}

// Financial Ratios (computed from current data)
const ratios = computed(() => {
  const bs = store.balanceSheet
  const is = store.incomeStatement
  if (!bs && !is) return null

  const totalAssets = num(bs?.total_assets)
  const totalLiab = num(bs?.total_liabilities)
  const totalEquity = num(bs?.total_equity)
  const revenue = num(is?.total_revenue)
  const netIncome = num(is?.net_income)
  const grossProfit = num(is?.gross_profit)

  // Extract current assets / current liabilities from groups
  let currentAssets = 0
  let currentLiab = 0
  if (bs) {
    for (const grp of bs.assets) {
      if (grp.group_name === 'Current Assets') {
        currentAssets = num(grp.total)
      }
    }
    for (const grp of bs.liabilities) {
      if (grp.group_name === 'Current Liabilities') {
        currentLiab = num(grp.total)
      }
    }
  }

  return {
    currentRatio: currentLiab !== 0 ? (currentAssets / currentLiab).toFixed(2) : '—',
    debtToEquity: totalEquity !== 0 ? (totalLiab / totalEquity).toFixed(2) : '—',
    grossMargin: revenue !== 0 ? ((grossProfit / revenue) * 100).toFixed(1) + '%' : '—',
    netMargin: revenue !== 0 ? ((netIncome / revenue) * 100).toFixed(1) + '%' : '—',
    roa: totalAssets !== 0 ? ((netIncome / totalAssets) * 100).toFixed(1) + '%' : '—',
    roe: totalEquity !== 0 ? ((netIncome / totalEquity) * 100).toFixed(1) + '%' : '—',
  }
})

const isComparative = computed(() => !!store.balanceSheet?.prior_as_of_date || !!store.incomeStatement?.prior_period_start)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Financial Statements</h1>
      <label class="compare-toggle">
        <input type="checkbox" v-model="compareEnabled" />
        Compare Period
      </label>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'balance-sheet' }" @click="activeTab = 'balance-sheet'">Balance Sheet</button>
      <button :class="{ active: activeTab === 'income-statement' }" @click="activeTab = 'income-statement'">Income Statement</button>
      <button :class="{ active: activeTab === 'cash-flow' }" @click="activeTab = 'cash-flow'">Cash Flow</button>
    </div>

    <!-- Balance Sheet -->
    <div v-if="activeTab === 'balance-sheet'">
      <div class="filters">
        <label>As of <input type="date" v-model="bsDate" class="input" /></label>
        <template v-if="compareEnabled">
          <label>Prior <input type="date" v-model="bsCompareDate" class="input" /></label>
        </template>
        <button class="btn btn-primary" @click="loadBS" :disabled="store.loading">Generate</button>
      </div>

      <div v-if="store.loading" class="loading">Generating balance sheet...</div>

      <div v-else-if="store.balanceSheet" class="statement">
        <h2 class="statement-title">Balance Sheet as of {{ store.balanceSheet.as_of_date?.slice(0, 10) }}</h2>

        <div class="statement-grid">
          <div class="section">
            <h3>Assets</h3>
            <table class="stmt-table">
              <thead v-if="isComparative">
                <tr><th></th><th class="right">Current</th><th class="right">Prior</th><th class="right">Change</th></tr>
              </thead>
              <tbody>
                <template v-for="grp in store.balanceSheet.assets" :key="grp.group_name">
                  <tr class="group-header"><td :colspan="isComparative ? 4 : 2"><strong>{{ grp.group_name }}</strong></td></tr>
                  <tr v-for="a in grp.accounts" :key="a.account_id">
                    <td class="indent">{{ a.account_code }} {{ a.account_name }}</td>
                    <td class="right mono">{{ fmt(a.balance) }}</td>
                    <template v-if="isComparative">
                      <td class="right mono muted">{{ fmt(a.prior_balance) }}</td>
                      <td class="right mono" :class="{ positive: num(a.change) > 0, negative: num(a.change) < 0 }">{{ fmt(a.change) }}</td>
                    </template>
                  </tr>
                  <tr class="subtotal">
                    <td>Subtotal {{ grp.group_name }}</td>
                    <td class="right mono bold">{{ fmt(grp.total) }}</td>
                    <template v-if="isComparative">
                      <td class="right mono muted">{{ fmt(grp.prior_total) }}</td>
                      <td></td>
                    </template>
                  </tr>
                </template>
              </tbody>
              <tfoot>
                <tr class="total-row">
                  <td><strong>Total Assets</strong></td>
                  <td class="right mono bold">{{ fmt(store.balanceSheet.total_assets) }}</td>
                  <template v-if="isComparative">
                    <td class="right mono muted">{{ fmt(store.balanceSheet.prior_total_assets) }}</td>
                    <td></td>
                  </template>
                </tr>
              </tfoot>
            </table>
          </div>

          <div class="section">
            <h3>Liabilities</h3>
            <table class="stmt-table">
              <thead v-if="isComparative">
                <tr><th></th><th class="right">Current</th><th class="right">Prior</th><th class="right">Change</th></tr>
              </thead>
              <tbody>
                <template v-for="grp in store.balanceSheet.liabilities" :key="grp.group_name">
                  <tr class="group-header"><td :colspan="isComparative ? 4 : 2"><strong>{{ grp.group_name }}</strong></td></tr>
                  <tr v-for="l in grp.accounts" :key="l.account_id">
                    <td class="indent">{{ l.account_code }} {{ l.account_name }}</td>
                    <td class="right mono">{{ fmt(l.balance) }}</td>
                    <template v-if="isComparative">
                      <td class="right mono muted">{{ fmt(l.prior_balance) }}</td>
                      <td class="right mono" :class="{ positive: num(l.change) > 0, negative: num(l.change) < 0 }">{{ fmt(l.change) }}</td>
                    </template>
                  </tr>
                </template>
              </tbody>
              <tfoot>
                <tr class="total-row">
                  <td><strong>Total Liabilities</strong></td>
                  <td class="right mono bold">{{ fmt(store.balanceSheet.total_liabilities) }}</td>
                  <template v-if="isComparative">
                    <td class="right mono muted">{{ fmt(store.balanceSheet.prior_total_liab) }}</td>
                    <td></td>
                  </template>
                </tr>
              </tfoot>
            </table>

            <h3>Equity</h3>
            <table class="stmt-table">
              <tbody>
                <template v-for="grp in store.balanceSheet.equity" :key="grp.group_name">
                  <tr v-for="e in grp.accounts" :key="e.account_id">
                    <td>{{ e.account_code }} {{ e.account_name }}</td>
                    <td class="right mono">{{ fmt(e.balance) }}</td>
                    <template v-if="isComparative">
                      <td class="right mono muted">{{ fmt(e.prior_balance) }}</td>
                      <td class="right mono" :class="{ positive: num(e.change) > 0, negative: num(e.change) < 0 }">{{ fmt(e.change) }}</td>
                    </template>
                  </tr>
                </template>
                <tr>
                  <td>Retained Earnings (Current Period)</td>
                  <td class="right mono">{{ fmt(store.balanceSheet.retained_earnings) }}</td>
                  <template v-if="isComparative">
                    <td class="right mono muted">{{ fmt(store.balanceSheet.prior_retained_earn) }}</td>
                    <td></td>
                  </template>
                </tr>
              </tbody>
              <tfoot>
                <tr class="total-row"><td><strong>Total Equity</strong></td><td class="right mono bold">{{ fmt(store.balanceSheet.total_equity) }}</td>
                  <template v-if="isComparative"><td class="right mono muted">{{ fmt(store.balanceSheet.prior_total_equity) }}</td><td></td></template>
                </tr>
                <tr class="grand-total"><td><strong>Total Liabilities + Equity</strong></td><td class="right mono bold">{{ fmt((num(store.balanceSheet.total_liabilities) + num(store.balanceSheet.total_equity)).toString()) }}</td>
                  <template v-if="isComparative"><td></td><td></td></template>
                </tr>
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
        <template v-if="compareEnabled">
          <label>Prior From <input type="date" v-model="isPriorFrom" class="input" /></label>
          <label>Prior To <input type="date" v-model="isPriorTo" class="input" /></label>
        </template>
        <button class="btn btn-primary" @click="loadIS" :disabled="store.loading">Generate</button>
      </div>

      <div v-if="store.loading" class="loading">Generating income statement...</div>

      <div v-else-if="store.incomeStatement" class="statement">
        <h2 class="statement-title">Income Statement: {{ store.incomeStatement.period_start?.slice(0, 10) }} to {{ store.incomeStatement.period_end?.slice(0, 10) }}</h2>

        <table class="stmt-table wide">
          <thead v-if="isComparative">
            <tr><th></th><th class="right">Current</th><th class="right">Prior</th><th class="right">Change</th></tr>
          </thead>
          <tbody>
            <tr class="section-header"><td :colspan="isComparative ? 4 : 2"><strong>Revenue</strong></td></tr>
            <tr v-for="r in store.incomeStatement.revenue" :key="r.account_id">
              <td class="indent">{{ r.account_code }} {{ r.account_name }}</td>
              <td class="right mono">{{ fmt(r.balance) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(r.prior_balance) }}</td>
                <td class="right mono" :class="{ positive: num(r.change) > 0, negative: num(r.change) < 0 }">{{ fmt(r.change) }}</td>
              </template>
            </tr>
            <tr class="subtotal">
              <td>Total Revenue</td>
              <td class="right mono bold">{{ fmt(store.incomeStatement.total_revenue) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(store.incomeStatement.prior_revenue) }}</td>
                <td></td>
              </template>
            </tr>

            <tr class="section-header"><td :colspan="isComparative ? 4 : 2"><strong>Cost of Sales</strong></td></tr>
            <tr v-for="c in store.incomeStatement.cogs" :key="c.account_id">
              <td class="indent">{{ c.account_code }} {{ c.account_name }}</td>
              <td class="right mono">{{ fmt(c.balance) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(c.prior_balance) }}</td>
                <td class="right mono" :class="{ positive: num(c.change) > 0, negative: num(c.change) < 0 }">{{ fmt(c.change) }}</td>
              </template>
            </tr>
            <tr class="subtotal">
              <td>Total Cost of Sales</td>
              <td class="right mono bold">{{ fmt(store.incomeStatement.total_cogs) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(store.incomeStatement.prior_cogs) }}</td>
                <td></td>
              </template>
            </tr>
            <tr class="highlight">
              <td><strong>Gross Profit</strong></td>
              <td class="right mono bold">{{ fmt(store.incomeStatement.gross_profit) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(store.incomeStatement.prior_gross_profit) }}</td>
                <td></td>
              </template>
            </tr>

            <tr class="section-header"><td :colspan="isComparative ? 4 : 2"><strong>Operating Expenses</strong></td></tr>
            <tr v-for="e in store.incomeStatement.expenses" :key="e.account_id">
              <td class="indent">{{ e.account_code }} {{ e.account_name }}</td>
              <td class="right mono">{{ fmt(e.balance) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(e.prior_balance) }}</td>
                <td class="right mono" :class="{ positive: num(e.change) > 0, negative: num(e.change) < 0 }">{{ fmt(e.change) }}</td>
              </template>
            </tr>
            <tr class="subtotal">
              <td>Total Operating Expenses</td>
              <td class="right mono bold">{{ fmt(store.incomeStatement.total_expenses) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(store.incomeStatement.prior_expenses) }}</td>
                <td></td>
              </template>
            </tr>
          </tbody>
          <tfoot>
            <tr class="grand-total">
              <td><strong>Net Income</strong></td>
              <td class="right mono bold">{{ fmt(store.incomeStatement.net_income) }}</td>
              <template v-if="isComparative">
                <td class="right mono muted">{{ fmt(store.incomeStatement.prior_net_income) }}</td>
                <td></td>
              </template>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Cash Flow Statement -->
    <div v-if="activeTab === 'cash-flow'">
      <div class="filters">
        <label>From <input type="date" v-model="cfFrom" class="input" /></label>
        <label>To <input type="date" v-model="cfTo" class="input" /></label>
        <button class="btn btn-primary" @click="loadCF" :disabled="store.loading">Generate</button>
      </div>

      <div v-if="store.loading" class="loading">Generating cash flow statement...</div>

      <div v-else-if="store.cashFlowStatement" class="statement">
        <h2 class="statement-title">Cash Flow Statement: {{ store.cashFlowStatement.period_start?.slice(0, 10) }} to {{ store.cashFlowStatement.period_end?.slice(0, 10) }}</h2>

        <table class="stmt-table wide">
          <tbody>
            <tr class="section-header"><td colspan="2"><strong>Operating Activities</strong></td></tr>
            <tr>
              <td class="indent">Net Income</td>
              <td class="right mono">{{ fmt(store.cashFlowStatement.net_income) }}</td>
            </tr>
            <tr v-if="num(store.cashFlowStatement.depreciation_amort) !== 0">
              <td class="indent">Depreciation & Amortization</td>
              <td class="right mono">{{ fmt(store.cashFlowStatement.depreciation_amort) }}</td>
            </tr>
            <tr v-for="wc in store.cashFlowStatement.working_capital_changes" :key="wc.account_id">
              <td class="indent">{{ wc.account_name }}</td>
              <td class="right mono">{{ fmt(wc.balance) }}</td>
            </tr>
            <tr class="subtotal">
              <td><strong>Net Cash from Operations</strong></td>
              <td class="right mono bold">{{ fmt(store.cashFlowStatement.operating_total) }}</td>
            </tr>

            <tr class="section-header"><td colspan="2"><strong>Investing Activities</strong></td></tr>
            <tr v-for="inv in store.cashFlowStatement.investing_items" :key="inv.account_id">
              <td class="indent">{{ inv.account_name }}</td>
              <td class="right mono">{{ fmt(inv.balance) }}</td>
            </tr>
            <tr v-if="!store.cashFlowStatement.investing_items?.length" class="empty-row">
              <td class="indent muted" colspan="2">No investing activities</td>
            </tr>
            <tr class="subtotal">
              <td><strong>Net Cash from Investing</strong></td>
              <td class="right mono bold">{{ fmt(store.cashFlowStatement.investing_total) }}</td>
            </tr>

            <tr class="section-header"><td colspan="2"><strong>Financing Activities</strong></td></tr>
            <tr v-for="fin in store.cashFlowStatement.financing_items" :key="fin.account_id">
              <td class="indent">{{ fin.account_name }}</td>
              <td class="right mono">{{ fmt(fin.balance) }}</td>
            </tr>
            <tr v-if="!store.cashFlowStatement.financing_items?.length" class="empty-row">
              <td class="indent muted" colspan="2">No financing activities</td>
            </tr>
            <tr class="subtotal">
              <td><strong>Net Cash from Financing</strong></td>
              <td class="right mono bold">{{ fmt(store.cashFlowStatement.financing_total) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="grand-total">
              <td><strong>Net Change in Cash</strong></td>
              <td class="right mono bold" :class="{ positive: num(store.cashFlowStatement.net_change) > 0, negative: num(store.cashFlowStatement.net_change) < 0 }">{{ fmt(store.cashFlowStatement.net_change) }}</td>
            </tr>
            <tr>
              <td>Beginning Cash</td>
              <td class="right mono">{{ fmt(store.cashFlowStatement.beginning_cash) }}</td>
            </tr>
            <tr class="total-row">
              <td><strong>Ending Cash</strong></td>
              <td class="right mono bold">{{ fmt(store.cashFlowStatement.ending_cash) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Financial Ratios Panel -->
    <div v-if="ratios && (store.balanceSheet || store.incomeStatement)" class="ratios-panel">
      <h3 class="section-title">Key Financial Ratios</h3>
      <div class="ratios-grid">
        <div class="ratio-card">
          <div class="ratio-label">Current Ratio</div>
          <div class="ratio-value">{{ ratios.currentRatio }}</div>
          <div class="ratio-desc">Current Assets / Current Liabilities</div>
        </div>
        <div class="ratio-card">
          <div class="ratio-label">Debt to Equity</div>
          <div class="ratio-value">{{ ratios.debtToEquity }}</div>
          <div class="ratio-desc">Total Liabilities / Total Equity</div>
        </div>
        <div class="ratio-card">
          <div class="ratio-label">Gross Margin</div>
          <div class="ratio-value">{{ ratios.grossMargin }}</div>
          <div class="ratio-desc">Gross Profit / Revenue</div>
        </div>
        <div class="ratio-card">
          <div class="ratio-label">Net Margin</div>
          <div class="ratio-value">{{ ratios.netMargin }}</div>
          <div class="ratio-desc">Net Income / Revenue</div>
        </div>
        <div class="ratio-card">
          <div class="ratio-label">ROA</div>
          <div class="ratio-value">{{ ratios.roa }}</div>
          <div class="ratio-desc">Net Income / Total Assets</div>
        </div>
        <div class="ratio-card">
          <div class="ratio-label">ROE</div>
          <div class="ratio-value">{{ ratios.roe }}</div>
          <div class="ratio-desc">Net Income / Total Equity</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 24px; margin: 0; }
.compare-toggle { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--text-secondary); cursor: pointer; }
.compare-toggle input { cursor: pointer; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid var(--border-default); }
.tabs button { padding: 10px 20px; border: none; background: transparent; cursor: pointer; font-size: 14px; color: var(--text-secondary); border-bottom: 2px solid transparent; margin-bottom: -2px; }
.tabs button.active { color: var(--brand-primary); border-bottom-color: var(--brand-primary); font-weight: 600; }
.filters { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.filters label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--text-primary); }
.input { padding: 8px 12px; border: 1px solid var(--border-default); border-radius: 6px; font-size: 14px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary { background: var(--brand-primary); color: #fff; }
.btn-primary:hover { background: var(--brand-primary-hover); }
.btn:disabled { opacity: 0.5; }
.loading { text-align: center; padding: 40px; color: #666; }
.statement { background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 8px; padding: 24px; }
.statement-title { font-size: 18px; margin: 0 0 20px; text-align: center; color: var(--text-primary); }
.statement-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.section h3 { font-size: 15px; color: var(--text-primary); margin: 16px 0 8px; border-bottom: 1px solid var(--border-default); padding-bottom: 4px; }
.section-title { font-size: 16px; margin-bottom: 12px; color: var(--text-primary); }
.stmt-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.stmt-table th { font-size: 12px; color: var(--text-muted); font-weight: 500; padding: 6px 8px; }
.stmt-table td { padding: 6px 8px; }
.stmt-table.wide { max-width: 750px; margin: 0 auto; }
.right { text-align: right; }
.mono { font-family: monospace; }
.bold { font-weight: 600; }
.indent { padding-left: 24px !important; }
.muted { color: var(--text-muted); }
.positive { color: #16a34a; }
.negative { color: #dc2626; }
.group-header td { padding-top: 12px; font-size: 13px; color: var(--text-secondary); }
.total-row td { border-top: 1px solid var(--border-default); padding-top: 8px; }
.subtotal td { border-top: 1px solid #f3f4f6; color: var(--text-primary); }
.highlight td { background: #f0f4ff; }
html.dark .highlight td { background: rgba(99,102,241,0.08); }
.grand-total td { border-top: 2px solid #111; font-size: 15px; padding-top: 10px; }
html.dark .grand-total td { border-top-color: #555; }
.section-header td { padding-top: 16px; color: var(--text-primary); }
.balance-check { text-align: center; padding: 12px; margin-top: 20px; border-radius: 6px; font-weight: 600; }
.balanced { background: #d1fae5; color: #065f46; }
.unbalanced { background: #fee2e2; color: #991b1b; }
.empty-row td { font-style: italic; }

/* Financial Ratios Panel */
.ratios-panel {
  margin-top: 28px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 24px;
}
.ratios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}
.ratio-card {
  text-align: center;
  padding: 16px 12px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
}
.ratio-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.ratio-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.ratio-desc { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

@media (max-width: 768px) {
  .statement-grid { grid-template-columns: 1fr; }
  .filters { flex-direction: column; align-items: flex-start; }
  .ratios-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
