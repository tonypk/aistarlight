<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { client } from '../api/client'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()

const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')

interface FormRec {
  form_type: string
  name: string
  frequency: string
  required: boolean
  reason: string
  deadline_day?: number
}

const vatRegistered = ref(true)
const hasEmployees = ref(true)
const entityType = ref('corporation')
const recommendations = ref<FormRec[]>([])
const loading = ref(false)
const hasSearched = ref(false)

async function getRecommendations() {
  loading.value = true
  hasSearched.value = true
  try {
    const res = await client.get('/forms/recommended', {
      params: {
        vat: vatRegistered.value,
        has_employees: hasEmployees.value,
        entity_type: entityType.value,
      },
    })
    recommendations.value = res.data.data || []
  } catch {
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

function freqLabel(freq: string): string {
  const map: Record<string, string> = {
    monthly: t('formRouter.monthly'),
    quarterly: t('formRouter.quarterly'),
    annual: t('formRouter.annual'),
  }
  return map[freq] || freq
}

function freqClass(freq: string): string {
  const map: Record<string, string> = {
    monthly: 'freq-monthly',
    quarterly: 'freq-quarterly',
    annual: 'freq-annual',
  }
  return map[freq] || ''
}
</script>

<template>
  <div class="form-router">
    <h2>{{ t('formRouter.title') }}</h2>
    <p class="subtitle">{{ t('formRouter.subtitle', { authority: isSG ? 'IRAS' : 'BIR' }) }}</p>

    <div class="profile-form">
      <div class="field">
        <label>
          <input type="checkbox" v-model="vatRegistered" />
          {{ isSG ? t('formRouter.gstRegistered') : t('formRouter.vatRegistered') }}
        </label>
      </div>
      <div class="field">
        <label>
          <input type="checkbox" v-model="hasEmployees" />
          {{ t('formRouter.hasEmployees') }}
        </label>
      </div>
      <div class="field">
        <label>{{ t('formRouter.entityType') }}</label>
        <select v-model="entityType">
          <option value="corporation">{{ t('formRouter.corporation') }}</option>
          <option value="individual">{{ t('formRouter.individual') }}</option>
        </select>
      </div>
      <button class="recommend-btn" :disabled="loading" @click="getRecommendations">
        {{ loading ? t('formRouter.loading') : t('formRouter.getRecommendations') }}
      </button>
    </div>

    <div v-if="hasSearched && recommendations.length" class="results">
      <h3>{{ t('formRouter.requiredForms', { required: recommendations.filter(r => r.required).length, optional: recommendations.filter(r => !r.required).length }) }}</h3>
      <div class="form-cards">
        <div
          v-for="rec in recommendations"
          :key="rec.form_type"
          class="form-card"
          :class="{ optional: !rec.required }"
        >
          <div class="card-header">
            <span class="form-type">{{ rec.form_type.replace('_', ' ') }}</span>
            <span class="freq-badge" :class="freqClass(rec.frequency)">{{ freqLabel(rec.frequency) }}</span>
          </div>
          <div class="card-name">{{ rec.name }}</div>
          <div class="card-reason">{{ rec.reason }}</div>
          <div v-if="rec.deadline_day" class="card-deadline">
            {{ t('formRouter.deadline', { day: rec.deadline_day }) }}
          </div>
          <span v-if="!rec.required" class="optional-badge">{{ t('formRouter.optional') }}</span>
        </div>
      </div>
    </div>

    <div v-if="hasSearched && !recommendations.length && !loading" class="no-results">
      {{ t('formRouter.noResults') }}
    </div>
  </div>
</template>

<style scoped>
.form-router { max-width: 900px; }
.form-router h2 { margin-bottom: 4px; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-bottom: 24px; }
.profile-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--bg-surface-alt);
  border: 1px solid var(--border-default);
  border-radius: 12px;
}
.field label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.field select {
  display: block;
  margin-top: 4px;
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
}
.recommend-btn {
  padding: 10px 24px;
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.recommend-btn:disabled { opacity: 0.6; }
.results h3 { margin-bottom: 16px; font-size: 16px; }
.form-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.form-card {
  position: relative;
  padding: 16px;
  border: 1px solid var(--border-input);
  border-radius: 10px;
  background: var(--bg-surface);
}
.form-card.optional {
  border-style: dashed;
  opacity: 0.85;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.form-type { font-weight: 700; font-size: 15px; color: var(--text-primary); }
.freq-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.freq-monthly { background: #dbeafe; color: #1e40af; }
.freq-quarterly { background: #fef3c7; color: #92400e; }
.freq-annual { background: #d1fae5; color: #065f46; }
.card-name { font-size: 13px; color: var(--text-primary); margin-bottom: 6px; }
.card-reason { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.card-deadline { font-size: 12px; color: var(--brand-primary-hover); margin-top: 6px; }
.optional-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  background: var(--bg-surface-hover);
  color: var(--text-secondary);
  padding: 1px 6px;
  border-radius: 4px;
}
.no-results { color: var(--text-secondary); font-style: italic; }
</style>
