<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWithholdingStore } from '../stores/withholding'
import { useAuthStore } from '../stores/auth'
import VendorTable from '../components/vendor/VendorTable.vue'
import VendorForm from '../components/vendor/VendorForm.vue'
import type { Vendor, VendorCreateData } from '../types/withholding'

const { t } = useI18n()
const store = useWithholdingStore()
const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')
const showForm = ref(false)
const editingVendor = ref<Vendor | null>(null)
const searchQuery = ref('')
const error = ref('')

onMounted(() => {
  store.fetchVendors()
})

function openCreate() {
  editingVendor.value = null
  showForm.value = true
}

function openEdit(vendor: Vendor) {
  editingVendor.value = vendor
  showForm.value = true
}

async function handleSubmit(data: VendorCreateData) {
  error.value = ''
  try {
    if (editingVendor.value) {
      await store.updateVendor(editingVendor.value.id, data)
    } else {
      await store.createVendor(data)
    }
    showForm.value = false
    editingVendor.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Operation failed'
  }
}

async function handleDelete(id: string) {
  if (!confirm(t('vendor.deleteConfirm'))) return
  try {
    await store.deleteVendor(id)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Delete failed'
  }
}

async function handleSearch() {
  await store.fetchVendors(1, 50, searchQuery.value || undefined)
}
</script>

<template>
  <div class="vendor-view">
    <div class="view-header">
      <h2>{{ t('vendor.title') }}</h2>
      <button class="btn primary" @click="openCreate">{{ t('vendor.addVendor') }}</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="search-bar">
      <input
        v-model="searchQuery"
        :placeholder="isSG ? t('vendor.searchPlaceholderSG') : t('vendor.searchPlaceholderPH')"
        @keyup.enter="handleSearch"
      />
      <button class="btn" @click="handleSearch">Search</button>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editingVendor ? t('vendor.editVendor') : t('vendor.newVendor') }}</h3>
        <VendorForm
          :vendor="editingVendor"
          :jurisdiction="auth.jurisdiction"
          @submit="handleSubmit"
          @cancel="showForm = false"
        />
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">{{ t('vendor.loadingMsg') }}</div>
    <VendorTable
      v-else
      :vendors="store.vendors"
      :jurisdiction="auth.jurisdiction"
      @edit="openEdit"
      @delete="handleDelete"
    />
  </div>
</template>

<style scoped>
.vendor-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.view-header h2 { margin: 0; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }
.loading-msg { color: var(--text-secondary); text-align: center; padding: 40px 0; }

.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.search-bar input {
  flex: 1;
  max-width: 400px;
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
}

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
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal {
  background: var(--bg-surface);
  border-radius: 16px;
  padding: 32px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 20px; }
</style>
