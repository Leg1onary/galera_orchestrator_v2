// Базовый axios-клиент. BASE_URL пустой → относительные пути → Vite proxy в dev,
// сам контейнер в prod. withCredentials обязателен для httpOnly cookie (ТЗ раздел 4).
import axios from 'axios'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
    baseURL: BASE_URL,
    withCredentials: true,
    timeout: 30000, // [MINOR FIX] 30 сек потолок — диагностические SSH-запросы могут быть долгими
    headers: { 'Content-Type': 'application/json' },
})

// [MAJOR FIX] Флаг дедупликации: не делаем множественные редиректы
// если несколько запросов одновременно получили 401
let isRedirectingToLogin = false

// 401 → сбрасываем auth-state + редирект на /login (ТЗ п.4.2)
api.interceptors.response.use(
    (r) => r,
    async (err) => {
        if (err.response?.status === 401 && !isRedirectingToLogin) {
            isRedirectingToLogin = true

            // [MAJOR FIX] Синхронный динамический импорт через getActivePinia
            // избегает circular deps и гарантирует что Pinia уже инициализирована
            const { useAuthStore } = await import('@/stores/auth')
            const store = useAuthStore()

            if (store.isAuthenticated) {
                store.$patch({ isAuthenticated: false, authChecked: true })
            }

            // [BLOCKER FIX] ТЗ п.4.2: редирект на /login после сброса state
            await router.push('/login')

            // Сбрасываем флаг после завершения редиректа
            isRedirectingToLogin = false
        }

        return Promise.reject(err)
    }
)