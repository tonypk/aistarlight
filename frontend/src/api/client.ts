import axios from 'axios'
import { useToastStore } from '../stores/toast'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          const tokens = data.data
          localStorage.setItem('access_token', tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)
          error.config.headers.Authorization = `Bearer ${tokens.access_token}`
          return client(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    // Show toast for non-401 errors (skip if caller opts out via _silentError)
    if (error.response?.status !== 401 && !error.config?._silentError) {
      try {
        const toast = useToastStore()
        const msg =
          error.response?.data?.detail ||
          error.response?.data?.error ||
          error.message ||
          'Request failed'
        toast.error(msg)
      } catch {
        // Toast store not ready yet (before app mount) — ignore
      }
    }

    return Promise.reject(error)
  }
)

export { client }
