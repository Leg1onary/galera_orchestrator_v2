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

clusterStore.loadContours()

watch(
  () => clusterStore.selectedClusterId,
  (id) => {
    if (id != null) wsStore.connect(id)
    else wsStore.disconnect()
  },
  { immediate: true }
)

onUnmounted(() => wsStore.disconnect())

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

const confirmDialogPT = {
  root: { style: 'font-family: var(--font-body, sans-serif)' },
  mask: {
    style: [
      'background: oklch(0 0 0 / 0.6)',
      'backdrop-filter: blur(6px)',
      '-webkit-backdrop-filter: blur(6px)',
    ].join(';'),
  },
  dialog: {
    style: [
      'background: var(--color-surface)',
      'border: 1px solid var(--color-border)',
      'border-top: 1px solid color-mix(in oklch, var(--color-border) 60%, white)',
      'border-radius: var(--radius-xl)',
      'box-shadow: 0 2px 4px oklch(0 0 0 / 0.3), 0 16px 48px oklch(0 0 0 / 0.45), 0 0 0 1px oklch(from var(--color-error) l c h / 0.08)',
      'padding: 0',
      'min-width: 340px',
      'max-width: 440px',
      'width: 90vw',
    ].join(';'),
  },
  header: {
    style: [
      'padding: var(--space-5) var(--space-6) var(--space-4)',
      'border-bottom: 1px solid var(--color-border)',
      'display: flex',
      'align-items: center',
      'gap: var(--space-3)',
      'border-radius: var(--radius-xl) var(--radius-xl) 0 0',
      'background: var(--color-surface-2)',
    ].join(';'),
  },
  title: {
    style: [
      'font-size: var(--text-base)',
      'font-weight: 700',
      'color: var(--color-text)',
      'letter-spacing: -0.02em',
    ].join(';'),
  },
  content: {
    style: [
      'padding: var(--space-6) var(--space-6) var(--space-5)',
      'font-size: var(--text-sm)',
      'line-height: 1.6',
      'display: flex',
      'align-items: flex-start',
      'gap: var(--space-4)',
    ].join(';'),
  },
  icon: {
    style: [
      'color: var(--color-warning)',
      'font-size: 1.4rem',
      'flex-shrink: 0',
      'margin-top: 2px',
      'filter: drop-shadow(0 0 6px color-mix(in oklch, var(--color-warning) 55%, transparent))',
    ].join(';'),
  },
  message: {
    style: 'flex: 1; color: var(--color-text); font-size: var(--text-sm); font-weight: 500',
  },
  footer: {
    style: [
      'padding: var(--space-4) var(--space-6) var(--space-5)',
      'display: flex',
      'justify-content: flex-end',
      'gap: var(--space-3)',
      'border-top: 1px solid var(--color-border)',
      'background: linear-gradient(0deg, var(--color-surface-offset) 0%, var(--color-surface) 100%)',
      'border-radius: 0 0 var(--radius-xl) var(--radius-xl)',
    ].join(';'),
  },
  rejectButton: {
    root: {
      style: 'padding: 10px 24px !important; font-size: var(--text-sm) !important; font-weight: 600 !important;',
    },
  },
  acceptButton: {
    root: {
      style: 'padding: 10px 24px !important; font-size: var(--text-sm) !important; font-weight: 700 !important;',
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
  <ConfirmDialog :draggable="false" :pt="confirmDialogPT" />
</template>

<style>
[data-pc-section="footer"] [data-pc-section="root"].p-button {
  padding: 10px 24px !important;
  font-size: var(--text-sm) !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  border-radius: var(--radius-md) !important;
  min-height: unset !important;
}
</style>

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
  /*
    overflow-y: auto  +  overflow-x: visible — невалидная комбинация по CSS-спеке:
    когда одна ось не visible, вторая тоже не может быть visible, браузер
    принудительно делает её auto → контент обрезается.

    Решение: скроллим только по Y, по X позволяем контенту вытекать наружу
    через overflow-x: clip (не создаёт scroll-контейнер, не обрезает sticky).
  */
  overflow-y: auto;
  overflow-x: clip;
  padding: var(--space-6);
  min-height: 0;
  /* Гарантируем что дочерние flex/grid не схлопываются */
  width: 100%;
  min-width: 0;
}
</style>
