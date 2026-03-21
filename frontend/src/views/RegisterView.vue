<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NForm, NFormItem, NInput, NButton, NSpace, NResult, useMessage } from 'naive-ui'
import type { FormRules, FormInst } from 'naive-ui'
import { authApi } from '../api/auth'

const { t } = useI18n()
const route = useRoute()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const emailInput = ref('')
const selectedJurisdiction = ref('PH')
const loading = ref(false)
const emailSent = ref(false)
const resending = ref(false)
const referralCode = ref((route.query.ref as string) || '')

const jurisdictions = [
  { code: 'PH', name: 'Philippines' },
  { code: 'SG', name: 'Singapore' },
  { code: 'LK', name: 'Sri Lanka' },
]

const rules: FormRules = {
  email: [{ required: true, type: 'email', message: t('auth.fieldRequired'), trigger: ['blur'] }],
}

const form = ref({ email: '' })

async function handleRegister() {
  try {
    await formRef.value?.validate()
  } catch { return }
  loading.value = true
  try {
    await authApi.register({
      email: form.value.email,
      password: '',
      full_name: '',
      company_name: '',
      jurisdiction: selectedJurisdiction.value,
      referral_code: referralCode.value || undefined,
    })
    emailInput.value = form.value.email
    emailSent.value = true
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    message.error(err.response?.data?.error || t('auth.loginFailed'))
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  resending.value = true
  try {
    await authApi.resendVerification(emailInput.value)
    message.success(t('auth.emailSent'))
  } catch {
    message.error(t('auth.loginFailed'))
  } finally {
    resending.value = false
  }
}
</script>

<template>
  <div class="register-wrapper">
    <!-- Email sent confirmation -->
    <div v-if="emailSent" class="register-card">
      <div class="brand-header">
        <router-link to="/" class="brand-logo">
          <span class="logo-icon">H</span>
          <span class="logo-text">HalaOS</span>
        </router-link>
      </div>
      <NResult status="success" :title="t('auth.checkEmail')" :description="t('auth.magicLinkSent', { email: emailInput })">
        <template #footer>
          <p style="color: #2563eb; font-weight: 600; margin-bottom: 16px; font-size: 16px;">{{ emailInput }}</p>
          <p style="color: var(--text-muted, #64748b); font-size: 14px; margin-bottom: 20px;">
            {{ t('auth.magicLinkExpiry') }}
          </p>
          <NSpace vertical :size="12" style="width: 100%;">
            <NButton quaternary block :loading="resending" @click="handleResend">
              {{ t('auth.didntReceive') }} {{ t('auth.resend') }}
            </NButton>
          </NSpace>
        </template>
      </NResult>
    </div>

    <!-- Registration form -->
    <div v-else class="register-card">
      <div class="brand-header">
        <router-link to="/" class="brand-logo">
          <span class="logo-icon">H</span>
          <span class="logo-text">HalaOS</span>
        </router-link>
        <h2>{{ t('auth.registerTitle') }}</h2>
      </div>

      <div class="product-switcher">
        <a href="https://hr.halaos.com/register" class="product-btn">
          <span class="product-icon">&#x1F465;</span> {{ t('product.hr') }}
        </a>
        <span class="product-btn active">
          <span class="product-icon">&#x1F4B0;</span> {{ t('product.finance') }}
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
            @click="selectedJurisdiction = j.code"
            :data-testid="'jurisdiction-' + j.code.toLowerCase()"
          >
            <span class="flag">{{ j.code }}</span>
            <span class="country-name">{{ j.name }}</span>
          </button>
        </div>
      </div>

      <NForm ref="formRef" :model="form" :rules="rules">
        <NFormItem path="email" :label="t('auth.email')">
          <NInput
            v-model:value="form.email"
            :placeholder="t('auth.emailPlaceholder')"
            :input-props="{ type: 'email', autocomplete: 'email' }"
            size="large"
            data-testid="register-email"
          />
        </NFormItem>
        <NButton
          type="primary"
          block
          size="large"
          :loading="loading"
          style="margin-top: 4px;"
          data-testid="register-submit"
          @click="handleRegister"
        >
          {{ t('auth.getStarted') }}
        </NButton>
      </NForm>

      <div class="auth-footer">
        <span>{{ t('auth.hasAccount') }}</span>
        <router-link to="/login">{{ t('auth.login') }}</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-wrapper {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%);
  padding: 40px 16px;
}
.register-card {
  width: 440px; max-width: 90vw; background: #fff; border-radius: 16px;
  padding: 40px 36px 32px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
.brand-header { text-align: center; margin-bottom: 32px; }
.brand-logo { display: inline-flex; align-items: center; gap: 8px; text-decoration: none; margin-bottom: 16px; }
.logo-icon {
  width: 36px; height: 36px; background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800;
}
.logo-text { font-size: 22px; font-weight: 700; color: var(--text-primary, #0f172a); }
.brand-header h2 { font-size: 16px; font-weight: 500; color: var(--text-muted, #64748b); margin: 0; }
.product-switcher { display: flex; gap: 12px; justify-content: center; margin-bottom: 24px; }
.product-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 10px 24px;
  border-radius: 10px; font-size: 14px; font-weight: 600; text-decoration: none;
  transition: all 0.2s; border: 2px solid var(--border-default, #e5e7eb);
  color: var(--text-secondary, #555); background: transparent; cursor: pointer;
}
.product-btn:hover { border-color: #93c5fd; color: #2563eb; background: #eff6ff; }
.product-btn.active { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; border-color: transparent; cursor: default; }
.product-icon { font-size: 16px; }
.jurisdiction-selector { margin-bottom: 24px; }
.jurisdiction-label { text-align: center; font-size: 14px; color: var(--text-secondary); margin-bottom: 10px; }
.jurisdiction-options { display: flex; gap: 12px; justify-content: center; }
.jurisdiction-btn {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 24px; border: 2px solid var(--border-default, #e5e7eb); border-radius: 12px;
  background: var(--bg-surface, #fff); cursor: pointer; transition: all 0.2s; min-width: 100px;
}
.jurisdiction-btn:hover { border-color: #93c5fd; background: #eff6ff; }
.jurisdiction-btn.active { border-color: #2563eb; background: #eff6ff; box-shadow: 0 0 0 1px #2563eb; }
.jurisdiction-btn .flag { font-size: 24px; font-weight: 700; color: #1e3a5f; margin-bottom: 4px; }
.jurisdiction-btn .country-name { font-size: 12px; color: var(--text-secondary, #555); }
.auth-footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; font-size: 14px; color: var(--text-muted, #64748b); }
.auth-footer a { color: #2563eb; font-weight: 600; text-decoration: none; margin-left: 4px; }

@media (max-width: 768px) {
  .register-card { padding: 24px 20px; }
  .jurisdiction-options { gap: 8px; }
  .jurisdiction-btn { padding: 10px 16px; min-width: 80px; }
  .jurisdiction-btn .flag { font-size: 20px; }
  .jurisdiction-btn .country-name { font-size: 11px; }
}
</style>
