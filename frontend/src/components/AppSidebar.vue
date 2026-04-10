<!-- ТЗ 6.3: навигация + активный маршрут + collapse -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useOperationsStore } from '@/stores/operations'
import { useClusterStore } from '@/stores/cluster'

const route = useRoute()
const operationsStore = useOperationsStore()
const clusterStore = useClusterStore()

const collapsed = ref(false)

const navItems = [
  { name: 'overview',     label: 'Overview',     icon: 'pi pi-home' },
  { name: 'nodes',        label: 'Nodes',        icon: 'pi pi-server' },
  { name: 'topology',     label: 'Topology',     icon: 'pi pi-sitemap' },
  { name: 'recovery',     label: 'Recovery',     icon: 'pi pi-replay' },
  { name: 'maintenance',  label: 'Maintenance',  icon: 'pi pi-wrench' },
  { name: 'diagnostics',  label: 'Diagnostics',  icon: 'pi pi-chart-bar' },
  { name: 'settings',     label: 'Settings',     icon: 'pi pi-cog' },
  { name: 'docs',         label: 'Docs',         icon: 'pi pi-book' },
]

// Показываем spinner на recovery/maintenance когда есть активная операция
const hasActiveOp = computed(() =>
    clusterStore.selectedClusterId
        ? operationsStore.isLocked(clusterStore.selectedClusterId)
        : false
)

function isActive(name: string) {
  return route.name === name
}
</script>

<template>
  <nav :class="['app-sidebar', { collapsed }]" aria-label="Main navigation">
    <button
        class="collapse-btn"
        :aria-expanded="String(!collapsed)"
        aria-controls="sidebar-nav"
        :title="collapsed ? 'Expand' : 'Collapse'"
        @click="collapsed = !collapsed"
    >
      <i :class="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'" />
    </button>

    <ul id="sidebar-nav" class="nav-list">
      <li v-for="item in navItems" :key="item.name">
        <router-link
            :to="{ name: item.name }"
            :class="['nav-item', { active: isActive(item.name) }]"
            :title="collapsed ? item.label : undefined"
        >
          <i :class="item.icon" />
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
          <!-- Индикатор активной операции на recovery/maintenance -->
          <span
              v-if="hasActiveOp && ['recovery', 'maintenance'].includes(item.name)"
              :class="['op-indicator', { 'op-indicator--collapsed': collapsed }]"
          />
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>

.app-sidebar {
  background: var(--p-surface-section);
  border-right: 1px solid var(--p-content-border-color);
}

.collapse-btn {
  border-bottom: 1px solid var(--p-content-border-color);
  color: var(--p-text-muted-color);
}
.collapse-btn:hover { color: var(--p-primary-color); }

.nav-item {
  color: var(--p-text-muted-color);
}
.nav-item:hover {
  background: var(--p-surface-hover);
  color: var(--p-text-color);
}
.nav-item.active {
  background: var(--p-primary-50, color-mix(in srgb, var(--p-primary-color) 10%, transparent));
  color: var(--p-primary-color);
}

.op-indicator { background: var(--p-yellow-400); }

.app-sidebar.collapsed { width: 56px; }

.nav-list { list-style: none; padding: 0.5rem 0; margin: 0; flex: 1; }

.nav-label { white-space: nowrap; overflow: hidden; }

.op-indicator--collapsed {
  position: absolute;
  top: 6px;
  right: 6px;
  margin-left: 0;
}
</style>