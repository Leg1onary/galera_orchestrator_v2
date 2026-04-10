<!-- layouts/AppLayout.vue -->
<!-- ТЗ раздел 6.2–6.4: Header + Sidebar + Footer + RouterView -->
<!-- Монтирует WS при выборе кластера, инвалидирует Vue Query при смене -->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQueryClient, useQuery } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'
import { useWsStore, onWsEvent } from '@/stores/ws'
import { useOperationsStore } from '@/stores/operations'
import { useEventsStore } from '@/stores/events'
import { useSettingsStore } from '@/stores/settings'
import { api } from '@/api/client'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppFooter from '@/components/AppFooter.vue'

const auth = useAuthStore()
const clusterStore = useClusterStore()
const wsStore = useWsStore()
const operationsStore = useOperationsStore()
const eventsStore = useEventsStore()
const settingsStore = useSettingsStore()
const queryClient = useQueryClient()
const router = useRouter()
const route = useRoute()

const { data: clusterStatusData } = useQuery({
  queryKey: computed(() => ['cluster', clusterStore.selectedClusterId, 'status']),
  queryFn: () => api.get(`/api/clusters/${clusterStore.selectedClusterId}/status`).then(r => r.data),
  enabled: computed(() => !!clusterStore.selectedClusterId),
  refetchInterval: computed(() => settingsStore.pollingIntervalSec * 1000),
  staleTime: 5_000,
})

onMounted(async () => {
  await Promise.all([
    clusterStore.loadContours(),
    settingsStore.load(),
  ])
  if (clusterStore.selectedClusterId) {
    wsStore.connect(clusterStore.selectedClusterId)
    eventsStore.load(clusterStore.selectedClusterId)
  }
})

watch(
  () => clusterStore.selectedClusterId,
  (clusterId, prevId) => {
    if (!clusterId) return
    if (prevId) {
      queryClient.invalidateQueries({ queryKey: ['cluster', prevId] })
    }
    queryClient.invalidateQueries({ queryKey: ['cluster', clusterId] })
    wsStore.connect(clusterId)
    eventsStore.load(clusterId)
  }
)

const unsubscribeWs = onWsEvent((event) => {
  if (!clusterStore.selectedClusterId) return
  switch (event.event) {
    case 'operation_started':
    case 'operation_progress':
    case 'operation_finished':
      operationsStore.handleWsEvent(event)
      break
    case 'log_entry':
      eventsStore.appendFromWs(event.payload as any)
      break
    case 'node_state_changed':
    case 'arbitrator_state_changed':
      queryClient.invalidateQueries({
        queryKey: ['cluster', clusterStore.selectedClusterId, 'status'],
      })
      break
  }
})

onUnmounted(() => { unsubscribeWs() })

async function handleLogout() {
  wsStore.disconnect()
  queryClient.clear()
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-layout">
    <AppHeader
        :username="auth.username"
        :contours="clusterStore.contours"
        :clusters="clusterStore.clustersForContour"
        :selected-contour-id="clusterStore.selectedContourId"
        :selected-cluster-id="clusterStore.selectedClusterId"
        :cluster-status="clusterStatusData"
        @select-contour="clusterStore.selectContour"
        @select-cluster="(id) => clusterStore.selectCluster(id)"
        @logout="handleLogout"
    />

    <div class="app-body">
      <AppSidebar />

      <main class="app-main">
        <template
            v-if="clusterStore.selectedClusterId || ['settings', 'docs'].includes(String(route.name))"
        >
          <router-view />
        </template>
        <template v-else>
          <div class="no-cluster">
            <div class="no-cluster-inner">
              <svg viewBox="0 0 48 48" fill="none" class="no-cluster-icon" aria-hidden="true">
                <polygon points="24,4 44,14 44,34 24,44 4,34 4,14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" opacity="0.3"/>
                <polygon points="24,12 36,18.5 36,29.5 24,36 12,29.5 12,18.5" fill="none" stroke="currentColor" stroke-width="1" stroke-linejoin="round" opacity="0.2"/>
                <circle cx="24" cy="24" r="4" fill="currentColor" opacity="0.4"/>
              </svg>
              <p class="no-cluster-text">Выберите кластер в шапке</p>
            </div>
          </div>
        </template>
      </main>
    </div>

    <AppFooter :ws-status="wsStore.connectionStatus" />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  background: var(--color-bg);
}

.no-cluster {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.no-cluster-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  color: var(--color-text-faint);
}

.no-cluster-icon {
  width: 56px;
  height: 56px;
  color: var(--color-primary);
}

.no-cluster-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
