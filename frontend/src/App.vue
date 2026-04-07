<template>
  <div class="app-shell" :class="{ 'app-shell--login': $route.name === 'login' }">
    <!-- App shell renders layout, login handled by LoginPage route -->
    <template v-if="$route.name !== 'login'">
      <AppHeader />
      <AppSidebar />
      <main class="app-main">
        <router-view />
      </main>
      <AppFooter />
    </template>
    <template v-else>
      <router-view />
    </template>

    <!-- PrimeVue global services -->
    <Toast position="bottom-right" />
    <ConfirmDialog />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'

import AppHeader  from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppFooter  from '@/components/layout/AppFooter.vue'

import { useAuthStore }    from '@/stores/auth.js'
import { useClusterStore } from '@/stores/cluster.js'

const auth    = useAuthStore()
const cluster = useClusterStore()
const route   = useRoute()

// ── Theme: read from localStorage, apply immediately ──────────────
const LS_THEME = 'galera_theme'
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t)
}
const savedTheme = localStorage.getItem(LS_THEME) || 'dark'
applyTheme(savedTheme)

// ── Poll timer ────────────────────────────────────────────────────
let pollTimer = null

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    if (route.name !== 'login') {
      cluster.fetchStatus()
    }
  }, cluster.pollInterval * 1000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

watch(() => cluster.pollInterval, () => {
  startPolling()
})

// ── Lifecycle ─────────────────────────────────────────────────────
onMounted(async () => {
  // Init auth first
  await auth.init()

  // Sync data mode with backend, then fetch
  await cluster.syncModeWithBackend()
  await cluster.fetchStatus()
  await cluster.fetchGitSha()

  // Load contours for real mode
  await cluster.loadContours()

  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>
