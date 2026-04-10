// ТЗ раздел 4.3 — auth store.
// Состояние: isAuthenticated, username, authChecked.
// JWT живёт только в httpOnly cookie — store не хранит токен.
import { defineStore } from 'pinia'
import { api } from '@/api/client'

// [MINOR FIX] типизированный ответ GET /api/auth/me
interface AuthMeResponse {
    authenticated: boolean
    username: string
}

interface AuthState {
    isAuthenticated: boolean
    username: string | null
    authChecked: boolean
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthState => ({
        isAuthenticated: false,
        username: null,
        authChecked: false,
    }),

    actions: {
        // Вызывается router guard-ом при каждой навигации до первого resolved.
        // ТЗ раздел 4.2: GET /api/auth/me — единственный способ проверить сессию.
        // [MAJOR FIX] Повторный вызов допускается только если ещё не проверяли
        // ИЛИ если interceptor сбросил authChecked=false при 401.
        async checkAuth() {
            if (this.authChecked) return
            try {
                const { data } = await api.get<AuthMeResponse>('/api/auth/me')
                this.isAuthenticated = data.authenticated
                this.username = data.username ?? null
            } catch {
                this.isAuthenticated = false
                this.username = null
            } finally {
                this.authChecked = true
            }
        },

        async login(username: string, password: string) {
            const { data } = await api.post<AuthMeResponse>(
                '/api/auth/login',
                { username, password }
            )
            this.isAuthenticated = true
            this.username = data.username ?? username
            this.authChecked = true
        },

        async logout() {
            try {
                await api.post('/api/auth/logout')
            } finally {
                this.isAuthenticated = false
                this.username = null
                // [MAJOR FIX] authChecked остаётся true после logout —
                // мы точно знаем что пользователь не авторизован.
                // false спровоцировал бы повторный GET /api/auth/me в guard → 401 loop.
                this.authChecked = true
            }
        },
    },
})