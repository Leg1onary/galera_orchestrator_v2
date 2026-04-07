import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login',       name: 'Login',       component: () => import('@/pages/LoginPage.vue'),       meta: { public: true } },
  { path: '/',            name: 'Overview',    component: () => import('@/pages/OverviewPage.vue'),     meta: { layout: true } },
  { path: '/nodes',       name: 'Nodes',       component: () => import('@/pages/NodesPage.vue'),        meta: { layout: true } },
  { path: '/topology',    name: 'Topology',    component: () => import('@/pages/TopologyPage.vue'),     meta: { layout: true } },
  { path: '/recovery',    name: 'Recovery',    component: () => import('@/pages/RecoveryPage.vue'),     meta: { layout: true } },
  { path: '/maintenance', name: 'Maintenance', component: () => import('@/pages/MaintenancePage.vue'),  meta: { layout: true } },
  { path: '/diagnostics', name: 'Diagnostics', component: () => import('@/pages/DiagnosticsPage.vue'), meta: { layout: true } },
  { path: '/settings',    name: 'Settings',    component: () => import('@/pages/SettingsPage.vue'),     meta: { layout: true } },
  { path: '/docs',        name: 'Docs',        component: () => import('@/pages/DocsPage.vue'),         meta: { layout: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.checked) await auth.checkAuthStatus()
  if (to.meta.public) return true
  if (!auth.isAuthenticated) return { name: 'Login', query: { redirect: to.fullPath } }
  return true
})

export default router
