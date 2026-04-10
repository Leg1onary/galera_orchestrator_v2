// ТЗ раздел 6.1, 4.2: все роуты кроме /login требуют auth.
// Guard: один вызов checkAuth() до первого resolved, потом смотрим isAuthenticated.
// Lazy-load всех страниц кроме Login (она маленькая и нужна сразу).
// Персистентность: последний роут сохраняется в localStorage (go2-last-route).
// Overview — дефолтный маршрут. Редирект на last route только при прямом заходе
// (navigationId === 1, т.е. первая навигация в сессии). Явный клик по Overview — работает.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginPage from '@/pages/LoginPage.vue'

const LS_LAST_ROUTE = 'go2-last-route'

const SKIP_PERSIST = new Set<string>(['login', 'overview', 'not-found'])

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

router.beforeEach(async (to) => {
    const auth = useAuthStore()

    if (!auth.authChecked) {
        try {
            await auth.checkAuth()
        } catch {
            // сеть недоступна — authChecked выставлен в finally
        }
    }

    if (to.meta.public) {
        if (auth.isAuthenticated && to.name === 'login') {
            const last = localStorage.getItem(LS_LAST_ROUTE)
            return last ? last : { name: 'overview' }
        }
        return true
    }

    if (!auth.isAuthenticated) {
        return { name: 'login', query: { redirect: to.fullPath } }
    }

    // Восстанавливаем last route ТОЛЬКО при первом заходе на overview (прямой URL / F5).
    // router.currentRoute.value.name === null означает что это первая навигация в сессии.
    // Если пользователь явно кликнул по Overview в сайдбаре — currentRoute уже имеет имя,
    // редиректить не нужно.
    if (to.name === 'overview' && router.currentRoute.value.name == null) {
        const last = localStorage.getItem(LS_LAST_ROUTE)
        if (last && last !== '/') return last
    }
})

router.afterEach((to) => {
    const name = String(to.name ?? '')
    if (!to.meta.public && !SKIP_PERSIST.has(name)) {
        localStorage.setItem(LS_LAST_ROUTE, to.fullPath)
    }
})

export default router
