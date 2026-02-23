import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type LoginData, type RegisterData } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<Record<string, string> | null>(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(data: LoginData) {
    const res = await authApi.login(data)
    const tokens = res.data.data
    accessToken.value = tokens.access_token
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    await fetchUser()
  }

  async function register(data: RegisterData) {
    await authApi.register(data)
    await login({ email: data.email, password: data.password })
  }

  async function fetchUser() {
    const res = await authApi.me()
    user.value = res.data.data
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { user, accessToken, isAuthenticated, login, register, fetchUser, logout }
})
