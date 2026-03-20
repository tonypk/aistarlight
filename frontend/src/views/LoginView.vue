<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

const isRegister = ref(false)
const email = ref('')
const password = ref('')
const fullName = ref('')
const companyName = ref('')
const selectedJurisdiction = ref('PH')
const loading = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register({
        email: email.value,
        password: password.value,
        full_name: fullName.value,
        company_name: companyName.value,
        jurisdiction: selectedJurisdiction.value,
      })
    } else {
      await auth.login({ email: email.value, password: password.value })
    }
    router.push('/')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    message.error(err.response?.data?.error || 'Something went wrong')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1>HalaOS</h1>
      <p class="subtitle">Smart Tax Filing System</p>

      <div class="product-switcher">
        <a href="https://hr.halaos.com/login" class="product-btn">
          <span class="product-icon">&#x1F465;</span> HR
        </a>
        <span class="product-btn active">
          <span class="product-icon">&#x1F4B0;</span> Finance
        </span>
      </div>

      <div class="jurisdiction-selector">
        <p class="jurisdiction-label">Select Your Country</p>
        <div class="jurisdiction-options">
          <button
            type="button"
            class="jurisdiction-btn"
            :class="{ active: selectedJurisdiction === 'PH' }"
            @click="selectedJurisdiction = 'PH'"
            data-testid="jurisdiction-ph"
          >
            <span class="flag">PH</span>
            <span class="country-name">Philippines</span>
          </button>
          <button
            type="button"
            class="jurisdiction-btn"
            :class="{ active: selectedJurisdiction === 'SG' }"
            @click="selectedJurisdiction = 'SG'"
            data-testid="jurisdiction-sg"
          >
            <span class="flag">SG</span>
            <span class="country-name">Singapore</span>
          </button>
          <button
            type="button"
            class="jurisdiction-btn"
            :class="{ active: selectedJurisdiction === 'LK' }"
            @click="selectedJurisdiction = 'LK'"
            data-testid="jurisdiction-lk"
          >
            <span class="flag">LK</span>
            <span class="country-name">Sri Lanka</span>
          </button>
        </div>
      </div>

      <NForm @submit.prevent="handleSubmit">
        <NFormItem v-if="isRegister" label="Full Name">
          <NInput v-model:value="fullName" placeholder="Juan dela Cruz" />
        </NFormItem>
        <NFormItem v-if="isRegister" label="Company Name">
          <NInput v-model:value="companyName" placeholder="My Company Inc." />
        </NFormItem>
        <NFormItem label="Email">
          <NInput v-model:value="email" type="text" placeholder="you@company.com" data-testid="login-email" />
        </NFormItem>
        <NFormItem label="Password">
          <NInput v-model:value="password" type="password" show-password-on="click" placeholder="Enter password" data-testid="login-password" />
        </NFormItem>

        <NButton
          type="primary"
          block
          :loading="loading"
          attr-type="submit"
          data-testid="login-submit"
          @click="handleSubmit"
        >
          {{ isRegister ? 'Create Account' : 'Sign In' }}
        </NButton>
      </NForm>

      <p class="toggle">
        {{ isRegister ? 'Already have an account?' : 'Need an account?' }}
        <a href="#" @click.prevent="isRegister = !isRegister" data-testid="login-toggle">
          {{ isRegister ? 'Sign In' : 'Register' }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 50%, #2563eb 100%);
}
.login-card {
  background: var(--bg-surface, #ffffff);
  padding: 48px;
  border-radius: 16px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
h1 { text-align: center; color: #1e3a5f; font-size: 28px; }
.subtitle { text-align: center; color: var(--text-muted); margin-bottom: 24px; }
.product-switcher {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 24px;
}
.product-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  border: 2px solid var(--border-default, #e5e7eb);
  color: var(--text-secondary, #555555);
  background: transparent;
  cursor: pointer;
}
.product-btn:hover {
  border-color: #3b82f6;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.05);
}
.product-btn.active {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  border-color: transparent;
  cursor: default;
}
.product-icon { font-size: 16px; }
.jurisdiction-selector { margin-bottom: 24px; }
.jurisdiction-label {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.jurisdiction-options {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.jurisdiction-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 24px;
  border: 2px solid var(--border-default);
  border-radius: 12px;
  background: var(--bg-surface);
  cursor: pointer;
  transition: all 0.2s;
  min-width: 100px;
}
.jurisdiction-btn:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}
.jurisdiction-btn.active {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 0 0 1px #2563eb;
}
.jurisdiction-btn .flag {
  font-size: 24px;
  font-weight: 700;
  color: #1e3a5f;
  margin-bottom: 4px;
}
.jurisdiction-btn .country-name {
  font-size: 12px;
  color: var(--text-secondary);
}
.toggle { text-align: center; margin-top: 16px; font-size: 14px; color: var(--text-muted); }
.toggle a { color: #2563eb; }

@media (max-width: 768px) {
  .login-card {
    width: 100%;
    max-width: 400px;
    padding: 24px 20px;
    margin: 16px;
    border-radius: 12px;
  }
  .jurisdiction-options { gap: 8px; }
  .jurisdiction-btn { padding: 10px 16px; min-width: 80px; }
  .jurisdiction-btn .flag { font-size: 20px; }
  .jurisdiction-btn .country-name { font-size: 11px; }
}
</style>
