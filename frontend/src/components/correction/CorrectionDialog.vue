<script setup lang="ts">
import { ref } from 'vue'
import { correctionsApi } from '@/api/corrections'

const props = defineProps<{
  entityType: string
  entityId: string
  fieldName: string
  oldValue: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: [newValue: string]
}>()

const newValue = ref('')
const reason = ref('')
const saving = ref(false)
const error = ref('')

async function handleSave() {
  if (!newValue.value.trim()) {
    error.value = 'New value is required'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await correctionsApi.create({
      entity_type: props.entityType,
      entity_id: props.entityId,
      field_name: props.fieldName,
      old_value: props.oldValue,
      new_value: newValue.value.trim(),
      reason: reason.value.trim() || undefined,
    })
    emit('saved', newValue.value.trim())
    handleClose()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Failed to save correction'
  } finally {
    saving.value = false
  }
}

function handleClose() {
  newValue.value = ''
  reason.value = ''
  error.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">
        <h3>Correct: {{ fieldName }}</h3>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>
      <div class="dialog-body">
        <div class="field-group">
          <label>Current Value</label>
          <div class="current-value">{{ oldValue || '(empty)' }}</div>
        </div>
        <div class="field-group">
          <label>New Value <span class="required">*</span></label>
          <input
            v-model="newValue"
            type="text"
            class="input"
            placeholder="Enter corrected value..."
            autofocus
          />
        </div>
        <div class="field-group">
          <label>Reason (optional)</label>
          <input
            v-model="reason"
            type="text"
            class="input"
            placeholder="Why is this correction needed?"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
      <div class="dialog-footer">
        <button class="cancel-btn" @click="handleClose">Cancel</button>
        <button class="save-btn" @click="handleSave" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Correction' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog {
  background: #fff;
  border-radius: 12px;
  width: 460px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.dialog-header h3 {
  font-size: 15px;
  margin: 0;
}
.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #9ca3af;
}
.dialog-body {
  padding: 20px;
}
.field-group {
  margin-bottom: 16px;
}
.field-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
  color: #374151;
}
.required {
  color: #ef4444;
}
.current-value {
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  font-family: monospace;
  font-size: 13px;
  color: #6b7280;
}
.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}
.input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}
.error {
  color: #ef4444;
  font-size: 13px;
  margin-top: 8px;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}
.cancel-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.save-btn {
  padding: 8px 16px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.save-btn:hover {
  background: #4338ca;
}
.save-btn:disabled {
  opacity: 0.5;
}
</style>
