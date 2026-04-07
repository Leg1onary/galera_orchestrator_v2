<template>
  <div :data-theme="theme" class="app-root">
    <!-- Login / no-layout pages -->
    <router-view v-if="$route.meta.public" />

    <!-- Main layout -->
    <div v-else-if="auth.isAuthenticated" class="app-layout">
      <AppSidebar />
      <div class="app-main">
        <AppHeader />
        <main class="app-content">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" :key="$route.path" />
            </transition>
          </router-view>
        </main>
      </div>
    </div>

    <Toast position="bottom-right" />
    <ConfirmDialog />
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useWebSocket, useIntervalFn, useOnline, useDark, useDocumentVisibility, useTitle } from '@vueuse/core'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'

const auth = useAuthStore()
const cluster = useClusterStore()

const theme = computed(() => cluster.prefs.theme || 'dark')

// ── useTitle — динамический title по статусу кластера ────────────
useTitle(computed(() => {
  const s = cluster.status
  if (!s) return 'Galera Orchestrator v2'
  const health = cluster.clusterHealth === 'ok' ? '●' : cluster.clusterHealth === 'warn' ? '⚠' : '✕'
  return `${health} ${s.cluster_name || 'Cluster'} | Galera Orch v2`
}))

// ── useDark — реактивная тема без ручного DOM-патчинга ───────────
const isDark = useDark({
  selector: '[data-theme]',
  attribute: 'data-theme',
  valueDark: 'dark',
  valueLight: 'light',
})
// Синхронизируем с prefs
watch(() => cluster.prefs.theme, (t) => { isDark.value = t !== 'light' }, { immediate: true })

// ── useOnline — пауза реконнекта при отсутствии сети ─────────────
const isOnline = useOnline()

// ── useDocumentVisibility — пауза polling на свёрнутой вкладке ───
const visibility = useDocumentVisibility()

// ── WebSocket через useWebSocket ─────────────────────────────────
let wsInstance = null

function buildWsUrl() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = auth.token
  return `${proto}://${location.host}/ws/cluster${token ? `?token=${token}` : ''}`
}

function connectWS() {
  if (!auth.isAuthenticated) return

  const { status, data, close } = useWebSocket(buildWsUrl(), {
    autoReconnect: {
      retries: Infinity,
      delay: 2000,
      onFailed() { cluster.wsConnected = false },
    },
    heartbeat: { message: 'ping', interval: 30000, pongTimeout: 5000 },
    onConnected()  { cluster.wsConnected = true },
    onDisconnected() { cluster.wsConnected = false },
    onMessage(_, event) {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'status') cluster.applyStatus(msg)
        if (msg.type === 'event') cluster.addLog(msg.level, msg.message, msg.source)
      } catch {}
    },
  })

  wsInstance = { close }

  // Пауза реконнекта когда нет сети
  watch(isOnline, (online) => {
    if (!online) { cluster.wsConnected = false }
  })
}

function disconnectWS() {
  wsInstance?.close()
  wsInstance = null
}

// ── useIntervalFn — polling fallback ────────────────────────────
const { pause: pausePoll, resume: resumePoll } = useIntervalFn(() => {
  // Пропускаем если вкладка скрыта или WS активен
  if (visibility.value === 'hidden') return
  if (!cluster.wsConnected) cluster.fetchStatus()
}, computed(() => (cluster.prefs.poll_interval || 5) * 1000), { immediate: false })

// Пауза polling когда вкладка скрыта
watch(visibility, (v) => {
  v === 'hidden' ? pausePoll() : resumePoll()
})

onMounted(async () => {
  if (!auth.checked) await auth.checkAuthStatus()
  if (auth.isAuthenticated) {
    await Promise.all([
      cluster.fetchStatus(),
      cluster.fetchContours(),
      cluster.fetchPrefs(),
      cluster.fetchVersion(),
    ])
    connectWS()
    resumePoll()
  }
})

watch(() => auth.isAuthenticated, (v) => {
  if (v) {
    cluster.fetchStatus()
    cluster.fetchContours()
    cluster.fetchPrefs()
    connectWS()
    resumePoll()
  } else {
    disconnectWS()
    pausePoll()
  }
})
</script>

<style>
.app-root { height: 100vh; overflow: hidden; }
</style>
