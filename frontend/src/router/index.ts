// ТЗ раздел 6.1, 4.2: все роуты кроме /login требуют auth.
// Guard: один вызов checkAuth() до первого resolved, потом смотрим isAuthenticated.
// Lazy-load всех страниц кроме Login (она маленькая и нужна сразу).
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginPage from '@/pages/LoginPage.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginPage,
            meta: { public: true },
        },
        {
            path: '/',
            component: () => import('@/layouts/AppLayout.vue'),
            // meta на родителе — явная семантика, что все дочерние защищены
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    name: 'overview',
                    component: () => import('@/pages/OverviewPage.vue'),
                },
                {
                    path: 'nodes',
                    name: 'nodes',
                    component: () => import('@/pages/NodesPage.vue'),
                },
                {
                    path: 'topology',
                    name: 'topology',
                    component: () => import('@/pages/TopologyPage.vue'),
                },
                {
                    path: 'recovery',
                    name: 'recovery',
                    component: () => import('@/pages/RecoveryPage.vue'),
                },
                {
                    path: 'maintenance',
                    name: 'maintenance',
                    component: () => import('@/pages/MaintenancePage.vue'),
                },
                {
                    path: 'diagnostics',
                    name: 'diagnostics',
                    component: () => import('@/pages/DiagnosticsPage.vue'),
                },
                {
                    path: 'settings',
                    name: 'settings',
                    component: () => import('@/pages/SettingsPage.vue'),
                },
                {
                    path: 'docs',
                    name: 'docs',
                    component: () => import('@/pages/DocsPage.vue'),
                },
            ],
        },
        // NotFoundPage — всегда публичная, без auth
        {
            path: '/:pathMatch(.*)*',
            name: 'not-found',
            component: () => import('@/pages/NotFoundPage.vue'),
            meta: { public: true },
        },
    ],
})

// ТЗ раздел 4.2: guard через GET /api/auth/me
// authChecked гарантирует что checkAuth() вызывается только один раз за сессию
router.beforeEach(async (to) => {
    const auth = useAuthStore()

    // Один вызов checkAuth за сессию — с защитой от сетевых ошибок
    if (!auth.authChecked) {
        try {
            await auth.checkAuth()
        } catch {
            // Сеть недоступна или 500 — считаем неавторизованным,
            // authChecked всё равно должен быть выставлен в auth.ts в finally
        }
    }

    // Авторизованный юзер на /login → редирект на overview
    if (to.meta.public) {
        if (auth.isAuthenticated && to.name === 'login') {
            return { name: 'overview' }
        }
        return true
    }

    if (!auth.isAuthenticated) {
        return { name: 'login', query: { redirect: to.fullPath } }
    }
})

export default router