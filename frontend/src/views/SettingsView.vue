<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { client } from '../api/client'

const form = ref({
  company_name: '',
  tin_number: '',
  rdo_code: '',
  vat_classification: 'vat_registered',
})

const saving = ref(false)
const saved = ref(false)
const apiKey = ref('')

onMounted(async () => {
  const res = await client.get('/settings/company')
  const data = res.data.data
  form.value = {
    company_name: data.company_name || '',
    tin_number: data.tin_number || '',
    rdo_code: data.rdo_code || '',
    vat_classification: data.vat_classification || 'vat_registered',
  }
})

async function handleSave() {
  saving.value = true
  saved.value = false
  try {
    await client.put('/settings/company', form.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

async function generateApiKey() {
  if (!confirm('Generate a new API key? This will invalidate any existing key.')) return
  const res = await client.post('/auth/api-key')
  apiKey.value = res.data.data.api_key
}
</script>

<template>
  <div class="settings-view">
    <h2>Company Settings</h2>

    <form class="settings-form" @submit.prevent="handleSave">
      <div class="field">
        <label>Company Name</label>
        <input v-model="form.company_name" required />
      </div>
      <div class="field">
        <label>TIN (Tax Identification Number)</label>
        <input v-model="form.tin_number" placeholder="123-456-789-000" />
      </div>
      <div class="field">
        <label>RDO Code</label>
        <input v-model="form.rdo_code" placeholder="e.g., 050" />
      </div>
      <div class="field">
        <label>VAT Classification</label>
        <select v-model="form.vat_classification">
          <option value="vat_registered">VAT Registered</option>
          <option value="non_vat">Non-VAT (Percentage Tax)</option>
        </select>
      </div>

      <button type="submit" :disabled="saving">
        {{ saving ? 'Saving...' : 'Save Settings' }}
      </button>
      <span v-if="saved" class="saved">Settings saved!</span>
    </form>

    <div class="api-section">
      <h3>API Access</h3>
      <p>Generate an API key for programmatic access to the AIStarlight API.</p>
      <button class="api-btn" @click="generateApiKey">Generate API Key</button>
      <div v-if="apiKey" class="api-key">
        <code>{{ apiKey }}</code>
        <p class="warn">Save this key - it won't be shown again!</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-view h2 { margin-bottom: 24px; }
.settings-form {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  max-width: 600px;
}
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 4px; font-size: 14px; color: #555; }
.field input, .field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}
button {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
button:hover { background: #4338ca; }
.saved { color: #059669; margin-left: 12px; }
.api-section {
  margin-top: 32px;
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  max-width: 600px;
}
.api-section h3 { margin-bottom: 8px; }
.api-section p { color: #888; margin-bottom: 16px; font-size: 14px; }
.api-btn { background: #059669; }
.api-btn:hover { background: #047857; }
.api-key {
  margin-top: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}
.api-key code {
  display: block;
  font-size: 14px;
  word-break: break-all;
  color: #1a1a2e;
}
.warn { color: #ef4444; font-size: 12px; margin-top: 8px; }
</style>
