import { defineStore } from 'pinia'
import { ref } from 'vue'
import { accountsApi, journalApi, glApi, statementsApi, taxBridgeApi, taxExportApi, journalBridgeApi, receiptBridgeApi } from '../api/accounting'
import type { Account, JournalEntry, TrialBalanceRow, BalanceSheet, IncomeStatement, TaxCalculationResult } from '../types/accounting'
import { useToastStore } from './toast'

export const useAccountingStore = defineStore('accounting', () => {
  const toast = useToastStore()
  const loading = ref(false)

  // --- Chart of Accounts ---
  const accounts = ref<Account[]>([])
  const accountTotal = ref(0)

  async function fetchAccounts(page = 1, limit = 100) {
    loading.value = true
    try {
      const { data } = await accountsApi.list({ page, limit })
      accounts.value = data.data ?? []
      accountTotal.value = data.meta?.total ?? accounts.value.length
    } finally {
      loading.value = false
    }
  }

  async function seedAccounts() {
    loading.value = true
    try {
      await accountsApi.seed()
      toast.success('Chart of Accounts seeded successfully')
      await fetchAccounts()
    } finally {
      loading.value = false
    }
  }

  // --- Journal Entries ---
  const journalEntries = ref<JournalEntry[]>([])
  const journalTotal = ref(0)
  const currentJournal = ref<JournalEntry | null>(null)

  async function fetchJournalEntries(page = 1, limit = 20, status?: string) {
    loading.value = true
    try {
      const { data } = await journalApi.list({ page, limit, status })
      journalEntries.value = data.data ?? []
      journalTotal.value = data.meta?.total ?? journalEntries.value.length
    } finally {
      loading.value = false
    }
  }

  async function fetchJournalEntry(id: string) {
    loading.value = true
    try {
      const { data } = await journalApi.get(id)
      currentJournal.value = data.data
    } finally {
      loading.value = false
    }
  }

  async function postJournalEntry(id: string) {
    await journalApi.post(id)
    toast.success('Journal entry posted')
    await fetchJournalEntries()
  }

  async function reverseJournalEntry(id: string) {
    await journalApi.reverse(id)
    toast.success('Journal entry reversed')
    await fetchJournalEntries()
  }

  // --- General Ledger ---
  const trialBalance = ref<TrialBalanceRow[]>([])

  async function fetchTrialBalance(asOf?: string) {
    loading.value = true
    try {
      const { data } = await glApi.trialBalance({ as_of: asOf })
      trialBalance.value = data.data ?? []
    } finally {
      loading.value = false
    }
  }

  // --- Financial Statements ---
  const balanceSheet = ref<BalanceSheet | null>(null)
  const incomeStatement = ref<IncomeStatement | null>(null)

  async function fetchBalanceSheet(asOf?: string) {
    loading.value = true
    try {
      const { data } = await statementsApi.balanceSheet({ as_of: asOf })
      balanceSheet.value = data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchIncomeStatement(from: string, to: string) {
    loading.value = true
    try {
      const { data } = await statementsApi.incomeStatement({ from, to })
      incomeStatement.value = data.data
    } finally {
      loading.value = false
    }
  }

  // --- Tax Bridge ---
  const taxResult = ref<TaxCalculationResult | null>(null)

  async function calculateTax(formType: string, periodStart: string, periodEnd: string) {
    loading.value = true
    try {
      const { data } = await taxBridgeApi.calculate({ form_type: formType, period_start: periodStart, period_end: periodEnd })
      taxResult.value = data.data
      toast.success('Tax calculated from GL')
    } finally {
      loading.value = false
    }
  }

  async function exportDAT(formType: string, period: string) {
    const { data } = await taxExportApi.exportDAT(formType, period)
    const blob = new Blob([data], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formType}_${period}.dat`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('DAT file downloaded')
  }

  // --- Bridge Actions ---
  async function convertReceiptToTransactions(batchId: string, sessionId: string) {
    loading.value = true
    try {
      const { data } = await receiptBridgeApi.convert(batchId, sessionId)
      toast.success(`Created ${data.data?.count ?? 0} transactions from receipt`)
      return data.data
    } finally {
      loading.value = false
    }
  }

  async function generateJournalsFromSession(sessionId: string) {
    loading.value = true
    try {
      const { data } = await journalBridgeApi.generateFromSession(sessionId)
      toast.success(`Generated ${data.data?.count ?? 0} journal entries`)
      return data.data
    } finally {
      loading.value = false
    }
  }

  async function generateJournalsFromTransactions(txnIds: string[]) {
    loading.value = true
    try {
      const { data } = await journalBridgeApi.generateFromTransactions(txnIds)
      toast.success(`Generated ${data.data?.count ?? 0} journal entries`)
      return data.data
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    // COA
    accounts, accountTotal, fetchAccounts, seedAccounts,
    // Journal
    journalEntries, journalTotal, currentJournal,
    fetchJournalEntries, fetchJournalEntry, postJournalEntry, reverseJournalEntry,
    // GL
    trialBalance, fetchTrialBalance,
    // Financial Statements
    balanceSheet, incomeStatement, fetchBalanceSheet, fetchIncomeStatement,
    // Tax
    taxResult, calculateTax, exportDAT,
    // Bridge actions
    convertReceiptToTransactions, generateJournalsFromSession, generateJournalsFromTransactions,
  }
})
