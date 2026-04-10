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

const navGroups = [
  {
    label: 'МОНИТОРИНГ',
    items: [
      { name: 'overview',    label: 'Обзор',       icon: 'pi pi-home' },
      { name: 'nodes',       label: 'Ноды',        icon: 'pi pi-server' },
      { name: 'topology',    label: 'Топология',   icon: 'pi pi-sitemap' },
    ],
  },
  {
    label: 'УПРАВЛЕНИЕ',
    items: [
      { name: 'recovery',    label: 'Recovery',    icon: 'pi pi-replay' },
      { name: 'maintenance', label: 'Обслуживание',icon: 'pi pi-wrench' },
      { name: 'diagnostics', label: 'Диагностика', icon: 'pi pi-chart-bar' },
      { name: 'settings',    label: 'Настройки',   icon: 'pi pi-cog' },
    ],
  },
  {
    label: 'СПРАВКА',
    items: [
      { name: 'docs',        label: 'Документация',icon: 'pi pi-book' },
    ],
  },
]

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
  <nav :class="['app-sidebar', { 'app-sidebar--collapsed': collapsed }]" aria-label="Основная навигация">
    <!-- Collapse toggle -->
    <button
        class="collapse-btn"
        :aria-expanded="String(!collapsed)"
        :title="collapsed ? 'Развернуть' : 'Свернуть'"
        @click="collapsed = !collapsed"
    >
      <i :class="collapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'" />
    </button>

    <!-- Nav groups -->
    <div class="nav-scroll">
      <div
          v-for="group in navGroups"
          :key="group.label"
          class="nav-group"
      >
        <span v-if="!collapsed" class="nav-group-label">{{ group.label }}</span>

        <ul class="nav-list">
          <li v-for="item in group.items" :key="item.name">
            <router-link
                :to="{ name: item.name }"
                :class="['nav-item', { 'nav-item--active': isActive(item.name) }]"
                :title="collapsed ? item.label : undefined"
            >
              <span class="nav-icon-wrap">
                <i :class="item.icon" />
              </span>
              <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>

              <!-- Active op indicator for recovery/maintenance -->
              <span
                  v-if="hasActiveOp && ['recovery', 'maintenance'].includes(item.name)"
                  class="op-dot"
                  :class="{ 'op-dot--collapsed': collapsed }"
              />
            </router-link>
          </li>
        </ul>
      </div>
    </div>

    <!-- Bottom cluster info -->
    <div v-if="!collapsed" class="sidebar-footer">
      <span class="sidebar-version">v2</span>
    </div>
  </nav>
</template>

<style scoped>
.app-sidebar {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width var(--transition-slow);
  position: relative;
  overflow: hidden;
}

.app-sidebar--collapsed {
  width: var(--sidebar-width-collapsed);
}

/* Subtle left glow accent */
.app-sidebar::after {
  content: '';
  position: absolute;
  top: 0; left: 0; bottom: 0;
  width: 1px;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(45,212,191,0.2) 30%,
    rgba(45,212,191,0.2) 70%,
    transparent 100%
  );
  pointer-events: none;
}

/* ── Collapse button ── */
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  width: 100%;
  border-bottom: 1px solid var(--color-border-muted);
  color: var(--color-text-faint);
  font-size: 0.7rem;
  transition: all var(--transition-normal);
  flex-shrink: 0;
}

.collapse-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-dim);
}

/* ── Nav scroll container ── */
.nav-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-3) 0;
}

/* ── Group ── */
.nav-group { margin-bottom: var(--space-2); }

.nav-group-label {
  display: block;
  padding: var(--space-3) var(--space-4) var(--space-1);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--color-text-faint);
  text-transform: uppercase;
  white-space: nowrap;
}

/* ── Nav list ── */
.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

/* ── Nav item ── */
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  margin: 1px var(--space-2);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 450;
  position: relative;
  transition: all var(--transition-normal);
  text-decoration: none;
}

.nav-item:hover {
  background: var(--color-surface-4);
  color: var(--color-text);
}

.nav-item--active {
  background: var(--color-primary-dim);
  color: var(--color-primary) !important;
  font-weight: 500;
}

.nav-item--active .nav-icon-wrap {
  filter: drop-shadow(0 0 4px rgba(45,212,191,0.5));
}

/* Left accent bar for active item */
.nav-item--active::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  border-radius: 0 2px 2px 0;
  background: var(--color-primary);
  box-shadow: 0 0 8px var(--color-primary-glow);
}

.nav-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  flex-shrink: 0;
  font-size: 0.875rem;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

/* ── Op indicator dot ── */
.op-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warning);
  box-shadow: 0 0 6px rgba(245,158,11,0.6);
  flex-shrink: 0;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.op-dot--collapsed {
  position: absolute;
  top: 5px;
  right: 5px;
  margin-left: 0;
}

/* ── Footer ── */
.sidebar-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border-muted);
  flex-shrink: 0;
}

.sidebar-version {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}
</style>
