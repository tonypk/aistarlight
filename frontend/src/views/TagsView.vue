<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTagStore } from '../stores/tags'
import type { Tag, CreateTagData } from '../api/tags'

const store = useTagStore()
const showForm = ref(false)
const editingTag = ref<Tag | null>(null)
const searchQuery = ref('')
const error = ref('')

// Form fields
const formName = ref('')
const formColor = ref('#4f46e5')

const presetColors = [
  '#4f46e5', '#7c3aed', '#db2777', '#dc2626',
  '#ea580c', '#d97706', '#16a34a', '#0891b2',
  '#2563eb', '#4b5563',
]

onMounted(() => {
  store.fetchTags()
})

function openCreate() {
  editingTag.value = null
  formName.value = ''
  formColor.value = '#4f46e5'
  showForm.value = true
}

function openEdit(tag: Tag) {
  editingTag.value = tag
  formName.value = tag.name
  formColor.value = tag.color
  showForm.value = true
}

async function handleSubmit() {
  error.value = ''
  const data: CreateTagData = {
    name: formName.value.trim(),
    color: formColor.value,
  }
  if (!data.name) {
    error.value = 'Tag name is required'
    return
  }
  try {
    if (editingTag.value) {
      await store.updateTag(editingTag.value.id, data)
    } else {
      await store.createTag(data)
    }
    showForm.value = false
    editingTag.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Operation failed'
  }
}

async function handleDelete(tag: Tag) {
  if (!confirm(`Delete tag "${tag.name}"?`)) return
  try {
    await store.deleteTag(tag.id)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'Delete failed'
  }
}

async function handleSearch() {
  await store.fetchTags(1, 50, searchQuery.value || undefined)
}
</script>

<template>
  <div class="tags-view">
    <div class="view-header">
      <h2>Tag Management</h2>
      <button class="btn primary" @click="openCreate">Add Tag</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="search-bar">
      <input
        v-model="searchQuery"
        placeholder="Search tags..."
        @keyup.enter="handleSearch"
      />
      <button class="btn" @click="handleSearch">Search</button>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editingTag ? 'Edit Tag' : 'New Tag' }}</h3>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>Name</label>
            <input v-model="formName" placeholder="Tag name..." required />
          </div>
          <div class="form-group">
            <label>Color</label>
            <div class="color-picker">
              <div class="color-presets">
                <button
                  v-for="c in presetColors"
                  :key="c"
                  type="button"
                  class="color-swatch"
                  :class="{ selected: formColor === c }"
                  :style="{ background: c }"
                  @click="formColor = c"
                />
              </div>
              <input type="color" v-model="formColor" class="color-input" />
            </div>
          </div>
          <div class="preview-group">
            <label>Preview</label>
            <span class="tag-chip" :style="{ background: formColor + '20', color: formColor, borderColor: formColor }">
              {{ formName || 'Tag name' }}
            </span>
          </div>
          <div class="form-actions">
            <button type="button" class="btn" @click="showForm = false">Cancel</button>
            <button type="submit" class="btn primary">{{ editingTag ? 'Update' : 'Create' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">Loading tags...</div>

    <div v-else-if="store.tags.length === 0" class="empty">
      No tags yet. Create one to get started.
    </div>

    <div v-else class="tags-grid">
      <div v-for="tag in store.tags" :key="tag.id" class="tag-card">
        <div class="tag-card-header">
          <span class="tag-chip" :style="{ background: tag.color + '20', color: tag.color, borderColor: tag.color }">
            {{ tag.name }}
          </span>
        </div>
        <div class="tag-card-actions">
          <button class="btn-sm" @click="openEdit(tag)">Edit</button>
          <button class="btn-sm danger" @click="handleDelete(tag)">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tags-view { max-width: 1200px; }
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.view-header h2 { margin: 0; }
.error { color: #ef4444; margin-bottom: 12px; font-size: 14px; }
.loading-msg { color: #6b7280; text-align: center; padding: 40px 0; }
.empty { color: #9ca3af; text-align: center; padding: 40px 0; }

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
  width: 440px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h3 { margin: 0 0 20px; }

.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}
.form-group input[type="text"],
.form-group input:not([type]) {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.color-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}
.color-presets {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
}
.color-swatch.selected {
  border-color: #1f2937;
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #1f2937;
}
.color-input {
  width: 36px;
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  padding: 2px;
}

.preview-group {
  margin-bottom: 20px;
}
.preview-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.tag-chip {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.tag-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tag-card-header {
  display: flex;
  align-items: center;
}
.tag-card-actions {
  display: flex;
  gap: 6px;
}
.btn-sm {
  padding: 4px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}
.btn-sm:hover { background: #f3f4f6; }
.btn-sm.danger { color: #dc2626; border-color: #fca5a5; }
.btn-sm.danger:hover { background: #fef2f2; }
</style>
