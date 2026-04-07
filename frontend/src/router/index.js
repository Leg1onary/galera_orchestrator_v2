import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    redirect: '/overview',
  },
  {
    path: '/overview',
    name: 'overview',
    component: () => import('@/pages/OverviewPage.vue'),
  },
  {
    path: '/nodes',
    name: 'nodes',
    component: () => import('@/pages/NodesPage.vue'),
  },
  {
    path: '/topology',
    name: 'topology',
    component: () => import('@/pages/TopologyPage.vue'),
  },
  {
    path: '/recovery',
    name: 'recovery',
    component: () => import('@/pages/RecoveryPage.vue'),
  },
  {
    path: '/maintenance',
    name: 'maintenance',
    component: () => import('@/pages/MaintenancePage.vue'),
  },
  {
    path: '/diagnostics',
    name: 'diagnostics',
    component: () => import('@/pages/DiagnosticsPage.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/pages/SettingsPage.vue'),
  },
  {
    path: '/docs',
    name: 'docs',
    component: () => import('@/pages/DocsPage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/overview',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) return next()
  const auth = useAuthStore()
  if (auth.authEnabled && !auth.isLoggedIn) {
    return next({ name: 'login' })
  }
  next()
})

export default router
