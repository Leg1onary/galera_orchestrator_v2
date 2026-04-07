<template>
  <aside class="app-sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <svg viewBox="0 0 36 36" width="32" height="32" fill="none" aria-label="Galera Orchestrator">
        <circle cx="18" cy="18" r="17" stroke="#3b82f6" stroke-width="2"/>
        <circle cx="10" cy="18" r="4" fill="#22c55e"/>
        <circle cx="26" cy="18" r="4" fill="#22c55e"/>
        <circle cx="18" cy="10" r="4" fill="#3b82f6"/>
        <line x1="14" y1="18" x2="22" y2="18" stroke="#3b82f6" stroke-width="1.5"/>
        <line x1="18" y1="10" x2="10" y2="18" stroke="#3b82f6" stroke-width="1.5"/>
        <line x1="18" y1="10" x2="26" y2="18" stroke="#3b82f6" stroke-width="1.5"/>
      </svg>
      <div class="logo-text">
        <span class="logo-name">Galera</span>
        <span class="logo-sub">Orchestrator v2</span>
      </div>
    </div>

    <!-- Cluster status indicator -->
    <div class="sidebar-status">
      <div class="status-dot" :class="cluster.clusterHealth" />
      <div class="status-info">
        <div class="status-name">{{ cluster.clusterName }}</div>
        <div class="status-detail">
          <span :class="`status-text-${cluster.clusterHealth}`">
            {{ statusText }}
          </span>
          <span class="status-count" v-if="cluster.status">
            {{ cluster.status.nodes_synced }}/{{ cluster.status.nodes_total }} Synced
          </span>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="sidebar-nav">
      <router-link v-for="item in navItems" :key="item.path"
        :to="item.path" class="nav-item"
        :class="{ active: $route.path === item.path }">
        <i :class="`pi ${item.icon}`" />
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="footer-row">
        <span class="badge" :class="cluster.isMock ? 'badge-mock' : 'badge-real'">
          {{ cluster.isMock ? 'MOCK' : 'REAL' }}
        </span>
        <span class="ws-indicator" :class="{ connected: cluster.wsConnected }" title="WebSocket">
          <i class="pi pi-circle-fill" />
        </span>
      </div>
      <div class="footer-version" v-if="cluster.version">
        <a :href="cluster.version.release_url || 'https://github.com/Leg1onary/galera_orchestrator_v2'"
           target="_blank" rel="noopener" class="version-link">
          {{ cluster.version.local || 'v2.0.0' }}
        </a>
        <span v-if="cluster.version.update_available" class="update-badge">UPDATE</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()

const statusText = computed(() => {
  const h = cluster.clusterHealth
  if (h === 'ok') return 'Primary'
  if (h === 'warn') return 'Degraded'
  if (h === 'error') return 'Critical'
  return 'Unknown'
})

const navItems = [
  { path: '/',            icon: 'pi-th-large',   label: 'Обзор' },
  { path: '/nodes',       icon: 'pi-server',     label: 'Ноды' },
  { path: '/topology',    icon: 'pi-sitemap',    label: 'Топология' },
  { path: '/recovery',    icon: 'pi-refresh',    label: 'Recovery' },
  { path: '/maintenance', icon: 'pi-wrench',     label: 'Обслуживание' },
  { path: '/diagnostics', icon: 'pi-chart-line', label: 'Диагностика' },
  { path: '/settings',    icon: 'pi-cog',        label: 'Настройки' },
  { path: '/docs',        icon: 'pi-book',       label: 'Документация' },
]
</script>

<style scoped>
.app-sidebar { display: flex; flex-direction: column; height: 100%; }

.sidebar-logo {
  display: flex; align-items: center; gap: 0.625rem;
  padding: 1rem 1rem 0.875rem;
  border-bottom: 1px solid var(--color-border);
}
.logo-text { display: flex; flex-direction: column; }
.logo-name  { font-size: 14px; font-weight: 700; color: var(--color-text-primary); line-height: 1.2; }
.logo-sub   { font-size: 10px; color: var(--color-text-muted); }

.sidebar-status {
  display: flex; align-items: center; gap: 0.625rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  margin: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
}
.status-info { display: flex; flex-direction: column; min-width: 0; }
.status-name { font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.status-detail { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.status-count  { font-size: 11px; color: var(--color-text-muted); }
.status-text-ok    { font-size: 11px; color: var(--color-status-ok); }
.status-text-warn  { font-size: 11px; color: var(--color-status-warn); }
.status-text-error { font-size: 11px; color: var(--color-status-error); }
.status-text-unknown { font-size: 11px; color: var(--color-status-unknown); }

.sidebar-nav { flex: 1; overflow-y: auto; padding: 0.5rem 0.5rem; display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 0.625rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-item:hover { background: var(--color-bg-elevated); color: var(--color-text-primary); }
.nav-item.active { background: var(--color-accent-light); color: var(--color-accent-primary); }
.nav-item i { width: 16px; text-align: center; font-size: 14px; }

.sidebar-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--color-border);
  display: flex; flex-direction: column; gap: 0.375rem;
}
.footer-row { display: flex; align-items: center; gap: 0.5rem; }
.ws-indicator { font-size: 8px; }
.ws-indicator i { color: var(--color-status-unknown); }
.ws-indicator.connected i { color: var(--color-status-ok); }
.footer-version { display: flex; align-items: center; gap: 0.5rem; }
.version-link { font-size: 11px; color: var(--color-text-muted); text-decoration: none; }
.version-link:hover { color: var(--color-accent-primary); }
.update-badge { font-size: 9px; font-weight: 700; background: rgba(245,158,11,.2); color: #fbbf24; border: 1px solid rgba(245,158,11,.4); border-radius: 3px; padding: 1px 4px; }
</style>
