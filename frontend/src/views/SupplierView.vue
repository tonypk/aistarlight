<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWithholdingStore } from '../stores/withholding'
import { useAuthStore } from '../stores/auth'
import SupplierTable from '../components/supplier/SupplierTable.vue'
import SupplierForm from '../components/supplier/SupplierForm.vue'
import type { Supplier, SupplierCreateData } from '../types/withholding'

const store = useWithholdingStore()
const auth = useAuthStore()
const isSG = computed(() => auth.jurisdiction === 'SG')
const showForm = ref(false)
const editingSupplier = ref<Supplier | null>(null)
const searchQuery = ref('')
const error = ref('')

onMounted(() => {
  store.fetchSuppliers()
})

function openCreate() {
  editingSupplier.value = null
  showForm.value = true
}

function openEdit(supplier: Supplier) {
  editingSupplier.value = supplier
  showForm.value = true
}

async function handleSubmit(data: SupplierCreateData) {
  error.value = ''
  try {
    if (editingSupplier.value) {
      await store.updateSupplier(editingSupplier.value.id, data)
    } else {
      await store.createSupplier(data)
    }
    showForm.value = false
    editingSupplier.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Operation failed'
  }
}

async function handleDelete(id: string) {
  if (!confirm('Delete this supplier?')) return
  try {
    await store.deleteSupplier(id)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Delete failed'
  }
}

async function handleSearch() {
  await store.fetchSuppliers(1, 50, searchQuery.value || undefined)
}
</script>

<template>
  <div class="supplier-view">
    <div class="view-header">
      <h2>Supplier Management</h2>
      <button class="btn primary" @click="openCreate">Add Supplier</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="search-bar">
      <input
        v-model="searchQuery"
        :placeholder="isSG ? 'Search by name or UEN...' : 'Search by name or TIN...'"
        @keyup.enter="handleSearch"
      />
      <button class="btn" @click="handleSearch">Search</button>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editingSupplier ? 'Edit Supplier' : 'New Supplier' }}</h3>
        <SupplierForm
          :supplier="editingSupplier"
          :jurisdiction="auth.jurisdiction"
          @submit="handleSubmit"
          @cancel="showForm = false"
        />
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">Loading suppliers...</div>
    <SupplierTable
      v-else
      :suppliers="store.suppliers"
      :jurisdiction="auth.jurisdiction"
      @edit="openEdit"
      @delete="handleDelete"
    />
  </div>
</template>

<style scoped>
.supplier-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.view-header h2 { margin: 0; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }
.loading-msg { color: #6b7280; text-align: center; padding: 40px 0; }

.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.search-bar input {
  flex: 1;
  max-width: 400px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn:hover { background: #f3f4f6; }
.btn.primary { background: #4f46e5; color: #fff; border-color: #4f46e5; }
.btn.primary:hover { background: #4338ca; }

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
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 20px; }
</style>
