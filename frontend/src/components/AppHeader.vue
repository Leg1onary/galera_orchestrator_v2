<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useAuthStore }    from '@/stores/auth'
import { useWsStore }      from '@/stores/ws'
import { useQueryClient }  from '@tanstack/vue-query'

const route        = useRoute()
const router       = useRouter()
const clusterStore = useClusterStore()
const authStore    = useAuthStore()
const wsStore      = useWsStore()
const qc           = useQueryClient()

// ─── Page title ───────────────────────────────────────────────────────────────
const PAGE_TITLES: Record<string, string> = {
  overview:    'Overview',
  nodes:       'Nodes',
  topology:    'Topology',
  recovery:    'Recovery',
  maintenance: 'Maintenance',
  diagnostics: 'Diagnostics',
  settings:    'Settings',
  docs:        'Docs',
}
const PAGE_ICONS: Record<string, string> = {
  overview:    'pi-chart-bar',
  nodes:       'pi-server',
  topology:    'pi-sitemap',
  recovery:    'pi-replay',
  maintenance: 'pi-wrench',
  diagnostics: 'pi-search',
  settings:    'pi-sliders-h',
  docs:        'pi-book',
}
const pageName = computed(() => PAGE_TITLES[String(route.name)] ?? String(route.name ?? ''))
const pageIcon = computed(() => PAGE_ICONS[String(route.name)] ?? 'pi-circle')

// ─── Cluster dropdown ────────────────────────────────────────────────────────
const clusters         = computed(() => clusterStore.clustersForContour)
const selectedCluster  = computed(() => clusterStore.selectedCluster)
const selectedContour  = computed(() => clusterStore.contours.find(c => c.id === clusterStore.selectedContourId) ?? null)
const clusterOpen      = ref(false)

function selectCluster(id: number) {
  clusterStore.selectCluster(id, qc)
  clusterOpen.value = false
}
function toggleClusterDropdown() {
  if (clusters.value.length <= 1) return
  clusterOpen.value = !clusterOpen.value
}
function onClickOutside(e: MouseEvent) {
  const el = document.getElementById('cluster-dropdown-root')
  if (el && !el.contains(e.target as Node)) clusterOpen.value = false
}
function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    clusterOpen.value = false
    userOpen.value = false
  }
}
onMounted(() => {
  document.addEventListener('mousedown', onClickOutside)
  document.addEventListener('mousedown', onUserClickOutside)
  document.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onClickOutside)
  document.removeEventListener('mousedown', onUserClickOutside)
  document.removeEventListener('keydown', onKeyDown)
})

// ─── Cluster health ──────────────────────────────────────────────────────────
const clusterStatus = computed(() => selectedCluster.value?.status ?? null)
const healthLabel = computed(() => {
  const m: Record<string, string> = { healthy: 'Healthy', degraded: 'Degraded', critical: 'Critical' }
  return clusterStatus.value ? m[clusterStatus.value] ?? clusterStatus.value : null
})

// ─── WebSocket status ────────────────────────────────────────────────────────
const wsStatus  = computed(() => wsStore.connectionStatus)
const wsPolling = computed(() => wsStore.pollingFallbackActive)
const wsLabel   = computed(() => {
  if (wsStatus.value === 'connected')    return 'Live'
  if (wsStatus.value === 'reconnecting') return 'Reconnecting…'
  if (wsStatus.value === 'connecting')   return 'Connecting…'
  if (wsPolling.value)                   return 'Polling'
  return 'Offline'
})

// ─── User / logout ───────────────────────────────────────────────────────────
const username = computed(() => authStore.username ?? 'user')
const initials = computed(() => username.value.slice(0, 2).toUpperCase())
// role не хранится в authStore (ТЗ не предусматривает роли) — fallback 'Administrator'
const userRole = computed(() => 'Administrator')
const userOpen = ref(false)

function toggleUserMenu() { userOpen.value = !userOpen.value }
function onUserClickOutside(e: MouseEvent) {
  const el = document.getElementById('user-menu-root')
  if (el && !el.contains(e.target as Node)) userOpen.value = false
}

