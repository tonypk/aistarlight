<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const email = ref('')
const password = ref('')
const fullName = ref('')
const companyName = ref('')
const selectedJurisdiction = ref('PH')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
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
    error.value = err.response?.data?.error || 'Something went wrong'
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

      <form @submit.prevent="handleSubmit">
        <div v-if="isRegister" class="field">
          <label>Full Name</label>
          <input v-model="fullName" type="text" required placeholder="Juan dela Cruz" />
        </div>
        <div v-if="isRegister" class="field">
          <label>Company Name</label>
          <input v-model="companyName" type="text" required placeholder="My Company Inc." />
        </div>
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" required placeholder="you@company.com" data-testid="login-email" />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" required placeholder="Enter password" data-testid="login-password" />
        </div>

        <p v-if="error" class="error" data-testid="login-error">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading" data-testid="login-submit">
          {{ loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In' }}
        </button>
      </form>

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
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.login-card {
  background: var(--bg-surface);
  padding: 48px;
  border-radius: 16px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
h1 { text-align: center; color: #1a1a2e; font-size: 28px; }
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
  border: 2px solid var(--border-default, #334155);
  color: var(--text-secondary, #94a3b8);
  background: transparent;
  cursor: pointer;
}
.product-btn:hover {
  border-color: #818cf8;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.1);
}
.product-btn.active {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  border-color: transparent;
  cursor: default;
}
.product-icon {
  font-size: 16px;
}
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
  border-color: #a5b4fc;
  background: #f5f3ff;
}
.jurisdiction-btn.active {
  border-color: var(--brand-primary);
  background: #eef2ff;
  box-shadow: 0 0 0 1px var(--brand-primary);
}
.jurisdiction-btn .flag {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}
.jurisdiction-btn .country-name {
  font-size: 12px;
  color: var(--text-secondary);
}
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 4px; font-size: 14px; color: var(--text-secondary); }
.field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  font-size: 14px;
}
.field input:focus { outline: none; border-color: var(--brand-primary); }
.error { color: #ef4444; font-size: 13px; margin-bottom: 12px; }
.submit-btn {
  width: 100%;
  padding: 12px;
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.submit-btn:hover { background: var(--brand-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.toggle { text-align: center; margin-top: 16px; font-size: 14px; color: var(--text-muted); }
.toggle a { color: var(--brand-primary); }

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
