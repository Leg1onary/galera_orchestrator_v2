<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClusterStore }    from '@/stores/cluster'
import { useOperationsStore } from '@/stores/operations'
import { useWsStore }         from '@/stores/ws'

const props = defineProps<{ collapsed: boolean }>()
const emit  = defineEmits<{ toggle: [] }>()

const route        = useRoute()
const router       = useRouter()
const clusterStore = useClusterStore()
const opsStore     = useOperationsStore()
const wsStore      = useWsStore()

const clusterId = computed(() => clusterStore.selectedCluster?.id ?? 0)

// ── Nav items ───────────────────────────────────────────────────────────────
interface NavItem {
  key:    string
  label:  string
  icon:   string
  to?:    () => object
  group?: string
}

const navItems = computed((): NavItem[] => [
  { key: 'overview',    label: 'Overview',    icon: 'pi-chart-bar',  group: 'monitor', to: () => ({ name: 'overview'    }) },
  { key: 'topology',   label: 'Topology',    icon: 'pi-sitemap',    group: 'monitor', to: () => ({ name: 'topology'    }) },
  { key: 'nodes',      label: 'Nodes',       icon: 'pi-server',     group: 'monitor', to: () => ({ name: 'nodes'       }) },
  { key: 'recovery',   label: 'Recovery',    icon: 'pi-replay',     group: 'ops',     to: () => ({ name: 'recovery'    }) },
  { key: 'maintenance',label: 'Maintenance', icon: 'pi-wrench',     group: 'ops',     to: () => ({ name: 'maintenance' }) },
  { key: 'diagnostics',label: 'Diagnostics', icon: 'pi-search',     group: 'ops',     to: () => ({ name: 'diagnostics' }) },
  { key: 'settings',   label: 'Settings',    icon: 'pi-sliders-h',  group: 'system',  to: () => ({ name: 'settings'   }) },
  { key: 'docs',       label: 'Docs',        icon: 'pi-book',       group: 'system',  to: () => ({ name: 'docs'       }) },
])

const groups: { key: string; label: string }[] = [
  { key: 'monitor', label: 'Monitor' },
  { key: 'ops',     label: 'Operations' },
  { key: 'system',  label: 'System' },
]

function isActive(item: NavItem)  { return route.name === item.key }
function navigate(item: NavItem)  {
  // guard: locked ops items must not trigger navigation
  if (isItemLocked(item)) return
  if (item.to) router.push(item.to())
}

// ── Cluster health ────────────────────────────────────────────────────────────
const clusterStatus = computed(() => clusterStore.selectedCluster?.status ?? null)
const clusterName   = computed(() => clusterStore.selectedCluster?.name ?? null)

const statusColor = computed(() => {
  if (clusterStatus.value === 'healthy')  return '#2dd4bf'
  if (clusterStatus.value === 'degraded') return '#fbbf24'
  if (clusterStatus.value === 'critical') return '#f87171'
  return '#52525b'
})

// ── Active operation ───────────────────────────────────────────────────────────
const activeOp = computed(() =>
  clusterId.value ? opsStore.activeOperation(clusterId.value) : null
)
const isLocked = computed(() =>
  clusterId.value ? opsStore.isLocked(clusterId.value) : false
)

const OP_LABELS: Record<string, string> = {
  'recovery-bootstrap': 'Bootstrap',
  'recovery-rejoin':    'Rejoin',
  'rolling-restart':    'Rolling restart',
  'node-action':        'Node action',
}
const opLabel = computed(() =>
  activeOp.value ? (OP_LABELS[activeOp.value.type] ?? activeOp.value.type) : ''
)

/*
  showOpBar drives v-show (NOT <Transition>+v-if) on the progress bar.

  Why v-show and not <Transition>+v-if:
  Vue's <Transition> holds the element in the DOM during the leave-animation.
  If router.push() fires during that window Vue tries to patch a node the
  router has already removed → "Cannot read properties of null (reading
  'parentNode')". v-show never removes the node from the DOM, so the race
  condition cannot happen. Visual hide/show is handled via CSS opacity.
*/
const showOpBar = computed(() => isLocked.value && !props.collapsed)

