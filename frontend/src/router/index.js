import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

// Eagerly loaded — required before any auth check
import LoginPage from '@/pages/LoginPage.vue'
import NotFoundPage from '@/pages/NotFoundPage.vue'

// Lazy-loaded placeholder for pages not yet implemented in Phase 0
const PlaceholderPage = () => import('@/pages/PlaceholderPage.vue')

// AppLayout wraps all authenticated pages
const AppLayout = () => import('@/layouts/AppLayout.vue')

const routes = [
    // ── Public route ──────────────────────────────────────────────────────────
    {
        path: '/login',
        name: 'login',
        component: LoginPage,
        meta: { public: true },
    },

    // ── Authenticated routes — wrapped in AppLayout ────────────────────────
    {
        path: '/',
        component: AppLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'overview',
                // Phase 5: replace with () => import('@/pages/OverviewPage.vue')
                component: PlaceholderPage,
                meta: { title: 'Overview' },
            },
            {
                path: 'nodes',
                name: 'nodes',
                component: PlaceholderPage,
                meta: { title: 'Nodes' },
            },
            {
                path: 'topology',
                name: 'topology',
                component: PlaceholderPage,
                meta: { title: 'Topology' },
            },
            {
                path: 'recovery',
                name: 'recovery',
                component: PlaceholderPage,
                meta: { title: 'Recovery' },
            },
            {
                path: 'maintenance',
                name: 'maintenance',
                component: PlaceholderPage,
                meta: { title: 'Maintenance' },
            },
            {
                path: 'diagnostics',
                name: 'diagnostics',
                component: PlaceholderPage,
                meta: { title: 'Diagnostics' },
            },
            {
                path: 'settings',
                name: 'settings',
                component: PlaceholderPage,
                meta: { title: 'Settings' },
            },
            {
                path: 'docs',
                name: 'docs',
                component: PlaceholderPage,
                meta: { title: 'Documentation' },
            },
        ],
    },

    // ── 404 ───────────────────────────────────────────────────────────────────
    {
        path: '/:pathMatch(.*)*',
        name: 'not-found',
        component: NotFoundPage,
        meta: { public: true },
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior(_to, _from, savedPosition) {
        if (savedPosition) return savedPosition
        return { top: 0 }
    },
})

// ── Navigation guard ──────────────────────────────────────────────────────
// Per ТЗ section 4.2: router guard waits for GET /api/auth/me before deciding.
// - authChecked ensures we only call the API once per app session
// - public routes are always allowed
// - unauthenticated users are redirected to /login
// - authenticated users are redirected away from /login to /

router.beforeEach(async (to) => {
    const authStore = useAuthStore()

    // Call checkAuth once on first navigation (after page load / refresh)
    if (!authStore.authChecked) {
        await authStore.checkAuth()
    }

    // Public routes (login, 404) are always accessible
    if (to.meta.public) {
        // If already authenticated and trying to access /login, redirect to home
        if (to.name === 'login' && authStore.isAuthenticated) {
            return { name: 'overview' }
        }
        return true
    }

    // Protected routes — redirect to login if not authenticated
    if (!authStore.isAuthenticated) {
        return {
            name: 'login',
            query: { redirect: to.fullPath !== '/' ? to.fullPath : undefined },
        }
    }

    return true
})

export default router