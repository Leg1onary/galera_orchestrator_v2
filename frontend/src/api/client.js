import axios from 'axios'

/**
 * Axios instance for all API calls.
 *
 * - baseURL '/': all requests are relative, works in both dev (proxied) and prod
 * - withCredentials: true is REQUIRED so the httpOnly auth cookie is sent
 *   with every request, including cross-origin in dev (proxied via Vite)
 */
const apiClient = axios.create({
    baseURL: '/',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    timeout: 15000,
})

/**
 * Response interceptor — handle 401 globally.
 *
 * Per ТЗ section 4.2: "При ответе 401 от любого API frontend очищает
 * auth-state и делает редирект на /login."
 *
 * Imports are lazy (inside the handler) to avoid circular dependency:
 *   client.js → stores/auth.js → api/auth.js → client.js
 */
apiClient.interceptors.response.use(
    // 2xx responses pass through unchanged
    (response) => response,

    // Error handler
    async (error) => {
        const status = error.response?.status

        if (status === 401) {
            // Lazy import to break circular dependency chain
            const { useAuthStore } = await import('@/stores/auth.js')
            const { default: router } = await import('@/router/index.js')

            const authStore = useAuthStore()
            const currentPath = router.currentRoute.value?.path ?? '/'

            // Only redirect if we're not already on the login page
            // Avoids infinite redirect loop when /api/auth/login itself returns 401
            if (currentPath !== '/login') {
                authStore.$reset()
                router.push({ name: 'login' })
            }
        }

        return Promise.reject(error)
    }
)

export default apiClient