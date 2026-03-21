<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useVendorPolicyStore } from '../stores/vendorPolicies'
import type { VendorPolicy } from '../api/vendorPolicies'

const { t } = useI18n()

const store = useVendorPolicyStore()
const showForm = ref(false)
const editingPolicy = ref<VendorPolicy | null>(null)
const error = ref('')

// Form fields
const formCategory = ref('')
const formAccountCode = ref('')
const formTaxCode = ref('')
const formDepartment = ref('')
const formProject = ref('')

onMounted(() => {
  store.fetchPolicies()
  store.fetchSuggestions()
})

function openEdit(policy: VendorPolicy) {
  editingPolicy.value = policy
  formCategory.value = policy.default_category
  formAccountCode.value = policy.account_code
  formTaxCode.value = policy.tax_code
  formDepartment.value = policy.department
  formProject.value = policy.project
  showForm.value = true
}

async function handleSubmit() {
  if (!editingPolicy.value) return
  error.value = ''
  try {
    await store.updatePolicy(editingPolicy.value.id, {
      category: formCategory.value,
      account_code: formAccountCode.value,
      tax_code: formTaxCode.value,
      department: formDepartment.value,
      project: formProject.value,
    })
    showForm.value = false
    editingPolicy.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('vendorPolicies.updateFailed')
  }
}

async function handleDelete(policy: VendorPolicy) {
  if (!confirm(t('vendorPolicies.deleteConfirm', { vendor: policy.vendor_normalized }))) return
  try {
    await store.deletePolicy(policy.id)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('vendorPolicies.deleteFailed')
  }
}

async function handlePromote(policy: VendorPolicy) {
  try {
    await store.promoteRule(policy.id)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('vendorPolicies.promoteFailed')
  }
}

function confidenceColor(score: number): string {
  if (score >= 0.9) return '#16a34a'
  if (score >= 0.75) return '#d97706'
  return '#dc2626'
}

function confidenceLabel(score: number): string {
  return (score * 100).toFixed(0) + '%'
}
</script>