async function logout() {
  userOpen.value = false
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="app-header">

    <!-- ══ LEFT: page title ══════════════════════════════════════════════ -->
    <div class="header-page-title">
      <i :class="['pi', pageIcon, 'page-icon']" aria-hidden="true" />
      <span class="page-name">{{ pageName }}</span>
    </div>

    <!-- ══ RIGHT: status + cluster + user ════════════════════════════════ -->
    <div class="header-right">

      <!-- ── WS live indicator ─────────────────────────────────────── -->
      <div
        :class="['ws-pill', `ws-pill--${wsStatus}`, wsPolling ? 'ws-pill--polling' : '']"
        v-tooltip.bottom="wsPolling ? 'WebSocket offline — polling fallback active' : `WebSocket: ${wsLabel}`"
      >
        <span class="ws-dot" />
        <span class="ws-label">{{ wsLabel }}</span>
      </div>

      <!-- ── Cluster health badge ───────────────────────────────────── -->
      <div
        v-if="clusterStatus"
        :class="['health-badge', `health-badge--${clusterStatus}`]"
        v-tooltip.bottom="`Cluster status: ${healthLabel}`"
      >
        <span class="health-dot" />
        <span class="health-label">{{ healthLabel }}</span>
      </div>

      <div class="header-divider" />

      <!-- ── Cluster + contour block ───────────────────────────────── -->
      <div class="cluster-block">
        <!-- Contour breadcrumb -->
        <div v-if="selectedContour" class="contour-crumb">
          <span class="contour-crumb__label">Contour:</span>
          <span class="contour-crumb__name">{{ selectedContour.name }}</span>
        </div>

        <!-- Cluster dropdown -->
        <div
          id="cluster-dropdown-root"
          class="cluster-dropdown"
          :class="{ 'is-open': clusterOpen, 'is-locked': clusterStore.isClusterLocked }"
        >
          <button
            class="cluster-trigger"
            @click="toggleClusterDropdown"
            :disabled="clusters.length <= 1"
            v-tooltip.bottom="clusterStore.isClusterLocked ? 'Cluster is locked — operation in progress' : undefined"
            aria-haspopup="listbox"
            :aria-expanded="clusterOpen"
          >
            <i v-if="clusterStore.isClusterLocked" class="pi pi-lock trigger-lock-icon" />
            <i v-else class="pi pi-database trigger-db-icon" />
            <span class="trigger-name">{{ selectedCluster?.name ?? 'No cluster' }}</span>
            <i v-if="clusters.length > 1" :class="['pi', clusterOpen ? 'pi-chevron-up' : 'pi-chevron-down', 'trigger-chevron']" />
          </button>

          <Transition name="dropdown">
            <ul v-if="clusterOpen" class="cluster-list" role="listbox">
              <li
                v-for="cl in clusters"
                :key="cl.id"
                class="cluster-item"
                :class="{ 'is-selected': cl.id === selectedCluster?.id }"
                role="option"
                :aria-selected="cl.id === selectedCluster?.id"
                @click="selectCluster(cl.id)"
              >
                <span :class="['cl-status-dot', `cl-status-dot--${cl.status ?? 'unknown'}`]" />
                <span class="cl-name">{{ cl.name }}</span>
                <span v-if="cl.active_operation" class="cl-op-badge">
                  <i class="pi pi-spin pi-spinner" />
                </span>
                <i v-if="cl.id === selectedCluster?.id" class="pi pi-check cl-check" />
              </li>
            </ul>
          </Transition>
        </div>
      </div>

      <div class="header-divider" />

      <!-- ── User chip ──────────────────────────────────────────────── -->
      <div id="user-menu-root" class="user-chip-wrap">
        <button class="user-chip" @click="toggleUserMenu" :aria-expanded="userOpen">
          <span class="user-avatar">{{ initials }}</span>
          <i :class="['pi', userOpen ? 'pi-chevron-up' : 'pi-chevron-down', 'user-chevron']" />
        </button>

        <Transition name="dropdown">
          <div v-if="userOpen" class="user-menu">
            <div class="user-menu-header">
              <span class="user-menu-avatar">{{ initials }}</span>
              <div>
                <div class="user-menu-name">{{ username }}</div>
                <div class="user-menu-role">{{ userRole }}</div>
              </div>
            </div>
            <div class="user-menu-divider" />
            <button class="user-menu-item user-menu-item--danger" @click="logout">
              <i class="pi pi-sign-out" />
              Sign out
            </button>
          </div>
        </Transition>
      </div>

    </div>
  </header>
</template>

<style scoped>
/* ════════════════════════════════════════════════════════
   LAYOUT
════════════════════════════════════════════════════════ */
.app-header {
  height: var(--header-height, 56px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  border-bottom: 1px solid rgba(255,255,255,0.055);
  background: rgba(12,13,16,0.85);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  position: sticky;
  top: 0;
  z-index: 40;
  flex-shrink: 0;
  gap: var(--space-4);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.04),
    0 4px 24px rgba(0,0,0,0.35);
}

/* ════════════════════════════════════════════════════════
   PAGE TITLE
════════════════════════════════════════════════════════ */
.header-page-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}
.page-icon {
  font-size: 0.875rem;
  color: var(--color-text-faint);
  opacity: 0.7;
}
.page-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

