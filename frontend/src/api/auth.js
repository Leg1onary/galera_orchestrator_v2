import apiClient from '@/api/client.js'

/**
 * Auth API — thin wrappers around the three auth endpoints.
 * Business logic lives in stores/auth.js, not here.
 *
 * Per ТЗ section 4.1:
 *   POST /api/auth/login
 *   POST /api/auth/logout
 *   GET  /api/auth/me
 */

/**
 * Authenticate and receive an httpOnly session cookie.
 *
 * @param {{ username: string, password: string }} credentials
 * @returns {Promise<{ message: string }>}
 * @throws {AxiosError} on 401 (wrong credentials) or 5xx (server error)
 */
export async function apiLogin(credentials) {
    const response = await apiClient.post('/api/auth/login', credentials)
    return response.data
}

/**
 * Clear the session cookie on the server.
 *
 * @returns {Promise<{ message: string }>}
 */
export async function apiLogout() {
    const response = await apiClient.post('/api/auth/logout')
    return response.data
}

/**
 * Check current authentication state.
 * Called by authStore.checkAuth() on every app load / page refresh.
 *
 * Returns { authenticated: true, username: "admin" } if cookie is valid.
 * Throws AxiosError with status 401 if not authenticated.
 *
 * @returns {Promise<{ authenticated: boolean, username: string }>}
 */
export async function apiGetMe() {
    const response = await apiClient.get('/api/auth/me')
    return response.data
}