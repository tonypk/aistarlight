<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWithholdingStore } from '../stores/withholding'
import { useAuthStore } from '../stores/auth'
import EwtSummaryCards from '../components/withholding/EwtSummaryCards.vue'
import CertificateTable from '../components/withholding/CertificateTable.vue'

const store = useWithholdingStore()
const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

const selectedPeriod = ref('')
const error = ref('')

// Generate period options (last 12 months)
const periodOptions = computed(() => {
  const options: string[] = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    options.push(`${y}-${m}`)
  }
  return options
})

onMounted(async () => {
  if (!selectedPeriod.value && periodOptions.value.length > 0) {
    selectedPeriod.value = periodOptions.value[0]
  }
  await loadData()
})

async function loadData() {
  if (!selectedPeriod.value) return
  error.value = ''
  try {
    await Promise.all([
      store.fetchEwtSummary(selectedPeriod.value),
      store.fetchCertificates(1, 50, selectedPeriod.value),
    ])
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Failed to load data'
  }
}

async function handleDownloadCert(certId: string) {
  try {
    await store.downloadCertificate(certId)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Download failed'
  }
}

async function handleDownloadSawt(format: 'csv' | 'pdf') {
  try {
    await store.downloadSawt(selectedPeriod.value, format)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? (isSG.value ? 'WHT summary download failed' : 'SAWT download failed')
  }
}
</script>

<template>
  <div class="withholding-view">
    <div class="view-header">
      <h2>{{ isSG ? 'Withholding Tax (S45) Dashboard' : 'Withholding Tax Dashboard' }}</h2>
      <div class="header-actions">
        <router-link to="/suppliers" class="btn">Manage Suppliers</router-link>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Period Selector -->
    <div class="control-panel">
      <div class="control-row">
        <label>Period:</label>
        <select v-model="selectedPeriod" @change="loadData">
          <option v-for="p in periodOptions" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="control-actions">
        <button class="btn" @click="handleDownloadSawt('csv')">{{ isSG ? 'Download WHT Summary (CSV)' : 'Download SAWT (CSV)' }}</button>
        <button class="btn" @click="handleDownloadSawt('pdf')">{{ isSG ? 'Download WHT Summary (PDF)' : 'Download SAWT (PDF)' }}</button>
      </div>
    </div>

    <!-- EWT/WHT Summary Cards -->
    <EwtSummaryCards v-if="store.ewtSummary" :summary="store.ewtSummary" :jurisdiction="auth.jurisdiction" />

    <div v-if="!store.ewtSummary && !store.loading" class="empty-state">
      <p>No withholding tax data for this period.</p>
      <p class="hint">
        {{ isSG
          ? 'To generate data: Go to Reconciliation, classify transactions for WHT, then generate S45 certificates.'
          : 'To generate data: Go to Reconciliation, classify transactions for EWT, then generate BIR 2307 certificates.'
        }}
      </p>
    </div>

    <!-- Certificates -->
    <div class="section" v-if="store.certificates.length > 0">
      <h3>{{ isSG ? 'S45 WHT Certificates' : 'BIR 2307 Certificates' }}</h3>
      <CertificateTable
        :certificates="store.certificates"
        :jurisdiction="auth.jurisdiction"
        @download="handleDownloadCert"
      />
    </div>
  </div>
</template>

<style scoped>
.withholding-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.view-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }

.control-panel {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.control-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.control-row label { font-size: 14px; font-weight: 500; }
.control-row select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.control-actions { display: flex; gap: 8px; }

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}
.empty-state p { margin: 0 0 8px; color: #374151; }
.empty-state .hint { color: #9ca3af; font-size: 14px; }

.section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}
.section h3 { margin: 0 0 16px; font-size: 16px; }

.btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  color: inherit;
}
.btn:hover { background: #f3f4f6; }
</style>
