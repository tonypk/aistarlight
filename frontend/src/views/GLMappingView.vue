<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { integrationApi, type GLMappingRule, type CreateGLMappingRequest } from '../api/integration'
import { useAccountingStore } from '../stores/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const { t } = useI18n()
const accountingStore = useAccountingStore()
const auth = useAuthStore()
const toast = useToastStore()

const mappings = ref<GLMappingRule[]>([])
const loading = ref(false)
const jurisdiction = ref(auth.jurisdiction || 'PH')
const showForm = ref(false)
const editingId = ref<string | null>(null)

const form = ref<CreateGLMappingRequest>({
  jurisdiction: jurisdiction.value,
  source_dimension: 'earning',
  source_value: '',
  target_account_id: '',
  debit_credit: 'debit',
  priority: 0,
})

const dimensions = ['earning', 'deduction', 'contribution', 'net_pay']

const dimensionLabels = computed<Record<string, string>>(() => ({
  earning: t('glMapping.earningDR'),
  deduction: t('glMapping.deductionCR'),
  contribution: t('glMapping.contributionDR'),
  net_pay: t('glMapping.netPayCR'),
}))

const grouped = computed(() => {
  const groups: Record<string, GLMappingRule[]> = {}
  for (const m of mappings.value) {
    const key = m.source_dimension
    if (!groups[key]) groups[key] = []
    groups[key].push(m)
  }
  return groups
})

