<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'

const props = defineProps<{ collapsed: boolean }>()
const emit  = defineEmits<{ toggle: [] }>()

const route        = useRoute()
const router       = useRouter()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.currentCluster?.id ?? '')

interface NavItem {
  key:    string
  label:  string
  icon:   string
  to?:    () => object
  group?: string
}

const navItems = computed((): NavItem[] => [
  { key: 'overview',    label: 'Overview',    icon: 'pi-chart-bar',   group: 'monitor', to: () => ({ name: 'overview',    params: { clusterId: clusterId.value } }) },
  { key: 'topology',   label: 'Topology',    icon: 'pi-sitemap',     group: 'monitor', to: () => ({ name: 'topology',    params: { clusterId: clusterId.value } }) },
  { key: 'nodes',      label: 'Nodes',       icon: 'pi-server',      group: 'monitor', to: () => ({ name: 'nodes',       params: { clusterId: clusterId.value } }) },
  { key: 'recovery',   label: 'Recovery',    icon: 'pi-replay',      group: 'ops',     to: () => ({ name: 'recovery',    params: { clusterId: clusterId.value } }) },
  { key: 'maintenance',label: 'Maintenance', icon: 'pi-wrench',      group: 'ops',     to: () => ({ name: 'maintenance', params: { clusterId: clusterId.value } }) },
  { key: 'diagnostics',label: 'Diagnostics', icon: 'pi-search',      group: 'ops',     to: () => ({ name: 'diagnostics', params: { clusterId: clusterId.value } }) },
  { key: 'settings',   label: 'Settings',    icon: 'pi-sliders-h',   group: 'system',  to: () => ({ name: 'settings',    params: { clusterId: clusterId.value } }) },
  { key: 'docs',       label: 'Docs',        icon: 'pi-book',        group: 'system',  to: () => ({ name: 'docs',        params: { clusterId: clusterId.value } }) },
])

const groups: { key: string; label: string }[] = [
  { key: 'monitor', label: 'Monitor' },
  { key: 'ops',     label: 'Operations' },
  { key: 'system',  label: 'System' },
]

function isActive(item: NavItem): boolean {
  return route.name === item.key
}

function navigate(item: NavItem) {
  if (item.to) router.push(item.to())
}
</script>

<template>
  <nav
    class="sidebar"
    :class="{ 'sidebar--collapsed': collapsed }"
    aria-label="Main navigation"
  >
    <!-- ── Header ───────────────────────────────────────────────── -->
    <div class="sidebar-header">
      <!-- Logo (hidden when collapsed) -->
      <div class="sidebar-logo" v-show="!collapsed">
        <div class="logo-icon">
          <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="10" stroke="#2dd4bf" stroke-width="1.5" opacity="0.35"/>
            <circle cx="11" cy="11" r="6"  stroke="#2dd4bf" stroke-width="1.5" opacity="0.65"/>
            <circle cx="11" cy="11" r="2.5" fill="#2dd4bf"/>
          </svg>
        </div>
        <span class="logo-text">Galera</span>
        <span class="logo-version">v2</span>
      </div>

      <!-- Toggle button — всегда виден, меняет позицию -->
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

    <!-- ── Cluster pill ─────────────────────────────────────────── -->
    <div
      v-if="clusterStore.currentCluster"
      class="cluster-pill"
      :class="{ 'cluster-pill--collapsed': collapsed }"
      :title="collapsed ? clusterStore.currentCluster.name : undefined"
    >
      <!-- collapsed: пульсирующая точка -->
      <span v-if="collapsed" class="cluster-dot" />
      <template v-else>
        <span class="cluster-pill__label">cluster</span>
        <span class="cluster-pill__name">{{ clusterStore.currentCluster.name }}</span>
      </template>
    </div>

    <!-- ── Nav ──────────────────────────────────────────────────── -->
    <div class="sidebar-nav">
      <template v-for="group in groups" :key="group.key">
        <!-- Group header -->
        <div class="nav-section-head" v-if="!collapsed">
          {{ group.label }}
        </div>
        <div class="nav-section-sep" v-else />

        <!-- Nav items -->
        <button
          v-for="item in navItems.filter(i => i.group === group.key)"
          :key="item.key"
          class="nav-item"
          :class="{ 'nav-item--active': isActive(item) }"
          @click="navigate(item)"
          v-tooltip.right="collapsed ? item.label : ''"
          :aria-label="item.label"
          :aria-current="isActive(item) ? 'page' : undefined"
        >
          <i :class="'pi ' + item.icon" class="nav-icon" />
          <span class="nav-label" v-show="!collapsed">{{ item.label }}</span>
          <!-- Active bar -->
          <span v-if="isActive(item)" class="nav-active-bar" aria-hidden="true" />
        </button>
      </template>
    </div>

    <!-- ── Footer ────────────────────────────────────────────────── -->
    <div class="sidebar-footer" v-show="!collapsed">
      <span class="sidebar-footer__text">Galera Orchestrator</span>
    </div>

  </nav>
