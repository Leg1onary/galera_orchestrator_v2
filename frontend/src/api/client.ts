// Базовый axios-клиент. BASE_URL пустой → относительные пути → Vite proxy в dev,
// сам контейнер в prod. withCredentials обязателен для httpOnly cookie (ТЗ раздел 4).
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
    baseURL: BASE_URL,
    withCredentials: true,
    headers: { 'Content-Type': 'application/json' },
})

// 401 → сбрасываем auth-state без редиректа (редирект делает router guard)
api.interceptors.response.use(
    (r) => r,
    (err) => {
        if (err.response?.status === 401) {
            // Импорт через getActivePinia чтобы не создавать circular deps
            import('@/stores/auth').then(({ useAuthStore }) => {
                const store = useAuthStore()
                if (store.isAuthenticated) store.$patch({ isAuthenticated: false })
            })
        }
        return Promise.reject(err)
    }
)