// ── Cluster count (footer) ───────────────────────────────────────────────────────
const clusterCount = computed(() => clusterStore.clustersForContour.length)

// ── WS ───────────────────────────────────────────────────────────────────────
const wsStatus = computed(() => wsStore.connectionStatus)

// ── Lock check per item ───────────────────────────────────────────────────────
function isItemLocked(item: NavItem) {
  return isLocked.value && item.group === 'ops'
}
</script>

<template>
  <nav
    class="sidebar"
    :class="{ 'sidebar--collapsed': collapsed }"
    aria-label="Main navigation"
  >

    <!-- ══ HEADER ═════════════════════════════════════════════════════ -->
    <div class="sidebar-header">
      <div class="sidebar-logo" v-show="!collapsed">
        <div class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="10" stroke="#2dd4bf" stroke-width="1.5" opacity="0.25"/>
            <circle cx="11" cy="11" r="6.5" stroke="#2dd4bf" stroke-width="1.5" opacity="0.5"/>
            <circle cx="11" cy="11" r="3" fill="#2dd4bf" opacity="0.9"/>
            <circle cx="11" cy="1.5" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="11" cy="20.5" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="1.5" cy="11" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="20.5" cy="11" r="1.2" fill="#2dd4bf" opacity="0.4"/>
          </svg>
        </div>
        <div class="logo-text-group">
          <span class="logo-text">Galera</span>
          <span class="logo-sub">Orchestrator</span>
        </div>
        <span class="logo-version">v2</span>
      </div>

      <button
        class="toggle-btn"
        :class="{ 'toggle-btn--solo': collapsed }"
        @click="emit('toggle')"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        v-tooltip.right="collapsed ? 'Expand sidebar' : ''"
      >
        <i :class="collapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'" />
      </button>
    </div>

    <!-- ══ CLUSTER PILL ═══════════════════════════════════════════════ -->
    <div
      v-if="clusterStore.selectedCluster"
      class="cluster-pill"
      :class="[
        `cluster-pill--${clusterStatus ?? 'unknown'}`,
        { 'cluster-pill--collapsed': collapsed },
        { 'cluster-pill--locked': isLocked },
      ]"
      :title="collapsed ? clusterName ?? '' : undefined"
    >
      <template v-if="collapsed">
        <span class="cluster-dot" :style="{ background: statusColor, boxShadow: `0 0 7px ${statusColor}99` }" />
      </template>
      <template v-else>
        <div class="cluster-pill-row">
          <span class="cluster-pill__label">cluster</span>
          <span :class="['cluster-status-badge', `cluster-status-badge--${clusterStatus ?? 'unknown'}`]">
            <span class="cluster-status-dot" />
            {{ clusterStatus ?? 'unknown' }}
          </span>
        </div>
        <div class="cluster-pill-row cluster-pill-row--name">
          <i class="pi pi-database cluster-pill-icon" />
          <span class="cluster-pill__name">{{ clusterName }}</span>
          <i v-if="isLocked" class="pi pi-lock cluster-lock-icon" v-tooltip.right="'Operation in progress'" />
        </div>
      </template>
    </div>

    <!-- ══ OPERATION PROGRESS BAR ═══════════════════════════════════════════ -->
    <!-- v-show intentional: avoids Transition+v-if parentNode crash on router.push -->
    <div v-show="showOpBar" class="op-progress-wrap">
      <div class="op-progress-label">
        <i class="pi pi-spin pi-spinner" />
        {{ opLabel }}
      </div>
      <div class="op-progress-track">
        <div class="op-progress-fill" />
      </div>
    </div>

    <!-- ══ NAV ══════════════════════════════════════════════════════════ -->
    <div class="sidebar-nav">
      <template v-for="group in groups" :key="group.key">
        <div v-if="!collapsed" class="nav-section-head">
          <span class="nav-section-line" />
          <span class="nav-section-label">{{ group.label }}</span>
          <span class="nav-section-line" />
        </div>
        <div v-else class="nav-section-sep" />

        <button
          v-for="item in navItems.filter(i => i.group === group.key)"
          :key="item.key"
          class="nav-item"
          :class="{
            'nav-item--active':  isActive(item),
            'nav-item--locked':  isItemLocked(item),
          }"
          @click="navigate(item)"
          v-tooltip.right="collapsed ? item.label : isItemLocked(item) ? 'Locked — operation in progress' : ''"
          :aria-label="item.label"
          :aria-current="isActive(item) ? 'page' : undefined"
        >
          <span v-if="isActive(item)" class="nav-glow-sweep" aria-hidden="true" />
          <i :class="'pi ' + item.icon" class="nav-icon" />
          <span class="nav-label" v-show="!collapsed">{{ item.label }}</span>
          <i v-if="isItemLocked(item) && !collapsed" class="pi pi-lock nav-lock-icon" aria-hidden="true" />
          <span v-if="isActive(item)" class="nav-active-bar" aria-hidden="true" />
        </button>
      </template>
    </div>

    <!-- ══ FOOTER ═════════════════════════════════════════════════════════ -->
    <div class="sidebar-footer" :class="{ 'sidebar-footer--collapsed': collapsed }">
      <template v-if="!collapsed">
        <div class="footer-ws-row">
          <span :class="['footer-ws-dot', `footer-ws-dot--${wsStatus}`]" />
          <span class="footer-ws-label">
            {{ wsStatus === 'connected' ? 'Live' : wsStatus === 'reconnecting' ? 'Reconnecting' : wsStatus === 'connecting' ? 'Connecting' : 'Offline' }}
          </span>
          <span class="footer-cluster-count" v-if="clusterCount > 0">
            {{ clusterCount }} cluster{{ clusterCount !== 1 ? 's' : '' }}
          </span>
        </div>
        <div class="footer-brand"><span>Galera Orchestrator</span></div>
      </template>
      <template v-else>
        <span
          :class="['footer-ws-dot', `footer-ws-dot--${wsStatus}`, 'footer-ws-dot--solo']"
          v-tooltip.right="`WebSocket: ${wsStatus}`"
        />
      </template>
    </div>

  </nav>
