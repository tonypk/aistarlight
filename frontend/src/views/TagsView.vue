<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTagStore } from '../stores/tags'
import type { Tag, CreateTagData } from '../api/tags'

const { t } = useI18n()
const store = useTagStore()
const showForm = ref(false)
const editingTag = ref<Tag | null>(null)
const searchQuery = ref('')
const error = ref('')

// Form fields
const formName = ref('')
const formColor = ref('var(--brand-primary)')
const formIsProject = ref(false)

const presetColors = [
  'var(--brand-primary)', '#7c3aed', '#db2777', '#dc2626',
  '#ea580c', '#d97706', '#16a34a', '#0891b2',
  '#2563eb', '#4b5563',
]

onMounted(() => {
  store.fetchTags()
})

function openCreate() {
  editingTag.value = null
  formName.value = ''
  formColor.value = 'var(--brand-primary)'
  formIsProject.value = false
  showForm.value = true
}

function openEdit(tag: Tag) {
  editingTag.value = tag
  formName.value = tag.name
  formColor.value = tag.color
  formIsProject.value = tag.is_project ?? false
  showForm.value = true
}

async function handleSubmit() {
  error.value = ''
  const data: CreateTagData = {
    name: formName.value.trim(),
    color: formColor.value,
    is_project: formIsProject.value,
  }
  if (!data.name) {
    error.value = t('tags.nameRequired')
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
  if (!confirm(t('tags.deleteConfirm', { name: tag.name }))) return
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
      <h2>{{ t('tags.title') }}</h2>
      <button class="btn primary" @click="openCreate">{{ t('tags.addTag') }}</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="search-bar">
      <input
        v-model="searchQuery"
        :placeholder="t('tags.searchPlaceholder')"
        @keyup.enter="handleSearch"
      />
      <button class="btn" @click="handleSearch">Search</button>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editingTag ? t('tags.editTag') : t('tags.newTag') }}</h3>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>{{ t('tags.name') }}</label>
            <input v-model="formName" :placeholder="t('tags.namePlaceholder')" required />
          </div>
          <div class="form-group">
            <label>{{ t('tags.color') }}</label>
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
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formIsProject" />
              <span>{{ t('tags.useAsProject') }}</span>
            </label>
            <p class="hint">{{ t('tags.projectHint') }}</p>
          </div>
          <div class="preview-group">
            <label>{{ t('tags.preview') }}</label>
            <span class="tag-chip" :style="{ background: formColor + '20', color: formColor, borderColor: formColor }">
              {{ formName || t('tags.tagNameDefault') }}
            </span>
            <span v-if="formIsProject" class="project-badge">{{ t('tags.project') }}</span>
          </div>
          <div class="form-actions">
            <button type="button" class="btn" @click="showForm = false">Cancel</button>
            <button type="submit" class="btn primary">{{ editingTag ? 'Update' : 'Create' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="store.loading" class="loading-msg">{{ t('tags.loadingMsg') }}</div>

    <div v-else-if="store.tags.length === 0" class="empty">
      {{ t('tags.emptyState') }}
    </div>

    <div v-else class="tags-grid">
      <div v-for="tag in store.tags" :key="tag.id" class="tag-card">
        <div class="tag-card-header">
          <span class="tag-chip" :style="{ background: tag.color + '20', color: tag.color, borderColor: tag.color }">
            {{ tag.name }}
          </span>
          <span v-if="tag.is_project" class="project-badge">{{ t('tags.project') }}</span>
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
.loading-msg { color: var(--text-secondary); text-align: center; padding: 40px 0; }
.empty { color: var(--text-muted); text-align: center; padding: 40px 0; }

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
  color: var(--text-primary);
}
.form-group input[type="text"],
.form-group input:not([type]) {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.checkbox-group {
  margin-bottom: 16px;
}
.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
}
.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--brand-primary);
}
.hint {
  margin: 4px 0 0 24px;
  font-size: 12px;
  color: var(--text-muted);
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
  border-color: var(--text-primary);
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #1f2937;
}
.color-input {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  cursor: pointer;
  padding: 2px;
}

.preview-group {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.preview-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-right: 4px;
}

.tag-chip {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid;
}

.project-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: #dbeafe;
  color: #1d4ed8;
  border: 1px solid #93c5fd;
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
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tag-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tag-card-actions {
  display: flex;
  gap: 6px;
}
.btn-sm {
  padding: 4px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  background: var(--bg-surface);
  cursor: pointer;
  font-size: 12px;
}
.btn-sm:hover { background: var(--bg-surface-hover); }
.btn-sm.danger { color: #dc2626; border-color: #fca5a5; }
.btn-sm.danger:hover { background: #fef2f2; }
</style>