</template>

<style scoped>
/* ── Shell ── */
.sidebar {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width, 220px);
  background: #0f1015;
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width 240ms cubic-bezier(0.16,1,0.3,1);
  overflow: hidden;
}
.sidebar--collapsed {
  width: var(--sidebar-width-collapsed, 56px);
}

/* ── Header row ── */
.sidebar-header {
  height: var(--header-height, 52px);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  gap: var(--space-2);
  min-width: 0;
}

/* Logo group — grow to fill, hide on collapse */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.logo-icon { flex-shrink: 0; display: flex; align-items: center; }

.logo-text {
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #e4e4e7;
  white-space: nowrap;
}

.logo-version {
  font-size: 0.65rem;
  font-weight: 600;
  color: #2dd4bf;
  background: rgba(45,212,191,0.1);
  border: 1px solid rgba(45,212,191,0.2);
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  letter-spacing: 0.03em;
}

/* Toggle button */
.toggle-btn {
  flex-shrink: 0;
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md, 6px);
  border: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.03);
  color: #52525b;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 150ms ease;
}
.toggle-btn:hover {
  color: #e4e4e7;
  background: rgba(255,255,255,0.07);
  border-color: rgba(255,255,255,0.12);
}
/* Когда collapsed — кнопка одна в header, центрируем её */
.toggle-btn--solo {
  margin: 0 auto;
}

/* ── Cluster pill ── */
.cluster-pill {
  margin: var(--space-3) var(--space-3) var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: rgba(45,212,191,0.05);
  border: 1px solid rgba(45,212,191,0.15);
  border-radius: var(--radius-md, 6px);
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  transition: all 150ms ease;
}
.cluster-pill--collapsed {
  margin: var(--space-3) auto var(--space-1);
  width: 32px; height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.cluster-pill__label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #2dd4bf;
  font-weight: 600;
  opacity: 0.7;
}
.cluster-pill__name {
  font-size: var(--text-sm, 0.875rem);
  font-weight: 600;
  color: #e4e4e7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--font-mono, monospace);
}
.cluster-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #2dd4bf;
  box-shadow: 0 0 6px rgba(45,212,191,0.6);
  animation: pulse-dot 2.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px rgba(45,212,191,0.6); }
  50%       { opacity: 0.6; box-shadow: 0 0 12px rgba(45,212,191,0.3); }
}

/* ── Nav scroll area ── */
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

/* Section heading */
.nav-section-head {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #3f3f46;
  font-weight: 600;
  padding: var(--space-3) var(--space-2) var(--space-1);
  white-space: nowrap;
  user-select: none;
}
.nav-section-sep {
  height: 1px;
  background: rgba(255,255,255,0.04);
  margin: var(--space-2) var(--space-2);
}

/* Nav item */
.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2);
  border-radius: var(--radius-md, 6px);
  color: #52525b;
  font-size: var(--text-sm, 0.875rem);
  font-weight: 450;
  cursor: pointer;
  transition: all 150ms ease;
  width: 100%;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  border: none;
  background: transparent;
  font-family: inherit;
}
.nav-item:hover {
  color: #a1a1aa;
  background: rgba(255,255,255,0.04);
}
.nav-item--active {
  color: #2dd4bf;
  background: rgba(45,212,191,0.08);
  font-weight: 500;
}
.nav-item--active:hover {
  background: rgba(45,212,191,0.12);
}

/* In collapsed mode center the icon */
.sidebar--collapsed .nav-item {
  justify-content: center;
  padding: var(--space-2);
}

.nav-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Active right-edge indicator */
.nav-active-bar {
  position: absolute;
  right: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 18px;
  background: #2dd4bf;
  border-radius: 2px 0 0 2px;
  box-shadow: 0 0 8px rgba(45,212,191,0.5);
}

/* ── Footer ── */
.sidebar-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid rgba(255,255,255,0.04);
  flex-shrink: 0;
}
.sidebar-footer__text {
  font-size: 0.65rem;
  color: #3f3f46;
  letter-spacing: 0.03em;
}
</style>
