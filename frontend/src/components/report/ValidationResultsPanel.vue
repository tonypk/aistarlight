<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { complianceApi } from '@/api/compliance'
import type { CheckResult, ValidationResult } from '@/types/correction'

const props = defineProps<{
  reportId: string
}>()

const validation = ref<ValidationResult | null>(null)
const loading = ref(false)
const validating = ref(false)
const error = ref('')

onMounted(() => fetchValidation())

async function fetchValidation() {
  loading.value = true
  try {
    const res = await complianceApi.getValidation(props.reportId)
    validation.value = res.data.data
  } catch {
    // No validation yet — that's fine
  } finally {
    loading.value = false
  }
}

async function handleValidate() {
  validating.value = true
  error.value = ''
  try {
    const res = await complianceApi.validate(props.reportId)
    validation.value = res.data.data
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Validation failed'
  } finally {
    validating.value = false
  }
}

const groupedChecks = computed(() => {
  if (!validation.value) return {}
  const groups: Record<string, CheckResult[]> = {}
  for (const check of validation.value.check_results) {
    const sev = check.severity
    if (!groups[sev]) groups[sev] = []
    groups[sev].push(check)
  }
  return groups
})

const severityOrder = ['critical', 'high', 'medium', 'low']

function severityColor(sev: string): string {
  const colors: Record<string, string> = {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#d97706',
    low: '#6b7280',
  }
  return colors[sev] || '#6b7280'
}

function scoreClass(score: number): string {
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-warning'
  return 'score-danger'
}
</script>

<template>
  <div class="validation-panel">
    <div class="panel-header">
      <h4>Compliance Validation</h4>
      <button class="validate-btn" @click="handleValidate" :disabled="validating">
        {{ validating ? 'Validating...' : validation ? 'Re-Validate' : 'Run Validation' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Loading validation...</div>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="validation" class="results">
      <div class="score-display" :class="scoreClass(validation.overall_score)">
        <span class="score-number">{{ validation.overall_score }}</span>
        <span class="score-label">/100</span>
      </div>

      <!-- Rule check results grouped by severity -->
      <div v-for="sev in severityOrder" :key="sev">
        <div v-if="groupedChecks[sev]?.length" class="severity-group">
          <div class="severity-header" :style="{ color: severityColor(sev) }">
            {{ sev.toUpperCase() }} ({{ groupedChecks[sev].length }})
          </div>
          <div
            v-for="check in groupedChecks[sev]"
            :key="check.check_id"
            class="check-item"
            :class="{ passed: check.passed, failed: !check.passed }"
          >
            <span class="check-icon">{{ check.passed ? '&#10003;' : '&#10007;' }}</span>
            <span class="check-name">{{ check.check_name }}</span>
            <span class="check-msg">{{ check.message }}</span>
          </div>
        </div>
      </div>

      <!-- RAG findings -->
      <div v-if="validation.rag_findings?.length" class="rag-section">
        <div class="severity-header" style="color: #7c3aed">
          AI FINDINGS ({{ validation.rag_findings.length }})
        </div>
        <div
          v-for="(finding, idx) in validation.rag_findings"
          :key="idx"
          class="check-item failed"
        >
          <span class="check-icon" :style="{ color: severityColor(finding.severity) }">&#9888;</span>
          <span class="check-name">{{ finding.finding }}</span>
          <span class="reg-ref" v-if="finding.regulation_reference">
            {{ finding.regulation_reference }}
          </span>
        </div>
      </div>

      <div class="validated-at">
        Validated: {{ new Date(validation.validated_at).toLocaleString() }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.validation-panel {
  margin-top: 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.panel-header h4 {
  margin: 0;
  font-size: 15px;
}
.validate-btn {
  padding: 6px 14px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.validate-btn:hover { background: #4338ca; }
.validate-btn:disabled { opacity: 0.5; }
.loading { color: #9ca3af; font-size: 13px; }
.error { color: #ef4444; font-size: 13px; }
.results { margin-top: 8px; }
.score-display {
  text-align: center;
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 16px;
}
.score-number { font-size: 48px; font-weight: 700; }
.score-label { font-size: 20px; opacity: 0.7; }
.score-good { background: #d1fae5; color: #065f46; }
.score-warning { background: #fef3c7; color: #92400e; }
.score-danger { background: #fee2e2; color: #991b1b; }
.severity-group { margin-bottom: 12px; }
.severity-header {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 4px 0;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 4px;
}
.check-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  font-size: 13px;
  border-radius: 4px;
}
.check-item.passed { color: #065f46; }
.check-item.failed { color: #991b1b; background: #fef2f2; }
.check-icon { font-weight: 700; flex-shrink: 0; }
.check-name { font-weight: 500; min-width: 180px; }
.check-msg { color: #6b7280; flex: 1; }
.rag-section { margin-top: 12px; }
.reg-ref {
  font-size: 11px;
  color: #7c3aed;
  font-style: italic;
  margin-left: auto;
}
.validated-at {
  text-align: right;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 12px;
}
</style>
