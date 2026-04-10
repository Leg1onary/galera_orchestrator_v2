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
      // Subtle top-edge highlight — gives depth on dark bg
      'border: 1px solid var(--color-border)',
      'border-top: 1px solid color-mix(in oklch, var(--color-border) 60%, white)',
      'border-radius: var(--radius-xl)',
      // Layered shadow: contact shadow + wide ambient + faint red glow
      'box-shadow: 0 2px 4px oklch(0 0 0 / 0.3), 0 16px 48px oklch(0 0 0 / 0.45), 0 0 0 1px oklch(from var(--color-error) l c h / 0.08)',
      'padding: 0',
      'min-width: 340px',
      'max-width: 440px',
      'width: 90vw',
      'overflow: hidden',
    ].join(';'),
  },
  header: {
    style: [
      'padding: var(--space-5) var(--space-6) var(--space-4)',
      'border-bottom: 1px solid var(--color-border)',
      'display: flex',
      'align-items: center',
      'gap: var(--space-3)',
      // Subtle surface gradient on header
      'background: linear-gradient(180deg, var(--color-surface-2) 0%, var(--color-surface) 100%)',
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
    // Larger warning icon with amber glow
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
    ].join(';'),
  },
  rejectButton: {
    root: {
      style: [
        'background: transparent',
        'border: 1px solid var(--color-border)',
        'color: var(--color-text-muted)',
        'border-radius: var(--radius-md)',
        // Bigger padding
        'padding: 10px var(--space-6)',
        'font-size: var(--text-sm)',
        'font-weight: 600',
        'cursor: pointer',
        'letter-spacing: 0.01em',
        'transition: background 160ms ease, border-color 160ms ease, color 160ms ease',
      ].join(';'),
    },
  },
  acceptButton: {
    root: {
      style: [
        // Gradient on accept for the "wow" moment
        'background: linear-gradient(135deg, var(--color-error) 0%, color-mix(in oklch, var(--color-error) 75%, var(--color-warning)) 100%)',
        'border: 1px solid var(--color-error)',
        'color: #fff',
        'border-radius: var(--radius-md)',
        'padding: 10px var(--space-6)',
        'font-size: var(--text-sm)',
        'font-weight: 700',
        'cursor: pointer',
        'letter-spacing: 0.01em',
        'box-shadow: 0 2px 8px color-mix(in oklch, var(--color-error) 45%, transparent)',
        'transition: box-shadow 160ms ease, filter 160ms ease',
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
