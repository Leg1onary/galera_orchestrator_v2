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
onMounted(()  => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))

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
const userOpen = ref(false)

function toggleUserMenu() { userOpen.value = !userOpen.value }
function onUserClickOutside(e: MouseEvent) {
  const el = document.getElementById('user-menu-root')
  if (el && !el.contains(e.target as Node)) userOpen.value = false
}
onMounted(()  => document.addEventListener('mousedown', onUserClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onUserClickOutside))

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

      <!-- ── Cluster dropdown ───────────────────────────────────────── -->
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
                <div class="user-menu-role">Administrator</div>
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
  color: #2dd4bf;
  opacity: 0.85;
}
.page-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #e4e4e7;
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
  background: rgba(74,222,128,0.07);
  border-color: rgba(74,222,128,0.18);
  color: #4ade80;
}
.ws-pill--connected .ws-dot {
  background: #4ade80;
  box-shadow: 0 0 6px rgba(74,222,128,0.7);
  animation: ws-pulse 2.5s ease-in-out infinite;
}
.ws-pill--reconnecting,
.ws-pill--connecting {
  background: rgba(251,191,36,0.07);
  border-color: rgba(251,191,36,0.18);
  color: #fbbf24;
}
.ws-pill--reconnecting .ws-dot,
.ws-pill--connecting .ws-dot {
  background: #fbbf24;
  animation: blink-fast 0.8s ease-in-out infinite;
}
.ws-pill--disconnected {
  background: rgba(248,113,113,0.07);
  border-color: rgba(248,113,113,0.15);
  color: #71717a;
}
.ws-pill--disconnected .ws-dot { background: #52525b; }
.ws-pill--polling {
  background: rgba(251,146,60,0.07);
  border-color: rgba(251,146,60,0.18);
  color: #fb923c;
}
.ws-pill--polling .ws-dot {
  background: #fb923c;
  animation: blink-fast 1.2s ease-in-out infinite;
}
@keyframes ws-pulse {
  0%, 100% { box-shadow: 0 0 6px rgba(74,222,128,0.7); opacity: 1; }
  50%       { box-shadow: 0 0 2px rgba(74,222,128,0.2); opacity: 0.6; }
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
  background: rgba(45,212,191,0.07);
  border-color: rgba(45,212,191,0.18);
  color: #2dd4bf;
}
.health-badge--healthy .health-dot {
  background: #2dd4bf;
  box-shadow: 0 0 6px rgba(45,212,191,0.65);
}
.health-badge--degraded {
  background: rgba(251,191,36,0.07);
  border-color: rgba(251,191,36,0.18);
  color: #fbbf24;
}
.health-badge--degraded .health-dot {
  background: #fbbf24;
  box-shadow: 0 0 6px rgba(251,191,36,0.55);
  animation: blink-fast 1.8s ease-in-out infinite;
}
.health-badge--critical {
  background: rgba(248,113,113,0.09);
  border-color: rgba(248,113,113,0.22);
  color: #f87171;
}
.health-badge--critical .health-dot {
  background: #f87171;
  box-shadow: 0 0 8px rgba(248,113,113,0.7);
  animation: blink-fast 0.9s ease-in-out infinite;
}
.health-label { line-height: 1; }

/* ════════════════════════════════════════════════════════
   CLUSTER DROPDOWN
════════════════════════════════════════════════════════ */
.cluster-dropdown { position: relative; }

.cluster-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px 5px 9px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: #d4d4d8;
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
  color: #f4f4f5;
}
.cluster-trigger:disabled { cursor: default; opacity: 0.7; }
.cluster-dropdown.is-locked .cluster-trigger {
  border-color: rgba(251,191,36,0.25);
  background: rgba(251,191,36,0.05);
}
.trigger-lock-icon { color: #fbbf24; font-size: 0.75rem; }
.trigger-db-icon   { color: #2dd4bf; font-size: 0.8rem; opacity: 0.7; }
.trigger-name      { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; }
.trigger-chevron   { font-size: 0.65rem; color: #52525b; flex-shrink: 0; }

.cluster-list {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 200px;
  background: #16181d;
  border: 1px solid rgba(255,255,255,0.09);
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
  color: #a1a1aa;
  cursor: pointer;
  transition: all 180ms;
}
.cluster-item:hover { background: rgba(255,255,255,0.06); color: #e4e4e7; }
.cluster-item.is-selected { background: rgba(45,212,191,0.07); color: #e4e4e7; }
.cl-name  { flex: 1; font-weight: 500; }
.cl-check { font-size: 0.7rem; color: #2dd4bf; }
.cl-op-badge .pi { font-size: 0.7rem; color: #fbbf24; }
.cl-status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.cl-status-dot--healthy  { background: #4ade80; box-shadow: 0 0 5px rgba(74,222,128,0.6); }
.cl-status-dot--degraded { background: #fbbf24; box-shadow: 0 0 5px rgba(251,191,36,0.5); }
.cl-status-dot--critical { background: #f87171; box-shadow: 0 0 5px rgba(248,113,113,0.6); }
.cl-status-dot--unknown  { background: #3f3f46; }

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
  border: 1.5px solid rgba(45,212,191,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 800;
  color: #2dd4bf;
  letter-spacing: 0.03em;
  flex-shrink: 0;
  line-height: 1;
}
.user-chevron { font-size: 0.6rem; color: #52525b; }

.user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: #16181d;
  border: 1px solid rgba(255,255,255,0.09);
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
  border: 1.5px solid rgba(45,212,191,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  color: #2dd4bf;
  flex-shrink: 0;
  line-height: 1;
}
.user-menu-name { font-size: 0.85rem; font-weight: 600; color: #e4e4e7; }
.user-menu-role { font-size: 0.72rem; color: #52525b; margin-top: 1px; }
.user-menu-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 4px 0; }
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
  color: #71717a;
}
.user-menu-item:hover { background: rgba(255,255,255,0.06); color: #a1a1aa; }
.user-menu-item--danger:hover { background: rgba(248,113,113,0.08); color: #f87171; }
.user-menu-item .pi { font-size: 0.8rem; }

/* ════════════════════════════════════════════════════════
   DROPDOWN TRANSITION
════════════════════════════════════════════════════════ */
.dropdown-enter-active { transition: opacity 180ms ease, transform 180ms cubic-bezier(0.16,1,0.3,1); }
.dropdown-leave-active { transition: opacity 150ms ease, transform 150ms ease; }
.dropdown-enter-from   { opacity: 0; transform: translateY(-6px) scale(0.97); }
.dropdown-leave-to     { opacity: 0; transform: translateY(-4px) scale(0.98); }
</style>
