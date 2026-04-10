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
  key:   string
  label: string
  icon:  string
  to?:   () => object
  group?: string
}

const navItems = computed((): NavItem[] => [
  { key: 'overview',    label: 'Overview',    icon: 'pi-chart-bar',    group: 'monitor',  to: () => ({ name: 'overview',    params: { clusterId: clusterId.value } }) },
  { key: 'topology',   label: 'Topology',    icon: 'pi-sitemap',      group: 'monitor',  to: () => ({ name: 'topology',    params: { clusterId: clusterId.value } }) },
  { key: 'nodes',      label: 'Nodes',       icon: 'pi-server',       group: 'monitor',  to: () => ({ name: 'nodes',       params: { clusterId: clusterId.value } }) },
  { key: 'recovery',   label: 'Recovery',    icon: 'pi-replay',       group: 'ops',      to: () => ({ name: 'recovery',    params: { clusterId: clusterId.value } }) },
  { key: 'maintenance',label: 'Maintenance', icon: 'pi-wrench',       group: 'ops',      to: () => ({ name: 'maintenance', params: { clusterId: clusterId.value } }) },
  { key: 'diagnostics',label: 'Diagnostics', icon: 'pi-search',       group: 'ops',      to: () => ({ name: 'diagnostics', params: { clusterId: clusterId.value } }) },
  { key: 'settings',   label: 'Settings',    icon: 'pi-sliders-h',    group: 'system',   to: () => ({ name: 'settings',    params: { clusterId: clusterId.value } }) },
  { key: 'docs',       label: 'Docs',        icon: 'pi-book',         group: 'system',   to: () => ({ name: 'docs',        params: { clusterId: clusterId.value } }) },
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
  <nav class="sidebar" :class="{ 'sidebar--collapsed': collapsed }" aria-label="Main navigation">

    <!-- Logo + collapse -->
    <div class="sidebar-logo">
      <div class="logo-mark">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
          <circle cx="11" cy="11" r="10" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <circle cx="11" cy="11" r="6"  stroke="currentColor" stroke-width="1.5" opacity="0.6"/>
          <circle cx="11" cy="11" r="2.5" fill="currentColor"/>
        </svg>
      </div>
      <span class="logo-text" v-if="!collapsed">Galera</span>
      <button
        class="collapse-btn"
        :class="{ 'collapse-btn--far': !collapsed }"
        @click="emit('toggle')"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        v-tooltip.right="collapsed ? 'Expand' : ''"
      >
        <i :class="collapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'" />
      </button>
    </div>

    <!-- Cluster selector -->
    <div class="sidebar-cluster" v-if="clusterStore.currentCluster && !collapsed">
      <span class="cluster-label">cluster</span>
      <span class="cluster-name">{{ clusterStore.currentCluster.name }}</span>
    </div>

    <!-- Navigation -->
    <div class="sidebar-nav">
      <template v-for="group in groups" :key="group.key">
        <div class="nav-group-label" v-if="!collapsed">{{ group.label }}</div>
        <div class="nav-group-sep" v-else />
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
          <span class="nav-label" v-if="!collapsed">{{ item.label }}</span>
          <span
            class="nav-active-indicator"
            v-if="isActive(item)"
            aria-hidden="true"
          />
        </button>
      </template>
    </div>

  </nav>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width var(--transition-slow);
  overflow: hidden;
}

.sidebar--collapsed { width: var(--sidebar-width-collapsed); }

.sidebar-logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 var(--space-3);
  gap: var(--space-3);
  border-bottom: 1px solid var(--color-border-muted);
  flex-shrink: 0;
}

.logo-mark {
  flex-shrink: 0;
  color: var(--color-primary);
  display: flex;
  align-items: center;
}

.logo-text {
  font-size: var(--text-md);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
  white-space: nowrap;
  flex: 1;
  overflow: hidden;
}

.collapse-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  color: var(--color-text-faint);
  transition: all var(--transition-normal);
  margin-left: auto;
}

.collapse-btn--far { margin-left: auto; }

.collapse-btn:hover {
  color: var(--color-text-muted);
  background: var(--color-surface-3);
}

.sidebar-cluster {
  padding: var(--space-3) var(--space-4);
  margin: var(--space-3) var(--space-3) var(--space-2);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.cluster-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  font-weight: 500;
}

.cluster-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--font-mono);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-2) var(--space-2);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-group-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--color-text-faint);
  font-weight: 600;
  padding: var(--space-3) var(--space-2) var(--space-1);
  white-space: nowrap;
}

.nav-group-sep {
  height: 1px;
  background: var(--color-border-muted);
  margin: var(--space-2) var(--space-2);
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 450;
  cursor: pointer;
  transition: all var(--transition-normal);
  width: 100%;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  color: var(--color-text);
  background: var(--color-surface-3);
}

.nav-item--active {
  color: var(--color-primary);
  background: var(--color-primary-dim);
  font-weight: 500;
}

.nav-item--active:hover {
  background: rgba(45,212,191,0.14);
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

.nav-active-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 16px;
  background: var(--color-primary);
  border-radius: 1px 0 0 1px;
}
</style>
