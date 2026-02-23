import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { reconciliationApi } from '../api/transactions'
import type {
  Anomaly,
  ReconciliationResult,
  ReconciliationSession,
  Transaction,
  TransactionFilters,
  VatSummary,
} from '../types/transaction'

export const useTransactionStore = defineStore('transaction', () => {
  // State
  const sessions = ref<ReconciliationSession[]>([])
  const currentSession = ref<ReconciliationSession | null>(null)
  const transactions = ref<Transaction[]>([])
  const transactionTotal = ref(0)
  const anomalies = ref<Anomaly[]>([])
  const anomalyTotal = ref(0)
  const summary = ref<VatSummary | null>(null)
  const reconciliationResult = ref<ReconciliationResult | null>(null)
  const loading = ref(false)
  const classifying = ref(false)
  const filters = ref<TransactionFilters>({})

  // Computed
  const hasSession = computed(() => currentSession.value !== null)

  const sessionStatus = computed(() => currentSession.value?.status ?? 'draft')

  const openAnomalyCount = computed(
    () => anomalies.value.filter((a) => a.status === 'open').length
  )

  const confidenceDistribution = computed(() => {
    const high = transactions.value.filter((t) => t.confidence >= 0.8).length
    const medium = transactions.value.filter(
      (t) => t.confidence >= 0.5 && t.confidence < 0.8
    ).length
    const low = transactions.value.filter((t) => t.confidence < 0.5).length
    return { high, medium, low }
  })

  // Actions — Sessions

  async function fetchSessions(page = 1) {
    loading.value = true
    try {
      const res = await reconciliationApi.listSessions(page)
      sessions.value = [...res.data.data]
    } finally {
      loading.value = false
    }
  }

  async function createSession(period: string, reportId?: string) {
    loading.value = true
    try {
      const res = await reconciliationApi.createSession(period, reportId)
      currentSession.value = { ...res.data.data }
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchSession(id: string) {
    const res = await reconciliationApi.getSession(id)
    currentSession.value = { ...res.data.data }
    return res.data.data
  }

  async function deleteSession(id: string) {
    await reconciliationApi.deleteSession(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSession.value?.id === id) {
      currentSession.value = null
    }
  }

  // Actions — Files

  async function addFile(
    sessionId: string,
    fileId: string,
    sourceType: string,
    sheetName?: string | null,
    columnMappings?: Record<string, string> | null
  ) {
    loading.value = true
    try {
      const res = await reconciliationApi.addFile(sessionId, {
        file_id: fileId,
        source_type: sourceType,
        sheet_name: sheetName,
        column_mappings: columnMappings,
      })
      // Refresh session to get updated source_files
      await fetchSession(sessionId)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  // Actions — Classification

  async function classifyTransactions(sessionId: string, force = false) {
    classifying.value = true
    try {
      const res = await reconciliationApi.classify(sessionId, force)
      // Refresh transactions after classification
      await fetchTransactions(sessionId)
      await fetchSession(sessionId)
      return res.data.data
    } finally {
      classifying.value = false
    }
  }

  // Actions — Transactions

  async function fetchTransactions(sessionId: string, page = 1, limit = 50) {
    loading.value = true
    try {
      const res = await reconciliationApi.listTransactions(
        sessionId,
        page,
        limit,
        filters.value
      )
      transactions.value = [...res.data.data]
      transactionTotal.value = res.data.meta?.total ?? res.data.data.length
    } finally {
      loading.value = false
    }
  }

  async function updateTransaction(
    sessionId: string,
    txnId: string,
    data: { vat_type?: string; category?: string; tin?: string }
  ) {
    const res = await reconciliationApi.updateTransaction(sessionId, txnId, data)
    const updated = res.data.data as Transaction
    transactions.value = transactions.value.map((t) =>
      t.id === txnId ? { ...updated } : t
    )
    return updated
  }

  function setFilters(newFilters: TransactionFilters) {
    filters.value = { ...newFilters }
  }

  // Actions — Anomalies

  async function detectAnomalies(sessionId: string) {
    loading.value = true
    try {
      const res = await reconciliationApi.detectAnomalies(sessionId)
      await fetchAnomalies(sessionId)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchAnomalies(sessionId: string, page = 1, statusFilter?: string) {
    const res = await reconciliationApi.listAnomalies(sessionId, page, 50, statusFilter)
    anomalies.value = [...res.data.data]
    anomalyTotal.value = res.data.meta?.total ?? res.data.data.length
  }

  async function resolveAnomaly(
    sessionId: string,
    anomalyId: string,
    status: string,
    note?: string
  ) {
    const res = await reconciliationApi.resolveAnomaly(sessionId, anomalyId, {
      status,
      resolution_note: note,
    })
    const updated = res.data.data as Anomaly
    anomalies.value = anomalies.value.map((a) =>
      a.id === anomalyId ? { ...updated } : a
    )
    return updated
  }

  // Actions — Summary & Reconciliation

  async function fetchSummary(sessionId: string) {
    const res = await reconciliationApi.getSummary(sessionId)
    summary.value = { ...res.data.data }
    return res.data.data
  }

  async function runReconciliation(
    sessionId: string,
    reportId?: string,
    amountTolerance?: number,
    dateTolerance?: number
  ) {
    loading.value = true
    try {
      const res = await reconciliationApi.reconcile(sessionId, {
        report_id: reportId,
        amount_tolerance: amountTolerance,
        date_tolerance_days: dateTolerance,
      })
      reconciliationResult.value = { ...res.data.data }
      await fetchSession(sessionId)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  // Actions — Export

  async function exportCsv(sessionId: string) {
    let url = ''
    try {
      const res = await reconciliationApi.exportCsv(sessionId)
      url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `reconciliation_${currentSession.value?.period ?? sessionId}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } finally {
      if (url) window.URL.revokeObjectURL(url)
    }
  }

  function reset() {
    currentSession.value = null
    transactions.value = []
    transactionTotal.value = 0
    anomalies.value = []
    anomalyTotal.value = 0
    summary.value = null
    reconciliationResult.value = null
    filters.value = {}
  }

  return {
    // State
    sessions,
    currentSession,
    transactions,
    transactionTotal,
    anomalies,
    anomalyTotal,
    summary,
    reconciliationResult,
    loading,
    classifying,
    filters,
    // Computed
    hasSession,
    sessionStatus,
    openAnomalyCount,
    confidenceDistribution,
    // Actions
    fetchSessions,
    createSession,
    fetchSession,
    deleteSession,
    addFile,
    classifyTransactions,
    fetchTransactions,
    updateTransaction,
    setFilters,
    detectAnomalies,
    fetchAnomalies,
    resolveAnomaly,
    fetchSummary,
    runReconciliation,
    exportCsv,
    reset,
  }
})