</template>

<style scoped>
/* ════════════════════════════════════════════════════════
   SHELL
════════════════════════════════════════════════════════ */
.sidebar {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width, 220px);
  background: #0c0d10;
  border-right: 1px solid rgba(255,255,255,0.055);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width 240ms cubic-bezier(0.16,1,0.3,1);
  overflow: hidden;
}
.sidebar--collapsed { width: var(--sidebar-width-collapsed, 56px); }

/* ════════════════════════════════════════════════════════
   HEADER
════════════════════════════════════════════════════════ */
.sidebar-header {
  height: var(--header-height, 56px);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  gap: var(--space-2);
  min-width: 0;
}
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.logo-icon { flex-shrink: 0; display: flex; align-items: center; }
.logo-text-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  line-height: 1.1;
}
.logo-text {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #e4e4e7;
  white-space: nowrap;
}
.logo-sub {
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #52525b;
  white-space: nowrap;
}
.logo-version {
  font-size: 0.62rem;
  font-weight: 700;
  color: #2dd4bf;
  background: rgba(45,212,191,0.1);
  border: 1px solid rgba(45,212,191,0.22);
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  letter-spacing: 0.04em;
  flex-shrink: 0;
  align-self: flex-start;
  margin-top: 2px;
}
.toggle-btn {
  flex-shrink: 0;
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.03);
  color: #52525b;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 150ms;
}
.toggle-btn:hover { color: #e4e4e7; background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.12); }
.toggle-btn--solo { margin: 0 auto; }

/* ════════════════════════════════════════════════════════
   CLUSTER PILL
════════════════════════════════════════════════════════ */
.cluster-pill {
  margin: var(--space-3) var(--space-3) 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.025);
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  transition: all 200ms ease;
  position: relative;
  overflow: hidden;
}
.cluster-pill--healthy  { border-color: rgba(45,212,191,0.18); }
.cluster-pill--degraded { border-color: rgba(251,191,36,0.18); }
.cluster-pill--critical { border-color: rgba(248,113,113,0.22); }
.cluster-pill--locked   { border-color: rgba(251,191,36,0.22); }
.cluster-pill::before {
  content: '';
  position: absolute;
  left: 0; top: 20%; bottom: 20%;
  width: 2px;
  border-radius: 0 2px 2px 0;
  background: currentColor;
  opacity: 0.5;
}
.cluster-pill--healthy::before  { color: #2dd4bf; }
.cluster-pill--degraded::before { color: #fbbf24; }
.cluster-pill--critical::before { color: #f87171; }
.cluster-pill--unknown::before  { color: #3f3f46; }
.cluster-pill--collapsed {
  margin: var(--space-3) auto 0;
  width: 36px; height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-direction: row;
}
.cluster-pill-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.cluster-pill-row--name { gap: 6px; }
.cluster-pill__label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #52525b;
  font-weight: 600;
}
.cluster-pill__name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #e4e4e7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--font-mono, monospace);
  flex: 1;
  min-width: 0;
}
.cluster-pill-icon { font-size: 0.7rem; color: #52525b; flex-shrink: 0; }
.cluster-lock-icon { font-size: 0.7rem; color: #fbbf24; flex-shrink: 0; }
.cluster-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  animation: pulse-dot 2.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
.cluster-status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 1px 6px 1px 4px;
  border-radius: 99px;
  border: 1px solid transparent;
  white-space: nowrap;
}
.cluster-status-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.cluster-status-badge--healthy  { background: rgba(45,212,191,0.08);  border-color: rgba(45,212,191,0.2);  color: #2dd4bf; }
.cluster-status-badge--healthy .cluster-status-dot  { background: #2dd4bf; box-shadow: 0 0 4px rgba(45,212,191,0.7); }
.cluster-status-badge--degraded { background: rgba(251,191,36,0.08);  border-color: rgba(251,191,36,0.2);  color: #fbbf24; }
.cluster-status-badge--degraded .cluster-status-dot { background: #fbbf24; animation: blink 1.8s ease-in-out infinite; }
.cluster-status-badge--critical { background: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.22); color: #f87171; }
.cluster-status-badge--critical .cluster-status-dot { background: #f87171; animation: blink 0.9s ease-in-out infinite; }
.cluster-status-badge--unknown  { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.08); color: #52525b; }
.cluster-status-badge--unknown .cluster-status-dot  { background: #3f3f46; }
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.2; }
}

/* ════════════════════════════════════════════════════════
   OPERATION PROGRESS BAR
   v-show intentional — never unmounts, avoids parentNode crash on router.push
════════════════════════════════════════════════════════ */
.op-progress-wrap {
  margin: 6px var(--space-3) 0;
  padding: 8px 10px;
  background: rgba(251,191,36,0.04);
  border: 1px solid rgba(251,191,36,0.14);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
  transition: opacity 220ms ease;
}
.op-progress-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: #fbbf24;
  font-family: var(--font-mono, monospace);
  font-weight: 500;
}
.op-progress-label .pi { font-size: 0.65rem; }
.op-progress-track {
  height: 3px;
  background: rgba(251,191,36,0.1);
  border-radius: 99px;
  overflow: hidden;
}
.op-progress-fill {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, transparent, #fbbf24, transparent);
  border-radius: 99px;
  animation: shimmer-bar 1.6s ease-in-out infinite;
}
@keyframes shimmer-bar {
  0%   { transform: translateX(-150%); }
  100% { transform: translateX(350%); }
}

/* ════════════════════════════════════════════════════════
   NAV
════════════════════════════════════════════════════════ */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: 1px;
  scrollbar-width: none;
}
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-section-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--space-3) var(--space-2) var(--space-1);
  user-select: none;
}
.nav-section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
}
.nav-section-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #3f3f46;
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
}
.nav-section-sep {
  height: 1px;
  background: rgba(255,255,255,0.04);
  margin: var(--space-2) var(--space-2);
}
.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 7px var(--space-2);
  border-radius: 7px;
  color: #52525b;
  font-size: 0.855rem;
  font-weight: 450;
  cursor: pointer;
  transition: color 150ms ease, background 150ms ease;
  width: 100%;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  border: none;
  background: transparent;
  font-family: inherit;
}
.nav-item:hover { color: #a1a1aa; background: rgba(255,255,255,0.04); }
.nav-item:hover .nav-icon { color: #d4d4d8; transform: scale(1.1); }
.nav-item:hover .nav-label { transform: translateX(2px); }
.nav-item--active { color: #e4e4e7; background: rgba(45,212,191,0.07); font-weight: 550; }
.nav-item--active:hover { background: rgba(45,212,191,0.1); }
.nav-item--active .nav-icon { color: #2dd4bf; }
.nav-item--locked { opacity: 0.45; cursor: not-allowed; }
.nav-item--locked:hover { background: rgba(251,191,36,0.04); color: #71717a; }
.nav-item--locked:hover .nav-icon { color: #71717a; transform: none; }
.nav-glow-sweep {
  position: absolute;
  inset: 0;
  border-radius: 7px;
  background: linear-gradient(90deg, rgba(45,212,191,0.12) 0%, rgba(45,212,191,0.04) 50%, transparent 100%);
  pointer-events: none;
}
.sidebar--collapsed .nav-item { justify-content: center; padding: 8px; }
.nav-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
  transition: color 150ms ease, transform 150ms cubic-bezier(0.16,1,0.3,1);
}
.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: transform 150ms cubic-bezier(0.16,1,0.3,1);
}
.nav-lock-icon { font-size: 0.65rem; color: #fbbf24; opacity: 0.7; flex-shrink: 0; margin-left: auto; }
.nav-active-bar {
  position: absolute;
  right: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 18px;
  background: #2dd4bf;
  border-radius: 2px 0 0 2px;
  box-shadow: 0 0 10px rgba(45,212,191,0.7), 0 0 20px rgba(45,212,191,0.3);
}

/* ════════════════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════════════════ */
.sidebar-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid rgba(255,255,255,0.04);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.sidebar-footer--collapsed { padding: var(--space-3); align-items: center; }
.footer-ws-row { display: flex; align-items: center; gap: 6px; }
.footer-ws-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.footer-ws-dot--solo { width: 7px; height: 7px; cursor: default; }
.footer-ws-dot--connected    { background: #4ade80; box-shadow: 0 0 5px rgba(74,222,128,0.65); animation: ws-glow 2.5s ease-in-out infinite; }
.footer-ws-dot--reconnecting { background: #fbbf24; animation: blink 0.9s ease-in-out infinite; }
.footer-ws-dot--connecting   { background: #fbbf24; animation: blink 1.2s ease-in-out infinite; }
.footer-ws-dot--disconnected { background: #3f3f46; }
@keyframes ws-glow {
  0%, 100% { box-shadow: 0 0 5px rgba(74,222,128,0.65); }
  50%       { box-shadow: 0 0 2px rgba(74,222,128,0.2); }
}
.footer-ws-label { font-size: 0.68rem; color: #52525b; font-family: var(--font-mono, monospace); letter-spacing: 0.02em; }
.footer-cluster-count { margin-left: auto; font-size: 0.65rem; color: #3f3f46; font-family: var(--font-mono, monospace); letter-spacing: 0.02em; }
.footer-brand { font-size: 0.6rem; color: #2d2d2d; letter-spacing: 0.04em; white-space: nowrap; }
</style>
