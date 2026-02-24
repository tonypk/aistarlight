<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAccountingStore } from '../stores/accounting'
import { glApi } from '../api/accounting'
import type { LedgerEntry } from '../types/accounting'

const store = useAccountingStore()
const asOfDate = ref(new Date().toISOString().slice(0, 10))
const selectedAccount = ref<{ id: string; number: string; name: string } | null>(null)
const ledgerEntries = ref<LedgerEntry[]>([])
const ledgerLoading = ref(false)
const ledgerFrom = ref(new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10))
const ledgerTo = ref(new Date().toISOString().slice(0, 10))

onMounted(() => {
  loadTrialBalance()
})

function loadTrialBalance() {
  store.fetchTrialBalance(asOfDate.value)
}

async function viewLedger(accountId: string, accountNumber: string, accountName: string) {
  selectedAccount.value = { id: accountId, number: accountNumber, name: accountName }
  ledgerLoading.value = true
  try {
    const { data } = await glApi.accountLedger(accountId, { from: ledgerFrom.value, to: ledgerTo.value })
    ledgerEntries.value = data.data ?? []
  } finally {
    ledgerLoading.value = false
  }
}

function closeLedger() {
  selectedAccount.value = null
  ledgerEntries.value = []
}

function formatAmount(val: string) {
  const n = parseFloat(val || '0')
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function totalDebit() {
  return store.trialBalance.reduce((sum, r) => sum + parseFloat(r.total_debit || '0'), 0)
}
function totalCredit() {
  return store.trialBalance.reduce((sum, r) => sum + parseFloat(r.total_credit || '0'), 0)
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>General Ledger</h1>
    </div>

    <!-- Account Ledger Detail -->
    <div v-if="selectedAccount" class="ledger-panel">
      <div class="ledger-header">
        <h2>{{ selectedAccount.number }} - {{ selectedAccount.name }}</h2>
        <button class="btn btn-secondary" @click="closeLedger">Back to Trial Balance</button>
      </div>
      <div class="ledger-filters">
        <label>From <input type="date" v-model="ledgerFrom" class="input" /></label>
        <label>To <input type="date" v-model="ledgerTo" class="input" /></label>
        <button class="btn btn-primary" @click="viewLedger(selectedAccount.id, selectedAccount.number, selectedAccount.name)">Refresh</button>
      </div>
      <div v-if="ledgerLoading" class="loading">Loading ledger...</div>
      <table v-else class="table">
        <thead>
          <tr><th>Date</th><th>#</th><th>Description</th><th>Ref</th><th class="right">Debit</th><th class="right">Credit</th><th class="right">Balance</th></tr>
        </thead>
        <tbody>
          <tr v-for="(entry, i) in ledgerEntries" :key="i">
            <td>{{ entry.entry_date?.slice(0, 10) }}</td>
            <td class="mono">{{ entry.entry_number }}</td>
            <td>{{ entry.description || '-' }}</td>
            <td>{{ entry.reference || '-' }}</td>
            <td class="right mono">{{ formatAmount(entry.debit) }}</td>
            <td class="right mono">{{ formatAmount(entry.credit) }}</td>
            <td class="right mono bold">{{ formatAmount(entry.running_balance) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!ledgerLoading && ledgerEntries.length === 0" class="empty">No entries in this period.</div>
    </div>

    <!-- Trial Balance -->
    <div v-else>
      <div class="filters">
        <label>As of <input type="date" v-model="asOfDate" class="input" /></label>
        <button class="btn btn-primary" @click="loadTrialBalance">Load</button>
      </div>

      <div v-if="store.loading" class="loading">Loading trial balance...</div>

      <table v-else class="table">
        <thead>
          <tr><th>Code</th><th>Account</th><th>Type</th><th class="right">Debit</th><th class="right">Credit</th><th class="right">Balance</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in store.trialBalance" :key="row.account_id" class="clickable" @click="viewLedger(row.account_id, row.account_number, row.account_name)">
            <td class="mono">{{ row.account_number }}</td>
            <td>{{ row.account_name }}</td>
            <td><span class="badge" :class="'badge-' + row.account_type">{{ row.account_type }}</span></td>
            <td class="right mono">{{ formatAmount(row.total_debit) }}</td>
            <td class="right mono">{{ formatAmount(row.total_credit) }}</td>
            <td class="right mono bold">{{ formatAmount(row.balance) }}</td>
          </tr>
        </tbody>
        <tfoot v-if="store.trialBalance.length > 0">
          <tr class="totals">
            <td colspan="3"><strong>Totals</strong></td>
            <td class="right mono bold">{{ formatAmount(totalDebit().toString()) }}</td>
            <td class="right mono bold">{{ formatAmount(totalCredit().toString()) }}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      <div v-if="!store.loading && store.trialBalance.length === 0" class="empty">
        No posted journal entries yet. Generate and post journal entries to see the trial balance.
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 24px; margin: 0; }
.filters, .ledger-filters { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.filters label, .ledger-filters label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #374151; }
.input { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn-secondary { background: #e5e7eb; color: #111; }
.table { width: 100%; border-collapse: collapse; font-size: 14px; }
.table th { text-align: left; padding: 10px 12px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; font-weight: 600; }
.table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; }
.right { text-align: right; }
.mono { font-family: monospace; }
.bold { font-weight: 600; }
.clickable { cursor: pointer; }
.clickable:hover { background: #f0f4ff; }
.loading, .empty { text-align: center; padding: 40px; color: #666; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; text-transform: capitalize; }
.badge-asset { background: #dbeafe; color: #1d4ed8; }
.badge-liability { background: #fce7f3; color: #be185d; }
.badge-equity { background: #ede9fe; color: #6d28d9; }
.badge-revenue { background: #d1fae5; color: #065f46; }
.badge-expense { background: #fef3c7; color: #92400e; }
.totals td { background: #f9fafb; border-top: 2px solid #e5e7eb; }
.ledger-panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; }
.ledger-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ledger-header h2 { margin: 0; font-size: 18px; }
</style>
