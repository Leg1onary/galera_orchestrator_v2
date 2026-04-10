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
      // overflow:hidden убран — header теперь сам скругляет верхние углы
    ].join(';'),
  },
  header: {
    style: [
      'padding: var(--space-5) var(--space-6) var(--space-4)',
      'border-bottom: 1px solid var(--color-border)',
      'display: flex',
      'align-items: center',
      'gap: var(--space-3)',
      // Скругляем только верхние углы, без градиента
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
      'color: var(--color-text-muted)',
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
      // Скругляем только нижние углы
      'border-radius: 0 0 var(--radius-xl) var(--radius-xl)',
    ].join(';'),
  },
  rejectButton: {
    root: {
      // !important через style не работает — используем min-height + padding напрямую
      // PrimeVue сбрасывает padding кнопок через свои классы, поэтому задаём через class
      class: 'confirm-btn-reject',
    },
  },
  acceptButton: {
    root: {
      class: 'confirm-btn-accept',
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

<style>
/* Унифицированные стили кнопок диалога — глобальные (без scoped),
   чтобы перекрыть PrimeVue specificity */
.confirm-btn-reject.p-button {
  background: transparent !important;
  border: 1px solid var(--color-border) !important;
  color: var(--color-text-muted) !important;
  border-radius: var(--radius-md) !important;
  padding: 10px 24px !important;
  font-size: var(--text-sm) !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease !important;
  box-shadow: none !important;
}
.confirm-btn-reject.p-button:hover {
  background: var(--color-surface-offset) !important;
  border-color: var(--color-text-faint) !important;
  color: var(--color-text) !important;
}

.confirm-btn-accept.p-button {
  background: linear-gradient(135deg, var(--color-error) 0%, color-mix(in oklch, var(--color-error) 75%, var(--color-warning)) 100%) !important;
  border: 1px solid var(--color-error) !important;
  color: #fff !important;
  border-radius: var(--radius-md) !important;
  padding: 10px 24px !important;
  font-size: var(--text-sm) !important;
  font-weight: 700 !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 2px 10px color-mix(in oklch, var(--color-error) 45%, transparent) !important;
  transition: filter 160ms ease, box-shadow 160ms ease !important;
}
.confirm-btn-accept.p-button:hover {
  filter: brightness(1.12) !important;
  box-shadow: 0 4px 16px color-mix(in oklch, var(--color-error) 55%, transparent) !important;
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
  overflow-y: auto;
  padding: var(--space-6);
  min-height: 0;
}
</style>
