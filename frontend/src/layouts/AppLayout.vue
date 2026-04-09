<!-- ТЗ раздел 6.2–6.4: Header + Sidebar + Footer + <slot> -->
<!-- Монтирует WS при выборе кластера, инвалидирует Vue Query при смене -->
<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'
import { useWsStore, onWsEvent } from '@/stores/ws'
import { useOperationsStore } from '@/stores/operations'
import { useEventsStore } from '@/stores/events'
import { useSettingsStore } from '@/stores/settings'
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

// Загружаем контуры + системные настройки при монтировании layout
onMounted(async () => {
  await Promise.all([
    clusterStore.loadContours(),
    settingsStore.load(),
  ])
})

// При смене кластера: WS переподключение + инвалидация Vue Query
watch(
    () => clusterStore.selectedClusterId,
    (clusterId, prevId) => {
      if (!clusterId) return

      // Инвалидируем все cluster-scoped запросы (ТЗ 6.2)
      queryClient.invalidateQueries({ queryKey: ['cluster', prevId] })
      queryClient.invalidateQueries({ queryKey: ['cluster', clusterId] })

      // Переподключаем WS на новый кластер
      wsStore.connect(clusterId)

      // Загружаем event log для нового кластера
      eventsStore.load(clusterId)
    },
    { immediate: true }
)

// Глобальный WS handler — роутит события в нужные stores
onWsEvent((event) => {
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

      // node_state_changed и arbitrator_state_changed инвалидируют status-запрос
    case 'node_state_changed':
    case 'arbitrator_state_changed':
      queryClient.invalidateQueries({
        queryKey: ['cluster', clusterStore.selectedClusterId, 'status'],
      })
      break
  }
})

async function handleLogout() {
  wsStore.disconnect()
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
        @select-contour="clusterStore.selectContour"
        @select-cluster="(id) => clusterStore.selectCluster(id, queryClient)"
        @logout="handleLogout"
    />

    <div class="app-body">
      <AppSidebar />

      <main class="app-main">
        <!-- Не рендерим контент пока кластер не выбран -->
        <template v-if="clusterStore.selectedClusterId">
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
  background: var(--surface-ground);
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
  color: var(--text-color-secondary);
}
</style>