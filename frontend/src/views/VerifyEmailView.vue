<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NResult, NSpin } from 'naive-ui'
import { authApi } from '../api/auth'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const token = route.query.token as string
  if (!token) {
    error.value = 'No verification token'
    loading.value = false
    return
  }
  try {
    await authApi.verifyEmail(token)
    setTimeout(() => router.push('/login'), 2000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    error.value = err.response?.data?.error || 'Verification failed'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="verify-page">
    <div class="verify-card">
      <div class="brand-header">
        <router-link to="/" class="brand-logo">
          <span class="logo-icon">H</span>
          <span class="logo-text">HalaOS</span>
        </router-link>
      </div>
      <div v-if="loading" style="text-align: center; padding: 32px 0;">
        <NSpin size="large" />
        <p style="margin-top: 16px; color: var(--text-muted);">{{ t('common.loading') }}</p>
      </div>
      <NResult v-else-if="!error" status="success" :title="t('common.success')" description="Redirecting to login..." />
      <NResult v-else status="error" title="Verification Failed" :description="error" />
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%);
}
.verify-card {
  width: 440px; max-width: 90vw; background: #fff; border-radius: 16px;
  padding: 40px 36px 32px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
.brand-header { text-align: center; margin-bottom: 24px; }
.brand-logo { display: inline-flex; align-items: center; gap: 8px; text-decoration: none; }
.logo-icon {
  width: 36px; height: 36px; background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800;
}
.logo-text { font-size: 22px; font-weight: 700; color: var(--text-primary, #0f172a); }
</style>
