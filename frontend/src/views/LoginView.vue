<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import type { FormRules, FormInst } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()

const formRef = ref<FormInst | null>(null)
const form = ref({ email: '', password: '' })
const selectedJurisdiction = ref('PH')
const loading = ref(false)

const jurisdictions = [
  { code: 'PH', name: 'Philippines' },
  { code: 'SG', name: 'Singapore' },
  { code: 'LK', name: 'Sri Lanka' },
]

const rules = computed<FormRules>(() => ({
  email: [
    { required: true, message: t('auth.fieldRequired'), trigger: ['blur', 'input'] },
  ],
  password: [
    { required: true, message: t('auth.fieldRequired'), trigger: ['blur', 'input'] },
  ],
}))

async function handleLogin() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch (errors: unknown) {
    const errArr = errors as Array<Array<{ message?: string }>> | undefined
    const firstMsg = errArr?.[0]?.[0]?.message
    message.warning(firstMsg || t('auth.fieldRequired'))
    return
  }
  loading.value = true
  try {
    await auth.login({ email: form.value.email, password: form.value.password })
    router.push('/')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    message.error(err.response?.data?.error || t('auth.loginFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="brand-header">
        <router-link to="/" class="brand-logo">
          <span class="logo-icon">H</span>
          <span class="logo-text">HalaOS</span>
        </router-link>
      </div>

      <div class="product-switcher">
        <a href="https://hr.halaos.com/login" class="product-btn">
          <span class="product-icon">&#x1F465;</span> HR
        </a>
        <span class="product-btn active">
          <span class="product-icon">&#x1F4B0;</span> Finance
        </span>
      </div>

      <div class="jurisdiction-selector">
        <p class="jurisdiction-label">{{ t('auth.selectCountry') }}</p>
        <div class="jurisdiction-options">
          <button
            v-for="j in jurisdictions"
            :key="j.code"
            type="button"
            class="jurisdiction-btn"
            :class="{ active: selectedJurisdiction === j.code }"
            :data-testid="`jurisdiction-${j.code.toLowerCase()}`"
            @click="selectedJurisdiction = j.code"
          >
            <span class="flag">{{ j.code }}</span>
            <span class="country-name">{{ j.name }}</span>
          </button>
        </div>
      </div>

      <NForm
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
      >
        <NFormItem path="email" :label="t('auth.email')">
          <NInput
            v-model:value="form.email"
            :input-props="{ type: 'email' }"
            :placeholder="t('auth.emailPlaceholder')"
            data-testid="login-email"
          />
        </NFormItem>
        <NFormItem path="password" :label="t('auth.password')">
          <NInput
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            :placeholder="t('auth.passwordPlaceholder')"
            data-testid="login-password"
          />
        </NFormItem>

        <NButton
          type="primary"
          block
          :loading="loading"
          attr-type="submit"
          data-testid="login-submit"
          @click="handleLogin"
        >
          {{ t('auth.login') }}
        </NButton>
      </NForm>

      <div class="auth-footer">
        <span>{{ t('auth.noAccount') }}</span>
        <router-link to="/register" data-testid="login-toggle">{{ t('auth.register') }}</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%);
}

.login-card {
  background: var(--bg-surface, #ffffff);
  padding: 40px 36px 32px;
  border-radius: 16px;
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.06);
}

.brand-header {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.brand-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  color: #1e3a5f;
  letter-spacing: -0.5px;
}

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

.product-icon {
  font-size: 16px;
}

.jurisdiction-selector {
  margin-bottom: 24px;
}

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
  border: 2px solid var(--border-default, #e5e7eb);
  border-radius: 12px;
  background: var(--bg-surface, #ffffff);
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
  color: var(--text-secondary, #6b7280);
}

.auth-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-default, #e5e7eb);
  font-size: 14px;
  color: var(--text-muted, #6b7280);
}

.auth-footer a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.auth-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-card {
    padding: 24px 20px;
    margin: 16px;
    border-radius: 12px;
  }

  .jurisdiction-options {
    gap: 8px;
  }

  .jurisdiction-btn {
    padding: 10px 16px;
    min-width: 80px;
  }

  .jurisdiction-btn .flag {
    font-size: 20px;
  }

  .jurisdiction-btn .country-name {
    font-size: 11px;
  }
}
</style>
