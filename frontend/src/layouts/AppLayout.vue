<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useWsStore }      from '@/stores/ws'
import AppHeader  from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppFooter  from '@/components/AppFooter.vue'

const route        = useRoute()
const clusterStore = useClusterStore()
const wsStore      = useWsStore()

// Загружаем контуры при монтировании layout (один раз за сессию).
// loadContours внутри вызывает loadClusters + восстанавливает выбор из localStorage.
clusterStore.loadContours()

// WS: подключаемся при смене кластера
watch(
  () => clusterStore.selectedClusterId,
  (id) => {
    if (id != null) wsStore.connect(id)
    else wsStore.disconnect()
  },
  { immediate: true }
)

onUnmounted(() => wsStore.disconnect())

// Sidebar collapse
const sidebarCollapsed = ref<boolean>(
  JSON.parse(localStorage.getItem('sidebar-collapsed') ?? 'false')
)
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed.value))
}

const showLayout = computed(
  () => route.name !== 'login' && route.name !== 'not-found'
)
</script>

<template>
  <div v-if="showLayout" class="app-shell">
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <div class="app-main" :class="{ 'app-main--collapsed': sidebarCollapsed }">
      <AppHeader />
      <main class="app-content">
        <RouterView />
      </main>
      <AppFooter />
    </div>
  </div>
  <RouterView v-else />

  <!-- Global overlays -->
  <ConfirmDialog />
  <Toast position="bottom-right" />
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100dvh;
  background: var(--color-bg);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left 240ms cubic-bezier(0.16, 1, 0.3, 1);
}

.app-main--collapsed {
  margin-left: var(--sidebar-width-collapsed);
}

.app-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  min-height: 0;
}
</style>
