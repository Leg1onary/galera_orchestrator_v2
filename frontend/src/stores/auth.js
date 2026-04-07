import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('galera_token') || '')
  const username = ref(localStorage.getItem('galera_username') || '')
  const authEnabled = ref(false)
  const checked = ref(false)

  const isAuthenticated = computed(() => {
    if (!authEnabled.value) return true
    return !!token.value
  })

  async function checkAuthStatus() {
    try {
      const { data } = await api.get('/api/auth/status')
      authEnabled.value = data.enabled
    } catch {
      authEnabled.value = false
    } finally {
      checked.value = true
    }
  }

  async function login(user, password) {
    const { data } = await api.post('/api/auth/login', { username: user, password })
    token.value = data.token
    username.value = data.username
    localStorage.setItem('galera_token', data.token)
    localStorage.setItem('galera_username', data.username)
    return data
  }

  async function logout() {
    try { await api.post('/api/auth/logout') } catch {}
    token.value = ''
    username.value = ''
    localStorage.removeItem('galera_token')
    localStorage.removeItem('galera_username')
  }

  return { token, username, authEnabled, checked, isAuthenticated, checkAuthStatus, login, logout }
})