/* ════════════════════════════════════════════════════════
   RIGHT SECTION
════════════════════════════════════════════════════════ */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(255,255,255,0.07);
  margin: 0 var(--space-1);
  flex-shrink: 0;
}

/* ════════════════════════════════════════════════════════
   WS PILL
════════════════════════════════════════════════════════ */
.ws-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px 3px 7px;
  border-radius: 99px;
  border: 1px solid transparent;
  font-size: 0.72rem;
  font-family: var(--font-mono, monospace);
  font-weight: 500;
  letter-spacing: 0.03em;
  transition: all 250ms;
  cursor: default;
  white-space: nowrap;
}
.ws-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ws-pill--connected {
  background: color-mix(in oklch, var(--color-synced) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-synced) 18%, transparent);
  color: var(--color-synced);
}
.ws-pill--connected .ws-dot {
  background: var(--color-synced);
  box-shadow: 0 0 6px color-mix(in oklch, var(--color-synced) 70%, transparent);
  animation: ws-pulse 2.5s ease-in-out infinite;
}
.ws-pill--reconnecting,
.ws-pill--connecting {
  background: color-mix(in oklch, var(--color-warning) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-warning) 18%, transparent);
  color: var(--color-warning);
}
.ws-pill--reconnecting .ws-dot,
.ws-pill--connecting .ws-dot {
  background: var(--color-warning);
  animation: blink-fast 0.8s ease-in-out infinite;
}
.ws-pill--disconnected {
  background: color-mix(in oklch, var(--color-offline) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-offline) 15%, transparent);
  color: var(--color-text-faint);
}
.ws-pill--disconnected .ws-dot { background: var(--color-text-faint); }
.ws-pill--polling {
  background: color-mix(in oklch, var(--color-donor) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-donor) 18%, transparent);
  color: var(--color-donor);
}
.ws-pill--polling .ws-dot {
  background: var(--color-donor);
  animation: blink-fast 1.2s ease-in-out infinite;
}
@keyframes ws-pulse {
  0%, 100% { box-shadow: 0 0 6px color-mix(in oklch, var(--color-synced) 70%, transparent); opacity: 1; }
  50%       { box-shadow: 0 0 2px color-mix(in oklch, var(--color-synced) 20%, transparent); opacity: 0.6; }
}
@keyframes blink-fast {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.2; }
}
.ws-label { line-height: 1; }

/* ════════════════════════════════════════════════════════
   HEALTH BADGE
════════════════════════════════════════════════════════ */
.health-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px 3px 7px;
  border-radius: 99px;
  border: 1px solid transparent;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: default;
  white-space: nowrap;
}
.health-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.health-badge--healthy {
  background: color-mix(in oklch, var(--color-synced) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-synced) 18%, transparent);
  color: var(--color-synced);
}
.health-badge--healthy .health-dot {
  background: var(--color-synced);
  box-shadow: 0 0 6px color-mix(in oklch, var(--color-synced) 65%, transparent);
}
.health-badge--degraded {
  background: color-mix(in oklch, var(--color-warning) 7%, transparent);
  border-color: color-mix(in oklch, var(--color-warning) 18%, transparent);
  color: var(--color-warning);
}
.health-badge--degraded .health-dot {
  background: var(--color-warning);
  box-shadow: 0 0 6px color-mix(in oklch, var(--color-warning) 55%, transparent);
  animation: blink-fast 1.8s ease-in-out infinite;
}
.health-badge--critical {
  background: color-mix(in oklch, var(--color-offline) 9%, transparent);
  border-color: color-mix(in oklch, var(--color-offline) 22%, transparent);
  color: var(--color-offline);
}
.health-badge--critical .health-dot {
  background: var(--color-offline);
  box-shadow: 0 0 8px color-mix(in oklch, var(--color-offline) 70%, transparent);
  animation: blink-fast 0.9s ease-in-out infinite;
}
.health-label { line-height: 1; }

/* ════════════════════════════════════════════════════════
   CLUSTER BLOCK (contour crumb + dropdown)
════════════════════════════════════════════════════════ */
.cluster-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.contour-crumb {
  display: flex;
  align-items: center;
  gap: 4px;
  line-height: 1;
}
.contour-crumb__label {
  font-size: 0.62rem;
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
}
.contour-crumb__name {
  font-size: 0.62rem;
  color: var(--color-text-muted);
  font-family: var(--font-mono, monospace);
  font-weight: 600;
  letter-spacing: 0.05em;
}

