<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWithholdingStore } from '../stores/withholding'
import { useAuthStore } from '../stores/auth'
import EwtSummaryCards from '../components/withholding/EwtSummaryCards.vue'
import CertificateTable from '../components/withholding/CertificateTable.vue'

const { t } = useI18n()
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
    error.value = e?.response?.data?.error ?? t('withholding.loadFailed')
  }
}

async function handleDownloadCert(certId: string) {
  try {
    await store.downloadCertificate(certId)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('withholding.downloadFailed')
  }
}

async function handleDownloadSawt(format: 'csv' | 'pdf') {
  try {
    await store.downloadSawt(selectedPeriod.value, format)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? (isSG.value ? t('withholding.whtDownloadFailed') : t('withholding.sawtDownloadFailed'))
  }
}
</script>

<template>
  <div class="withholding-view">
    <div class="view-header">
      <h2>{{ isSG ? t('withholding.titleSG') : t('withholding.titlePH') }}</h2>
      <div class="header-actions">
        <router-link to="/vendors" class="btn">{{ t('withholding.manageVendors') }}</router-link>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Period Selector -->
    <div class="control-panel">
      <div class="control-row">
        <label>{{ t('withholding.period') }}</label>
        <select v-model="selectedPeriod" @change="loadData">
          <option v-for="p in periodOptions" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="control-actions">
        <button class="btn" @click="handleDownloadSawt('csv')">{{ isSG ? t('withholding.downloadWhtCsv') : t('withholding.downloadSawtCsv') }}</button>
        <button class="btn" @click="handleDownloadSawt('pdf')">{{ isSG ? t('withholding.downloadWhtPdf') : t('withholding.downloadSawtPdf') }}</button>
      </div>
    </div>

    <!-- EWT/WHT Summary Cards -->
    <EwtSummaryCards v-if="store.ewtSummary" :summary="store.ewtSummary" :jurisdiction="auth.jurisdiction" />

    <div v-if="!store.ewtSummary && !store.loading" class="empty-state">
      <p>{{ t('withholding.noData') }}</p>
      <p class="hint">
        {{ isSG ? t('withholding.hintSG') : t('withholding.hintPH') }}
      </p>
    </div>

    <!-- Certificates -->
    <div class="section" v-if="store.certificates.length > 0">
      <h3>{{ isSG ? t('withholding.certTitleSG') : t('withholding.certTitlePH') }}</h3>
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
  background: var(--bg-surface-alt);
  border: 1px solid var(--border-default);
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
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
}
.control-actions { display: flex; gap: 8px; }

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
}
.empty-state p { margin: 0 0 8px; color: var(--text-primary); }
.empty-state .hint { color: var(--text-muted); font-size: 14px; }

.section {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}
.section h3 { margin: 0 0 16px; font-size: 16px; }

.btn {
  padding: 8px 20px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  color: inherit;
}
.btn:hover { background: var(--bg-surface-hover); }

@media (max-width: 768px) {
  .withholding-view { max-width: 100%; }
  .view-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .control-panel { flex-direction: column; align-items: stretch; }
  .control-actions { flex-direction: column; }
  .control-actions .btn { width: 100%; text-align: center; }
  .section { padding: 16px; }
}
</style>
