<script setup lang="ts">
import { ref, computed } from 'vue'
import { client } from '../api/client'
import { useAuthStore } from '../stores/auth'

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
    monthly: 'Monthly',
    quarterly: 'Quarterly',
    annual: 'Annual',
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
    <h2>Form Router</h2>
    <p class="subtitle">Find out which {{ isSG ? 'IRAS' : 'BIR' }} forms your company needs to file</p>

    <div class="profile-form">
      <div class="field">
        <label>
          <input type="checkbox" v-model="vatRegistered" />
          {{ isSG ? 'GST Registered' : 'VAT Registered' }}
        </label>
      </div>
      <div class="field">
        <label>
          <input type="checkbox" v-model="hasEmployees" />
          Has Employees
        </label>
      </div>
      <div class="field">
        <label>Entity Type</label>
        <select v-model="entityType">
          <option value="corporation">Corporation</option>
          <option value="individual">Individual / Sole Proprietor</option>
        </select>
      </div>
      <button class="recommend-btn" :disabled="loading" @click="getRecommendations">
        {{ loading ? 'Loading...' : 'Get Recommendations' }}
      </button>
    </div>

    <div v-if="hasSearched && recommendations.length" class="results">
      <h3>Required Forms ({{ recommendations.filter(r => r.required).length }} required, {{ recommendations.filter(r => !r.required).length }} optional)</h3>
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
            Deadline: {{ rec.deadline_day }}th of following month
          </div>
          <span v-if="!rec.required" class="optional-badge">Optional</span>
        </div>
      </div>
    </div>

    <div v-if="hasSearched && !recommendations.length && !loading" class="no-results">
      No form recommendations found.
    </div>
  </div>
</template>

<style scoped>
.form-router { max-width: 900px; }
.form-router h2 { margin-bottom: 4px; }
.subtitle { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
.profile-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 24px;
  padding: 20px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
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
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.recommend-btn {
  padding: 10px 24px;
  background: #4f46e5;
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
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
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
.form-type { font-weight: 700; font-size: 15px; color: #1e293b; }
.freq-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.freq-monthly { background: #dbeafe; color: #1e40af; }
.freq-quarterly { background: #fef3c7; color: #92400e; }
.freq-annual { background: #d1fae5; color: #065f46; }
.card-name { font-size: 13px; color: #374151; margin-bottom: 6px; }
.card-reason { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.card-deadline { font-size: 12px; color: #4338ca; margin-top: 6px; }
.optional-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  background: #f3f4f6;
  color: #6b7280;
  padding: 1px 6px;
  border-radius: 4px;
}
.no-results { color: #6b7280; font-style: italic; }
</style>
