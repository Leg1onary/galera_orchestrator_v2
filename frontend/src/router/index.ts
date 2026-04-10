// ТЗ раздел 6.1, 4.2: все роуты кроме /login требуют auth.
// Guard: один вызов checkAuth() до первого resolved, потом смотрим isAuthenticated.
// Lazy-load всех страниц кроме Login (она маленькая и нужна сразу).
// Персистентность: последний роут сохраняется в localStorage (go2-last-route).
// После auth-редиректа восстанавливается если нет явного ?redirect= параметра.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginPage from '@/pages/LoginPage.vue'

const LS_LAST_ROUTE = 'go2-last-route'

// Роуты, которые не нужно запоминать как «последний посещённый»
const SKIP_PERSIST = new Set(['/', '/login'])

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
        {
            path: '/:pathMatch(.*)*',
            name: 'not-found',
            component: () => import('@/pages/NotFoundPage.vue'),
            meta: { public: true },
        },
    ],
})

// ТЗ раздел 4.2: guard через GET /api/auth/me
router.beforeEach(async (to) => {
    const auth = useAuthStore()

    if (!auth.authChecked) {
        try {
            await auth.checkAuth()
        } catch {
            // Сеть недоступна или 500 — authChecked выставлен в auth.ts
        }
    }

    if (to.meta.public) {
        if (auth.isAuthenticated && to.name === 'login') {
            // Авторизованный идёт на /login — редиректим на последний роут или overview
            const last = localStorage.getItem(LS_LAST_ROUTE)
            return (last && !SKIP_PERSIST.has(last)) ? last : { name: 'overview' }
        }
        return true
    }

    if (!auth.isAuthenticated) {
        return { name: 'login', query: { redirect: to.fullPath } }
    }

    // Авторизован, идёт на корень '/' — восстанавливаем последний роут
    if (to.path === '/') {
        const last = localStorage.getItem(LS_LAST_ROUTE)
        if (last && !SKIP_PERSIST.has(last)) return last
    }
})

// Сохраняем текущий роут после каждой навигации (кроме /login и /)
router.afterEach((to) => {
    if (!to.meta.public && !SKIP_PERSIST.has(to.path)) {
        localStorage.setItem(LS_LAST_ROUTE, to.fullPath)
    }
})

export default router
