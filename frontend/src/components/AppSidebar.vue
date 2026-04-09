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
  <nav :class="['app-sidebar', { collapsed }]">
    <button class="collapse-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Expand' : 'Collapse'">
      <i :class="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'" />
    </button>

    <ul class="nav-list">
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
              v-if="!collapsed && hasActiveOp && ['recovery', 'maintenance'].includes(item.name)"
              class="op-indicator"
          />
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.app-sidebar {
  width: 220px;
  background: #1a1f2e;
  border-right: 1px solid #2a3040;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.2s ease;
}

.app-sidebar.collapsed { width: 56px; }

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: none;
  border: none;
  border-bottom: 1px solid #2a3040;
  cursor: pointer;
  color: #64748b;
  transition: color 0.15s;
}
.collapse-btn:hover { color: #4ade80; }

.nav-list { list-style: none; padding: 0.5rem 0; margin: 0; flex: 1; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.875rem;
  border-radius: 6px;
  margin: 2px 6px;
  transition: background 0.15s, color 0.15s;
  position: relative;
}
.nav-item:hover  { background: #252b3b; color: #e2e8f0; }
.nav-item.active { background: #0f2918; color: #4ade80; font-weight: 600; }

.nav-label { white-space: nowrap; overflow: hidden; }

.op-indicator {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #fbbf24;
  margin-left: auto;
  flex-shrink: 0;
}
</style>