.cluster-dropdown { position: relative; }

.cluster-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px 5px 9px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: var(--color-text-muted);
  font-size: 0.825rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms;
  white-space: nowrap;
  min-width: 130px;
}
.cluster-trigger:hover:not(:disabled) {
  background: rgba(255,255,255,0.07);
  border-color: rgba(255,255,255,0.13);
  color: var(--color-text);
}
.cluster-trigger:disabled { cursor: default; opacity: 0.7; }
.cluster-dropdown.is-locked .cluster-trigger {
  border-color: color-mix(in oklch, var(--color-warning) 25%, transparent);
  background: color-mix(in oklch, var(--color-warning) 5%, transparent);
}
.trigger-lock-icon { color: var(--color-warning); font-size: 0.75rem; }
.trigger-db-icon   { color: var(--color-synced); font-size: 0.8rem; opacity: 0.7; }
.trigger-name      { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; }
.trigger-chevron   { font-size: 0.65rem; color: var(--color-text-faint); flex-shrink: 0; }

.cluster-list {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 200px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 4px;
  list-style: none;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.3);
  z-index: 100;
}
.cluster-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 7px;
  font-size: 0.825rem;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 180ms;
}
.cluster-item:hover { background: rgba(255,255,255,0.06); color: var(--color-text); }
.cluster-item.is-selected {
  background: color-mix(in oklch, var(--color-synced) 7%, transparent);
  color: var(--color-text);
}
.cl-name  { flex: 1; font-weight: 500; }
.cl-check { font-size: 0.7rem; color: var(--color-synced); }
.cl-op-badge .pi { font-size: 0.7rem; color: var(--color-warning); }
.cl-status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.cl-status-dot--healthy  { background: var(--color-synced);  box-shadow: 0 0 5px color-mix(in oklch, var(--color-synced) 60%, transparent); }
.cl-status-dot--degraded { background: var(--color-warning); box-shadow: 0 0 5px color-mix(in oklch, var(--color-warning) 50%, transparent); }
.cl-status-dot--critical { background: var(--color-offline); box-shadow: 0 0 5px color-mix(in oklch, var(--color-offline) 60%, transparent); }
.cl-status-dot--unknown  { background: var(--color-text-faint); }

/* ════════════════════════════════════════════════════════
   USER CHIP
════════════════════════════════════════════════════════ */
.user-chip-wrap { position: relative; }

.user-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px 4px 5px;
  border-radius: 99px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 200ms;
}
.user-chip:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.14);
}
.user-avatar {
  width: 26px; height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #134e4a 0%, #0f766e 100%);
  border: 1.5px solid color-mix(in oklch, var(--color-synced) 35%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--color-synced);
  letter-spacing: 0.03em;
  flex-shrink: 0;
  line-height: 1;
}
.user-chevron { font-size: 0.6rem; color: var(--color-text-faint); }

.user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.3);
  z-index: 100;
}
.user-menu-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
}
.user-menu-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #134e4a 0%, #0f766e 100%);
  border: 1.5px solid color-mix(in oklch, var(--color-synced) 35%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--color-synced);
  flex-shrink: 0;
  line-height: 1;
}
.user-menu-name { font-size: 0.85rem; font-weight: 600; color: var(--color-text); }
.user-menu-role { font-size: 0.72rem; color: var(--color-text-faint); margin-top: 1px; }
.user-menu-divider { height: 1px; background: var(--color-divider); margin: 4px 0; }
.user-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 7px;
  font-size: 0.825rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 180ms;
  border: none;
  background: none;
  text-align: left;
  color: var(--color-text-faint);
}
.user-menu-item:hover { background: rgba(255,255,255,0.06); color: var(--color-text-muted); }
.user-menu-item--danger:hover {
  background: color-mix(in oklch, var(--color-offline) 8%, transparent);
  color: var(--color-offline);
}
.user-menu-item .pi { font-size: 0.8rem; }

/* ════════════════════════════════════════════════════════
   DROPDOWN TRANSITION
════════════════════════════════════════════════════════ */
.dropdown-enter-active { transition: opacity 180ms ease, transform 180ms cubic-bezier(0.16,1,0.3,1); }
.dropdown-leave-active { transition: opacity 150ms ease, transform 150ms ease; }
.dropdown-enter-from   { opacity: 0; transform: translateY(-6px) scale(0.97); }
.dropdown-leave-to     { opacity: 0; transform: translateY(-4px) scale(0.98); }
</style>