async function fetchMappings() {
  loading.value = true
  try {
    const { data } = await integrationApi.listMappings(jurisdiction.value)
    mappings.value = data.data || []
  } catch (e) {
    toast.error(t('glMapping.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function seedDefaults() {
  try {
    const { data } = await integrationApi.seedDefaults(jurisdiction.value)
    toast.success(t('glMapping.seededSuccess', { accounts: data.data?.accounts_created || 0, mappings: data.data?.mappings_created || 0 }))
    await fetchMappings()
    await accountingStore.fetchAccounts()
  } catch (e) {
    toast.error(t('glMapping.seedFailed'))
  }
}

function openCreate() {
  editingId.value = null
  form.value = {
    jurisdiction: jurisdiction.value,
    source_dimension: 'earning',
    source_value: '',
    target_account_id: '',
    debit_credit: 'debit',
    priority: 0,
  }
  showForm.value = true
}

function openEdit(rule: GLMappingRule) {
  editingId.value = rule.id
  form.value = {
    jurisdiction: rule.jurisdiction,
    source_dimension: rule.source_dimension,
    source_value: rule.source_value,
    target_account_id: rule.target_account_id,
    debit_credit: rule.debit_credit,
    priority: rule.priority,
  }
  showForm.value = true
}

async function saveMapping() {
  try {
    if (editingId.value) {
      await integrationApi.updateMapping(editingId.value, {
        target_account_id: form.value.target_account_id,
        debit_credit: form.value.debit_credit,
        priority: form.value.priority,
      })
      toast.success(t('glMapping.mappingUpdated'))
    } else {
      await integrationApi.createMapping(form.value)
      toast.success(t('glMapping.mappingCreated'))
    }
    showForm.value = false
    await fetchMappings()
  } catch (e) {
    toast.error(t('glMapping.saveFailed'))
  }
}

async function deleteMapping(id: string) {
  if (!confirm(t('glMapping.deleteConfirm'))) return
  try {
    await integrationApi.deleteMapping(id)
    toast.success(t('glMapping.mappingDeleted'))
    await fetchMappings()
  } catch (e) {
    toast.error(t('glMapping.deleteFailed'))
  }
}

onMounted(() => {
  fetchMappings()
  accountingStore.fetchAccounts()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ t('glMapping.title') }}</h1>
      <div class="actions">
        <select v-model="jurisdiction" class="select" @change="fetchMappings()">
          <option value="PH">{{ t('glMapping.philippines') }}</option>
          <option value="LK">{{ t('glMapping.sriLanka') }}</option>
          <option value="SG">{{ t('glMapping.singapore') }}</option>
        </select>
        <button class="btn btn-secondary" @click="seedDefaults()">{{ t('glMapping.seedDefaults') }}</button>
        <button class="btn btn-primary" @click="openCreate()">{{ t('glMapping.addMapping') }}</button>
      </div>
    </div>

    <p class="description">
      {{ t('glMapping.desc') }}
    </p>

    <div v-if="loading" class="loading">{{ t('glMapping.loadingMappings') }}</div>

    <div v-else-if="mappings.length === 0" class="empty">
      <p>{{ t('glMapping.emptyState', { jurisdiction }) }}</p>
    </div>

    <div v-else class="mapping-groups">
      <div v-for="(rules, dim) in grouped" :key="dim" class="mapping-group">
        <h3 class="group-title">{{ dimensionLabels[dim] || dim }}</h3>
        <table class="table">
          <thead>
            <tr>
              <th>{{ t('glMapping.thSourceValue') }}</th>
              <th>{{ t('glMapping.thGlAccount') }}</th>
              <th>{{ t('glMapping.thDC') }}</th>
              <th>{{ t('glMapping.thPriority') }}</th>
              <th>{{ t('glMapping.thActive') }}</th>
              <th>{{ t('glMapping.thActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in rules" :key="rule.id">
              <td><code>{{ rule.source_value }}</code></td>
              <td>{{ rule.account_number }} - {{ rule.account_name }}</td>
              <td><span :class="['badge', rule.debit_credit === 'debit' ? 'badge-debit' : 'badge-credit']">{{ rule.debit_credit.toUpperCase() }}</span></td>
              <td>{{ rule.priority }}</td>
              <td><span :class="['badge', rule.is_active ? 'badge-active' : 'badge-inactive']">{{ rule.is_active ? t('glMapping.active') : t('glMapping.inactive') }}</span></td>
              <td>
                <button class="btn btn-sm btn-secondary" @click="openEdit(rule)">{{ t('common.edit') }}</button>
                <button class="btn btn-sm btn-danger" @click="deleteMapping(rule.id)">{{ t('common.delete') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h2>{{ editingId ? t('glMapping.editMapping') : t('glMapping.createMapping') }}</h2>
        <form @submit.prevent="saveMapping()">
          <div class="form-group" v-if="!editingId">
            <label>{{ t('glMapping.dimension') }}</label>
            <select v-model="form.source_dimension" class="select">
              <option v-for="d in dimensions" :key="d" :value="d">{{ dimensionLabels[d] || d }}</option>
            </select>
          </div>
          <div class="form-group" v-if="!editingId">
            <label>{{ t('glMapping.sourceValue') }}</label>
            <input v-model="form.source_value" class="input" :placeholder="t('glMapping.sourceValuePlaceholder')" required />
          </div>
          <div class="form-group">
            <label>{{ t('glMapping.glAccount') }}</label>
            <select v-model="form.target_account_id" class="select" required>
              <option value="">{{ t('glMapping.selectAccount') }}</option>
              <option v-for="acct in accountingStore.accounts" :key="acct.id" :value="acct.id">
                {{ acct.account_number }} - {{ acct.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ t('glMapping.debitCredit') }}</label>
            <select v-model="form.debit_credit" class="select">
              <option value="debit">{{ t('glMapping.debit') }}</option>
              <option value="credit">{{ t('glMapping.credit') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ t('glMapping.priority') }}</label>
            <input v-model.number="form.priority" type="number" class="input" />
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="showForm = false">{{ t('common.cancel') }}</button>
            <button type="submit" class="btn btn-primary">{{ editingId ? t('common.update') : t('common.create') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.page-header h1 { font-size: 1.5rem; margin: 0; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.description { color: var(--text-secondary, #6b7280); margin-bottom: 24px; font-size: 0.9rem; }
.loading { text-align: center; padding: 40px; color: var(--text-secondary); }
.empty { text-align: center; padding: 40px; color: var(--text-secondary); }

.mapping-group { margin-bottom: 32px; }
.group-title { font-size: 1.1rem; margin-bottom: 12px; color: var(--text-primary, #1f2937); border-bottom: 2px solid var(--border, #e5e7eb); padding-bottom: 8px; }

.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th { text-align: left; padding: 8px 12px; background: var(--bg-secondary, #f9fafb); border-bottom: 2px solid var(--border, #e5e7eb); font-weight: 600; }
.table td { padding: 8px 12px; border-bottom: 1px solid var(--border, #e5e7eb); }
.table code { background: var(--bg-tertiary, #f3f4f6); padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.badge-debit { background: #dbeafe; color: #1e40af; }
.badge-credit { background: #dcfce7; color: #166534; }
.badge-active { background: #dcfce7; color: #166534; }
.badge-inactive { background: #fee2e2; color: #991b1b; }

.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 500; }
.btn-primary { background: var(--primary, #3b82f6); color: white; }
.btn-secondary { background: var(--bg-secondary, #f3f4f6); color: var(--text-primary, #374151); border: 1px solid var(--border, #d1d5db); }
.btn-danger { background: #fee2e2; color: #991b1b; }
.btn-sm { padding: 4px 8px; font-size: 0.8rem; }

.select { padding: 8px 12px; border: 1px solid var(--border, #d1d5db); border-radius: 6px; background: var(--bg-surface); font-size: 0.875rem; }
.input { padding: 8px 12px; border: 1px solid var(--border, #d1d5db); border-radius: 6px; width: 100%; font-size: 0.875rem; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-surface); border-radius: 12px; padding: 24px; width: 480px; max-width: 95vw; max-height: 90vh; overflow-y: auto; }
.modal h2 { margin: 0 0 16px; font-size: 1.25rem; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 4px; font-weight: 500; font-size: 0.875rem; }
.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 24px; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .table { font-size: 0.8rem; }
  .table th, .table td { padding: 6px 8px; }
}
</style>
