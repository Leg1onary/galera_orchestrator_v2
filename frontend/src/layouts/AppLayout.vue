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

// Загружаем контуры + системные настройки при монтировании layout
onMounted(async () => {
  await Promise.all([
    clusterStore.loadContours(), // внутри выставляет selectedClusterId
    settingsStore.load(),
  ])
  // После loadContours selectedClusterId уже известен — стартуем WS и events
  if (clusterStore.selectedClusterId) {
    wsStore.connect(clusterStore.selectedClusterId)
    eventsStore.load(clusterStore.selectedClusterId)
  }
})

// При смене кластера пользователем: WS переподключение + инвалидация Vue Query
// ИСПРАВЛЕНО: queryClient НЕ передаётся в store — инвалидация только здесь
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

// Глобальный WS handler — роутит события в нужные stores
// onUnmounted отписывается через возвращённую функцию
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

onUnmounted(() => {
  unsubscribeWs()
})

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
        <!-- Settings и Docs доступны без выбранного кластера (ТЗ 6.1) -->
        <template
            v-if="clusterStore.selectedClusterId || ['settings', 'docs'].includes(String(route.name))"
        >
          <router-view />
        </template>
        <template v-else>
          <div class="no-cluster">
            <p>Выберите кластер в шапке</p>
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
  background: var(--p-surface-ground);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.no-cluster {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--p-text-muted-color);
}
</style>
