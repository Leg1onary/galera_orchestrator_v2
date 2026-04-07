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
import { computed, onMounted, onUnmounted, watch } from 'vue'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'

const auth = useAuthStore()
const cluster = useClusterStore()

const theme = computed(() => cluster.prefs.theme || 'dark')

// WebSocket
let ws = null
let wsRetryTimeout = null
let retryDelay = 2000

function connectWS() {
  if (!auth.isAuthenticated) return
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = auth.token
  const url = `${proto}://${location.host}/ws/cluster${token ? `?token=${token}` : ''}`

  ws = new WebSocket(url)
  ws.onopen = () => { cluster.wsConnected = true; retryDelay = 2000 }
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data)
      if (msg.type === 'status') cluster.applyStatus(msg)
      if (msg.type === 'event') cluster.addLog(msg.level, msg.message, msg.source)
    } catch {}
  }
  ws.onerror = () => { cluster.wsConnected = false }
  ws.onclose = () => {
    cluster.wsConnected = false
    wsRetryTimeout = setTimeout(() => {
      retryDelay = Math.min(retryDelay * 1.5, 30000)
      connectWS()
    }, retryDelay)
  }
}

function disconnectWS() {
  if (ws) { ws.close(); ws = null }
  if (wsRetryTimeout) clearTimeout(wsRetryTimeout)
}

// Poll fallback
let pollInterval = null
function startPoll() {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(() => {
    if (!cluster.wsConnected) cluster.fetchStatus()
  }, (cluster.prefs.poll_interval || 5) * 1000)
}

watch(() => cluster.prefs.poll_interval, startPoll)

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
    startPoll()
  }
})

onUnmounted(() => {
  disconnectWS()
  if (pollInterval) clearInterval(pollInterval)
})

watch(() => auth.isAuthenticated, (v) => {
  if (v) {
    cluster.fetchStatus()
    cluster.fetchContours()
    cluster.fetchPrefs()
    connectWS()
    startPoll()
  } else {
    disconnectWS()
    if (pollInterval) clearInterval(pollInterval)
  }
})
</script>

<style>
.app-root { height: 100vh; overflow: hidden; }
</style>
