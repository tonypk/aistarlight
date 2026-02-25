<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useAccountingStore } from '../stores/accounting'

const store = useAccountingStore()
const filterType = ref('')
const search = ref('')

onMounted(() => {
  store.fetchAccounts()
})

const filteredAccounts = computed(() => {
  let list = store.accounts
  if (filterType.value) {
    list = list.filter(a => a.account_type === filterType.value)
  }
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(a =>
      a.account_number.includes(q) ||
      a.name.toLowerCase().includes(q)
    )
  }
  return list
})

const accountTypes = ['asset', 'liability', 'equity', 'revenue', 'expense']

const groupedAccounts = computed(() => {
  const groups: Record<string, typeof filteredAccounts.value> = {}
  for (const acct of filteredAccounts.value) {
    const prefix = acct.account_number.charAt(0)
    const label = prefix === '1' ? 'Assets' : prefix === '2' ? 'Liabilities' : prefix === '3' ? 'Equity' : prefix === '4' ? 'Revenue' : prefix === '5' ? 'Cost of Sales' : 'Expenses'
    if (!groups[label]) groups[label] = []
    groups[label].push(acct)
  }
  return groups
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Chart of Accounts</h1>
      <div class="actions">
        <button class="btn btn-secondary" @click="store.seedAccounts()" :disabled="store.loading" data-testid="coa-seed-btn">
          Seed PH Standard COA
        </button>
      </div>
    </div>

    <div class="filters">
      <input v-model="search" placeholder="Search by code or name..." class="input" />
      <select v-model="filterType" class="select">
        <option value="">All Types</option>
        <option v-for="t in accountTypes" :key="t" :value="t">{{ t }}</option>
      </select>
    </div>

    <div v-if="store.loading" class="loading">Loading accounts...</div>

    <div v-else-if="store.accounts.length === 0" class="empty">
      <p>No accounts found. Seed the Philippine Standard Chart of Accounts to get started.</p>
    </div>

    <div v-else class="account-groups" data-testid="coa-groups">
      <div v-for="(accts, group) in groupedAccounts" :key="group" class="account-group">
        <h3 class="group-title">{{ group }}</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Type</th>
              <th>Normal</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in accts" :key="a.id">
              <td class="mono">{{ a.account_number }}</td>
              <td>{{ a.name }}</td>
              <td><span class="badge" :class="'badge-' + a.account_type">{{ a.account_type }}</span></td>
              <td>{{ a.normal_balance }}</td>
              <td class="desc">{{ a.description }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 24px; margin: 0; }
.filters { display: flex; gap: 12px; margin-bottom: 20px; }
.input, .select { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
.input { flex: 1; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-secondary { background: #e5e7eb; color: #111; }
.btn-secondary:hover { background: #d1d5db; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.loading, .empty { text-align: center; padding: 40px; color: #666; }
.account-group { margin-bottom: 24px; }
.group-title { font-size: 16px; color: #374151; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid #e5e7eb; }
.table { width: 100%; border-collapse: collapse; font-size: 14px; }
.table th { text-align: left; padding: 8px 12px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; font-weight: 600; color: #374151; }
.table td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; }
.mono { font-family: monospace; font-weight: 600; }
.desc { color: #6b7280; font-size: 13px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; text-transform: capitalize; }
.badge-asset { background: #dbeafe; color: #1d4ed8; }
.badge-liability { background: #fce7f3; color: #be185d; }
.badge-equity { background: #ede9fe; color: #6d28d9; }
.badge-revenue { background: #d1fae5; color: #065f46; }
.badge-expense { background: #fef3c7; color: #92400e; }
</style>
