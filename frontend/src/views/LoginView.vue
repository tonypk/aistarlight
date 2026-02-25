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
      <h1>AIStarlight</h1>
      <p class="subtitle">Philippine Tax Filing Assistant</p>

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
  background: #fff;
  padding: 48px;
  border-radius: 16px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
h1 { text-align: center; color: #1a1a2e; font-size: 28px; }
.subtitle { text-align: center; color: #888; margin-bottom: 32px; }
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 4px; font-size: 14px; color: #555; }
.field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}
.field input:focus { outline: none; border-color: #4f46e5; }
.error { color: #ef4444; font-size: 13px; margin-bottom: 12px; }
.submit-btn {
  width: 100%;
  padding: 12px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.submit-btn:hover { background: #4338ca; }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.toggle { text-align: center; margin-top: 16px; font-size: 14px; color: #888; }
.toggle a { color: #4f46e5; }
</style>
