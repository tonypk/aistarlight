<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const error = ref('')
const loading = ref(true)

onMounted(async () => {
  const token = route.query.token as string
  if (!token) {
    error.value = 'No SSO token provided'
    loading.value = false
    return
  }

  try {
    await auth.loginWithSSO(token)
    router.replace('/')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
    error.value = msg || 'SSO login failed. The token may have expired.'
    loading.value = false
  }
})
</script>

<template>
  <div class="sso-callback">
    <div v-if="loading" class="sso-loading">
      <div class="spinner"></div>
      <p>Signing you in...</p>
    </div>
    <div v-else-if="error" class="sso-error">
      <h2>SSO Login Failed</h2>
      <p>{{ error }}</p>
      <router-link to="/login" class="login-link">Go to Login</router-link>
    </div>
  </div>
</template>

<style scoped>
.sso-callback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #0f0f23;
  color: #e2e8f0;
}
.sso-loading {
  text-align: center;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.sso-loading p {
  font-size: 16px;
  color: #94a3b8;
}
.sso-error {
  text-align: center;
  max-width: 400px;
  padding: 32px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}
.sso-error h2 {
  color: #f87171;
  margin-bottom: 12px;
}
.sso-error p {
  color: #94a3b8;
  margin-bottom: 20px;
}
.login-link {
  color: #6366f1;
  text-decoration: none;
  font-weight: 600;
}
.login-link:hover {
  text-decoration: underline;
}
</style>
