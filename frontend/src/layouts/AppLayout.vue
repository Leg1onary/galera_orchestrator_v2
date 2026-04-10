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

// ConfirmDialog passthrough — переопределяем стили через PT чтобы использовать наши CSS переменные
const confirmDialogPT = {
  root: { style: 'font-family: var(--font-body, sans-serif)' },
  mask: { style: 'background: oklch(0 0 0 / 0.55); backdrop-filter: blur(2px)' },
  dialog: {
    style: [
      'background: var(--color-surface)',
      'border: 1px solid var(--color-border)',
      'border-radius: var(--radius-xl)',
      'box-shadow: var(--shadow-lg)',
      'padding: 0',
      'min-width: 320px',
      'max-width: 420px',
      'width: 90vw',
    ].join(';'),
  },
  header: {
    style: [
      'padding: var(--space-5) var(--space-6) var(--space-3)',
      'border-bottom: 1px solid var(--color-border)',
      'display: flex',
      'align-items: center',
      'gap: var(--space-3)',
    ].join(';'),
  },
  title: {
    style: [
      'font-size: var(--text-base)',
      'font-weight: 700',
      'color: var(--color-text)',
      'letter-spacing: -0.01em',
    ].join(';'),
  },
  content: {
    style: [
      'padding: var(--space-5) var(--space-6)',
      'color: var(--color-text-muted)',
      'font-size: var(--text-sm)',
      'line-height: 1.55',
      'display: flex',
      'align-items: flex-start',
      'gap: var(--space-3)',
    ].join(';'),
  },
  icon: {
    style: 'color: var(--color-warning); font-size: 1.2rem; flex-shrink: 0; margin-top: 1px',
  },
  message: { style: 'flex: 1' },
  footer: {
    style: [
      'padding: var(--space-3) var(--space-6) var(--space-5)',
      'display: flex',
      'justify-content: flex-end',
      'gap: var(--space-2)',
      'border-top: 1px solid var(--color-border)',
    ].join(';'),
  },
  rejectButton: {
    root: {
      style: [
        'background: transparent',
        'border: 1px solid var(--color-border)',
        'color: var(--color-text-muted)',
        'border-radius: var(--radius-md)',
        'padding: var(--space-2) var(--space-4)',
        'font-size: var(--text-sm)',
        'font-weight: 600',
        'cursor: pointer',
        'transition: background 180ms ease, border-color 180ms ease, color 180ms ease',
      ].join(';'),
    },
  },
  acceptButton: {
    root: {
      style: [
        'background: var(--color-error)',
        'border: 1px solid var(--color-error)',
        'color: #fff',
        'border-radius: var(--radius-md)',
        'padding: var(--space-2) var(--space-4)',
        'font-size: var(--text-sm)',
        'font-weight: 600',
        'cursor: pointer',
        'transition: background 180ms ease',
      ].join(';'),
    },
  },
}
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
  <ConfirmDialog
    :draggable="false"
    :pt="confirmDialogPT"
  />
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
