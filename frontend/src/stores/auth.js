import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/index.js'

const LS_TOKEN = 'galera_token'

export const useAuthStore = defineStore('auth', () => {
  const token       = ref(localStorage.getItem(LS_TOKEN) || '')
  const authEnabled = ref(false)
  const loading     = ref(false)
  const loginError  = ref('')

  const isLoggedIn = computed(() => {
    if (!authEnabled.value) return true
    return !!token.value
  })

  function _setToken(t) {
    token.value = t
    if (t) {
      localStorage.setItem(LS_TOKEN, t)
    } else {
      localStorage.removeItem(LS_TOKEN)
    }
  }

  async function init() {
    // Check if auth is enabled on backend
    try {
      const resp = await api.get('/api/auth/status')
      authEnabled.value = !!resp.data?.enabled

      if (!authEnabled.value) return  // no auth needed

      // Validate existing token
      const saved = localStorage.getItem(LS_TOKEN)
      if (!saved) {
        _setToken('')
        return
      }
      try {
        const me = await api.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${saved}` }
        })
        if (me.status === 200) {
          _setToken(saved)
        } else {
          _setToken('')
        }
      } catch {
        _setToken('')
      }
    } catch {
      // Backend offline — assume no auth
      authEnabled.value = false
    }
  }

  async function login(username, password) {
    loading.value    = true
    loginError.value = ''
    try {
      const resp = await api.post('/api/auth/login', { username, password })
      if (resp.data?.token) {
        _setToken(resp.data.token)
        return true
      } else {
        loginError.value = resp.data?.detail || 'Неверный логин или пароль'
        return false
      }
    } catch (e) {
      loginError.value = e.response?.data?.detail || 'Ошибка соединения с сервером'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await api.post('/api/auth/logout')
    } catch { /* ignore */ }
    _setToken('')
  }

  function clearError() {
    loginError.value = ''
  }

  return {
    token, authEnabled, loading, loginError,
    isLoggedIn,
    init, login, logout, clearError,
  }
})
