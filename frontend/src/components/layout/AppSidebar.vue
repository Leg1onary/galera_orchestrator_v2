<template>
  <nav class="app-sidebar">
    <!-- МОНИТОРИНГ -->
    <div class="nav-section-label">Мониторинг</div>
    <router-link to="/overview" class="nav-item" :class="{ active: $route.name === 'overview' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="7" height="7"/>
        <rect x="14" y="3" width="7" height="7"/>
        <rect x="3" y="14" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/>
      </svg>
      Обзор
    </router-link>
    <router-link to="/nodes" class="nav-item" :class="{ active: $route.name === 'nodes' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="2" width="20" height="8" rx="2"/>
        <rect x="2" y="14" width="20" height="8" rx="2"/>
        <line x1="6" y1="6" x2="6.01" y2="6"/>
        <line x1="6" y1="18" x2="6.01" y2="18"/>
      </svg>
      Ноды
    </router-link>
    <router-link to="/topology" class="nav-item" :class="{ active: $route.name === 'topology' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="5" r="3"/>
        <circle cx="5" cy="19" r="3"/>
        <circle cx="19" cy="19" r="3"/>
        <line x1="12" y1="8" x2="5" y2="16"/>
        <line x1="12" y1="8" x2="19" y2="16"/>
      </svg>
      Топология
    </router-link>

    <!-- УПРАВЛЕНИЕ -->
    <div class="nav-section-label">Управление</div>
    <router-link to="/recovery" class="nav-item" :class="{ active: $route.name === 'recovery' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      Recovery
    </router-link>
    <router-link to="/maintenance" class="nav-item" :class="{ active: $route.name === 'maintenance' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
      Обслуживание
    </router-link>
    <router-link to="/diagnostics" class="nav-item" :class="{ active: $route.name === 'diagnostics' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="11" y1="8" x2="11" y2="14"/>
        <line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
      Диагностика
    </router-link>
    <router-link to="/settings" class="nav-item" :class="{ active: $route.name === 'settings' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
      </svg>
      Настройки
    </router-link>

    <!-- СПРАВКА -->
    <div class="nav-section-label">Справка</div>
    <router-link to="/docs" class="nav-item" :class="{ active: $route.name === 'docs' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      Документация
    </router-link>

    <!-- Spacer -->
    <div style="flex:1"></div>

    <!-- Sidebar Footer -->
    <div class="sidebar-footer">
      <!-- Cluster status -->
      <div class="sidebar-cluster-status" title="Статус кластера">
        <span class="sidebar-status-pulse" :class="statusPulseClass"></span>
        <div class="sidebar-status-info">
          <div class="sidebar-status-label" :class="statusPulseClass">{{ statusLabel }}</div>
          <div class="sidebar-status-sub">{{ statusSub }}</div>
        </div>
      </div>
      <!-- Version + mode -->
      <div class="sidebar-version-row">
        <span class="sidebar-mode-badge" :class="cluster.dataMode">{{ cluster.dataMode.toUpperCase() }}</span>
        <span style="flex:1"></span>
        <span class="sidebar-version-sha">{{ cluster.gitSha }}</span>
        <a
          href="https://github.com/Leg1onary/galera_orchestrator"
          target="_blank"
          rel="noopener noreferrer"
          title="GitHub"
          style="color:var(--text-faint);line-height:0;transition:color var(--transition)"
          onmouseover="this.style.color='var(--text)'"
          onmouseout="this.style.color='var(--text-faint)'"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
        </a>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster = useClusterStore()

const statusPulseClass = computed(() => {
  const s = cluster.clusterState
  if (s === 'healthy')  return 'ok'
  if (s === 'degraded') return 'warn'
  if (s === 'critical' || s === 'error') return 'error'
  return cluster.status ? 'ok' : 'unknown'
})

const statusLabel = computed(() => {
  if (!cluster.status) return 'Инициализация…'
  const ws = cluster.status?.nodes?.[0]?.wsrep_cluster_status || 'Primary'
  const s  = cluster.clusterState
  if (s === 'healthy')  return `${ws} · OK`
  if (s === 'degraded') return `${ws} · Degraded`
  if (s === 'critical' || s === 'error') return `${ws} · Critical`
  return ws
})

const statusSub = computed(() => {
  if (!cluster.status) return 'ожидание данных'
  const total  = cluster.nodes.length
  const synced = cluster.nodesSynced
  return `${synced} Synced из ${total}`
})
</script>