<template>
  <div class="vendor-policies-view">
    <div class="view-header">
      <div>
        <h2>{{ t('vendorPolicies.title') }}</h2>
        <p class="subtitle">{{ t('vendorPolicies.subtitle') }}</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Rule Suggestions -->
    <div v-if="store.suggestions.length > 0" class="suggestions-section">
      <h3>{{ t('vendorPolicies.ruleSuggestions') }}</h3>
      <p class="section-desc">{{ t('vendorPolicies.suggestionsDesc') }}</p>
      <div class="suggestion-cards">
        <div v-for="s in store.suggestions" :key="s.vendor_normalized" class="suggestion-card">
          <div class="suggestion-info">
            <strong>{{ s.vendor_normalized }}</strong>
            <span class="suggestion-detail">{{ s.message }}</span>
          </div>
          <div class="suggestion-stats">
            <span class="stat">{{ t('vendorPolicies.corrections', { count: s.correction_count }) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ t('vendorPolicies.editDefaults', { vendor: editingPolicy?.vendor_normalized }) }}</h3>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>{{ t('vendorPolicies.category') }}</label>
            <input v-model="formCategory" :placeholder="t('vendorPolicies.categoryPlaceholder')" />
          </div>
          <div class="form-group">
            <label>{{ t('vendorPolicies.accountCode') }}</label>
            <input v-model="formAccountCode" :placeholder="t('vendorPolicies.accountCodePlaceholder')" />
          </div>
          <div class="form-group">
            <label>{{ t('vendorPolicies.taxCode') }}</label>
            <input v-model="formTaxCode" :placeholder="t('vendorPolicies.taxCodePlaceholder')" />
          </div>
          <div class="form-group">
            <label>{{ t('vendorPolicies.department') }}</label>
            <input v-model="formDepartment" :placeholder="t('vendorPolicies.departmentPlaceholder')" />
          </div>
          <div class="form-group">
            <label>{{ t('vendorPolicies.project') }}</label>
            <input v-model="formProject" :placeholder="t('vendorPolicies.projectPlaceholder')" />
          </div>
          <div class="form-actions">
            <button type="button" class="btn" @click="showForm = false">{{ t('vendorPolicies.cancel') }}</button>
            <button type="submit" class="btn primary">{{ t('vendorPolicies.save') }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">{{ t('vendorPolicies.loading') }}</div>
    <div v-else-if="store.policies.length === 0" class="empty">
      {{ t('vendorPolicies.empty') }}
    </div>

    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>{{ t('vendorPolicies.thVendor') }}</th>
            <th>{{ t('vendorPolicies.thAliases') }}</th>
            <th>{{ t('vendorPolicies.thCategory') }}</th>
            <th>{{ t('vendorPolicies.thAccount') }}</th>
            <th>{{ t('vendorPolicies.thTaxCode') }}</th>
            <th class="text-center">{{ t('vendorPolicies.thUsed') }}</th>
            <th class="text-center">{{ t('vendorPolicies.thConfidence') }}</th>
            <th>{{ t('vendorPolicies.thActions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in store.policies" :key="p.id">
            <td class="vendor-name">{{ p.vendor_normalized }}</td>
            <td class="aliases-cell">
              <span v-for="a in (p.aliases || []).slice(0, 3)" :key="a" class="alias-chip">{{ a }}</span>
              <span v-if="(p.aliases || []).length > 3" class="text-muted">+{{ p.aliases.length - 3 }}</span>
            </td>
            <td>{{ p.default_category || '-' }}</td>
            <td>{{ p.account_code || '-' }}</td>
            <td>{{ p.tax_code || '-' }}</td>
            <td class="text-center">{{ p.usage_count }}</td>
            <td class="text-center">
              <span class="confidence-badge" :style="{ color: confidenceColor(p.confidence_score) }">
                {{ confidenceLabel(p.confidence_score) }}
              </span>
            </td>
            <td>
              <div class="action-btns">
                <button class="btn-sm" @click="openEdit(p)">{{ t('vendorPolicies.edit') }}</button>
                <button v-if="p.confidence_score < 0.7 && p.correction_count >= 5" class="btn-sm promote" @click="handlePromote(p)">{{ t('vendorPolicies.promote') }}</button>
                <button class="btn-sm danger" @click="handleDelete(p)">{{ t('vendorPolicies.delete') }}</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.vendor-policies-view { max-width: 1400px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.view-header h2 { margin: 0; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }
.loading-msg { color: var(--text-secondary); text-align: center; padding: 40px 0; }
.empty { color: var(--text-muted); text-align: center; padding: 40px 0; }

.suggestions-section {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.suggestions-section h3 { margin: 0 0 4px; font-size: 15px; color: #92400e; }
.section-desc { color: #a16207; font-size: 13px; margin-bottom: 12px; }
.suggestion-cards { display: flex; flex-direction: column; gap: 8px; }
.suggestion-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-surface);
  border-radius: 6px;
  border: 1px solid #fde68a;
}
.suggestion-info strong { font-size: 14px; }
.suggestion-detail { display: block; font-size: 12px; color: var(--text-secondary); }
.suggestion-stats .stat { font-size: 12px; color: #92400e; }

.table-container {
  overflow-x: auto;
  border: 1px solid var(--border-default);
  border-radius: 8px;
}
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead { background: var(--bg-surface-alt); }
th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-default);
  white-space: nowrap;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: var(--text-primary);
}
tbody tr:hover { background: var(--bg-surface-alt); }
.text-center { text-align: center; }
.text-muted { color: var(--text-muted); font-size: 12px; }

.vendor-name { font-weight: 500; }
.aliases-cell { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.alias-chip {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  background: var(--bg-surface-hover);
  color: var(--text-secondary);
}

.confidence-badge { font-weight: 600; font-size: 13px; }

.action-btns { display: flex; gap: 4px; }
.btn-sm {
  padding: 4px 10px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 12px;
}
.btn-sm:hover { background: var(--bg-surface-hover); }
.btn-sm.danger { color: #dc2626; border-color: #fca5a5; }
.btn-sm.danger:hover { background: #fef2f2; }
.btn-sm.promote { color: #16a34a; border-color: #86efac; }
.btn-sm.promote:hover { background: #f0fdf4; }

.btn {
  padding: 8px 20px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 14px;
}
.btn:hover { background: var(--bg-surface-hover); }
.btn.primary { background: var(--brand-primary); color: #fff; border-color: var(--brand-primary); }
.btn.primary:hover { background: var(--brand-primary-hover); }

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  background: var(--bg-surface); border-radius: 16px;
  padding: 32px; width: 480px;
  max-width: 90vw; max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 20px; font-size: 16px; }

.form-group { margin-bottom: 14px; }
.form-group label {
  display: block; margin-bottom: 4px;
  font-size: 13px; font-weight: 500; color: var(--text-primary);
}
.form-group input {
  width: 100%; padding: 8px 12px;
  border: 1px solid var(--border-input); border-radius: 6px;
  font-size: 14px; box-sizing: border-box;
}
.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }
</style>
