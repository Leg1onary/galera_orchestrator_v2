import { defineStore } from 'pinia'
import { apiGetMe, apiLogin, apiLogout } from '@/api/auth.js'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        /**
         * Whether the current user is authenticated.
         * Set by checkAuth() after GET /api/auth/me succeeds.
         */
        isAuthenticated: false,

        /**
         * Username of the authenticated user.
         * Null when not authenticated.
         * Per ТЗ section 4.3: store does NOT hold the JWT string.
         */
        username: null,

        /**
         * Whether the initial auth check has been performed.
         * The router guard waits for this to be true before making
         * any redirect decisions. This prevents a flash-redirect to /login
         * on page refresh when the user actually has a valid cookie.
         */
        authChecked: false,
    }),

    getters: {
        /**
         * Convenience getter — true only when auth check is done AND user is logged in.
         */
        isReady: (state) => state.authChecked && state.isAuthenticated,
    },

    actions: {
        /**
         * Check authentication state by calling GET /api/auth/me.
         * Sets isAuthenticated and username based on the response.
         * Sets authChecked = true regardless of the outcome.
         *
         * Per ТЗ section 4.2: this is the canonical way to determine auth state.
         * Called once by the router guard on first navigation.
         */
        async checkAuth() {
            try {
                const data = await apiGetMe()
                this.isAuthenticated = data.authenticated === true
                this.username = data.username ?? null
            } catch {
                // 401 or network error — treat as not authenticated
                this.isAuthenticated = false
                this.username = null
            } finally {
                this.authChecked = true
            }
        },

        /**
         * Log in with username and password.
         * Calls POST /api/auth/login — backend sets httpOnly cookie on success.
         * Then calls checkAuth() to populate the store.
         *
         * @throws {Error} if login fails (wrong credentials or server error)
         */
        async login(credentials) {
            // apiLogin throws on HTTP 4xx/5xx — let LoginPage.vue handle the error
            await apiLogin(credentials)
            // Re-check auth so store reflects the new cookie
            await this.checkAuth()
        },

        /**
         * Log out — calls POST /api/auth/logout to clear the httpOnly cookie.
         * Resets auth state regardless of whether the API call succeeds.
         */
        async logout() {
            try {
                await apiLogout()
            } catch {
                // Even if the API call fails, we clear local state
                // The cookie will expire on its own
            } finally {
                this.$reset()
            }
        },

        /**
         * Reset state to initial values.
         * Called by logout() and by the axios 401 interceptor.
         */
        $reset() {
            this.isAuthenticated = false
            this.username = null
            // Keep authChecked = true — we know the user is NOT authenticated
            // Setting it to false would trigger another checkAuth() call
            this.authChecked = true
        },
    },
})