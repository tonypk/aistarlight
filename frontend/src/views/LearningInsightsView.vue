<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { correctionsApi } from '@/api/corrections'
import type { CorrectionRule, CorrectionStats } from '@/types/correction'

const { t } = useI18n()

const stats = ref<{ total_corrections: number; total_rules: number; active_rules: number; correction_stats: any[] } | null>(null)
const correctionStats = ref<CorrectionStats | null>(null)
const rules = ref<CorrectionRule[]>([])
const candidates = ref<any[]>([])
const loading = ref(false)
const analyzing = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const [statsRes, corrStatsRes, rulesRes] = await Promise.all([
      correctionsApi.learningStats(),
      correctionsApi.stats(),
      correctionsApi.rules(),
    ])
    stats.value = statsRes.data.data
    correctionStats.value = corrStatsRes.data.data
    rules.value = rulesRes.data.data || []
  } catch {
    error.value = t('learning.loadFailed')
  } finally {
    loading.value = false
  }
})

async function handleAnalyze() {
  analyzing.value = true
  error.value = ''
  try {
    const res = await correctionsApi.analyze()
    candidates.value = res.data.data || []
    // Refresh rules
    const rulesRes = await correctionsApi.rules()
    rules.value = rulesRes.data.data || []
    // Refresh stats
    const statsRes = await correctionsApi.learningStats()
    stats.value = statsRes.data.data
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || t('learning.analysisFailed')
  } finally {
    analyzing.value = false
  }
}

async function toggleRule(rule: CorrectionRule) {
  try {
    await correctionsApi.updateRule(rule.id, { is_active: !rule.is_active })
    rule.is_active = !rule.is_active
  } catch {
    error.value = t('learning.updateFailed')
  }
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return '#22c55e'
  if (confidence >= 0.75) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <div class="learning-view">
    <div class="header-row">
      <h2>{{ t('learning.title') }}</h2>
      <button class="analyze-btn" @click="handleAnalyze" :disabled="analyzing">
        {{ analyzing ? t('learning.analyzing') : t('learning.runAnalysis') }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="loading" class="loading">{{ t('learning.loading') }}</div>

    <template v-if="!loading && stats">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_corrections }}</div>
          <div class="stat-label">{{ t('learning.totalCorrections') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_rules }}</div>
          <div class="stat-label">{{ t('learning.learnedRules') }}</div>
        </div>
        <div class="stat-card active">
          <div class="stat-value">{{ stats.active_rules }}</div>
          <div class="stat-label">{{ t('learning.activeRules') }}</div>
        </div>
      </div>

      <!-- Correction Frequency -->
      <div class="card" v-if="correctionStats && correctionStats.by_field.length">
        <h3>{{ t('learning.topPatterns') }}</h3>
        <table>
          <thead>
            <tr>
              <th>{{ t('learning.thField') }}</th>
              <th>{{ t('learning.thCorrectedTo') }}</th>
              <th>{{ t('learning.thEntityType') }}</th>
              <th>{{ t('learning.thCount') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in correctionStats.by_field.slice(0, 15)" :key="idx">
              <td class="field-name">{{ item.field_name }}</td>
              <td class="new-val">{{ item.new_value }}</td>
              <td>{{ item.entity_type }}</td>
              <td class="count">{{ item.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Learned Rules -->
      <div class="card">
        <h3>{{ t('learning.learnedRulesSection') }}</h3>
        <div v-if="rules.length === 0" class="empty">
          {{ t('learning.noRules') }}
        </div>
        <div v-for="rule in rules" :key="rule.id" class="rule-card" :class="{ inactive: !rule.is_active }">
          <div class="rule-header">
            <span class="rule-type">{{ rule.rule_type }}</span>
            <span class="confidence" :style="{ color: confidenceColor(rule.confidence) }">
              {{ (rule.confidence * 100).toFixed(0) }}%
            </span>
            <button class="toggle-btn" @click="toggleRule(rule)">
              {{ rule.is_active ? t('learning.deactivate') : t('learning.activate') }}
            </button>
          </div>
          <div class="rule-body">
            <div class="rule-criteria">
              {{ t('learning.matchLabel') }} <code>{{ JSON.stringify(rule.match_criteria) }}</code>
            </div>
            <div class="rule-action">
              {{ t('learning.setLabel') }} <strong>{{ rule.correction_field }}</strong> = <strong>{{ rule.correction_value }}</strong>
            </div>
            <div class="rule-meta">
              {{ t('learning.basedOn', { count: rule.source_correction_count }) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Analysis Candidates (if just analyzed) -->
      <div class="card" v-if="candidates.length > 0">
        <h3>{{ t('learning.candidateTitle') }}</h3>
        <div v-for="(cand, idx) in candidates" :key="idx" class="candidate-card">
          <div class="rule-header">
            <span class="rule-type">{{ cand.rule_type }}</span>
            <span class="confidence" :style="{ color: confidenceColor(cand.confidence) }">
              {{ (cand.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="rule-body">
            <div class="rule-action">
              {{ t('learning.setLabel') }} <strong>{{ cand.correction_field }}</strong> = <strong>{{ cand.correction_value }}</strong>
            </div>
            <div class="rule-meta">
              {{ t('learning.matchingCorrections', { count: cand.source_correction_count }) }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.learning-view { max-width: 1000px; }
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.analyze-btn {
  padding: 10px 20px;
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}
.analyze-btn:hover { background: var(--brand-primary-hover); }
.analyze-btn:disabled { opacity: 0.5; }
.error { color: #ef4444; margin-bottom: 12px; }
.loading { color: var(--text-muted); }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}
.stat-card.active {
  border-color: var(--brand-primary);
  background: var(--bg-accent, #f0f4ff);
}
.stat-value { font-size: 36px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}
.card h3 { margin: 0 0 16px; font-size: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 8px; color: var(--text-secondary); font-size: 12px; border-bottom: 1px solid var(--border-default); }
td { padding: 8px; border-bottom: 1px solid #f3f4f6; }
.field-name { font-family: monospace; color: var(--brand-primary); }
.new-val { color: #22c55e; font-weight: 500; }
.count { font-weight: 600; }
.empty { color: var(--text-muted); font-size: 14px; padding: 20px 0; }
.rule-card {
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 10px;
}
.rule-card.inactive { opacity: 0.5; background: var(--bg-surface-alt); }
.candidate-card {
  border: 1px dashed #c7d2fe;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 10px;
  background: var(--bg-accent, #f0f4ff);
}
.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.rule-type {
  padding: 2px 8px;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.confidence { font-weight: 700; font-size: 14px; }
.toggle-btn {
  margin-left: auto;
  padding: 4px 10px;
  border: 1px solid var(--border-input);
  background: var(--bg-surface);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.toggle-btn:hover { background: var(--bg-surface-hover); }
.rule-body { font-size: 13px; }
.rule-criteria { color: var(--text-secondary); margin-bottom: 4px; }
.rule-criteria code {
  background: var(--bg-surface-hover);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 11px;
}
.rule-action { margin-bottom: 4px; }
.rule-meta { color: var(--text-muted); font-size: 12px; }
</style>
