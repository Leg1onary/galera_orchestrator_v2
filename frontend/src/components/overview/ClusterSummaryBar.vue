<script setup lang="ts">
import { formatRelative } from '@/utils/time'

interface ClusterStatus {
  status: 'healthy' | 'degraded' | 'critical'
  online_nodes: number
  total_nodes: number
  wsrep_cluster_size: number
  primary: boolean
  online_arbitrators: number
  total_arbitrators: number
  last_update_ts: string | null
}

const props = defineProps<{ status: ClusterStatus | null }>()

function clusterStatusClass(s: ClusterStatus['status']) {
  if (s === 'healthy')  return 'status-pill--healthy'
  if (s === 'degraded') return 'status-pill--degraded-cluster'
  return 'status-pill--critical'
}
</script>

<template>
  <div v-if="status" class="summary-bar anim-fade-in">
    <!-- Status -->
    <div class="summary-item summary-item--status">
      <span class="summary-label">Статус</span>
      <span :class="['status-pill', clusterStatusClass(status.status)]">
        <span class="status-dot" />
        {{ status.status }}
      </span>
    </div>

    <!-- Primary Component -->
    <div class="summary-item">
      <span class="summary-label">Primary</span>
      <span :class="['status-pill', status.primary ? 'status-pill--healthy' : 'status-pill--critical']">
        {{ status.primary ? 'YES' : 'NO' }}
      </span>
    </div>

    <!-- Divider -->
    <div class="summary-sep" />

    <!-- Nodes -->
    <div class="summary-item">
      <span class="summary-label">Ноды</span>
      <span class="summary-value">
        <span :class="status.online_nodes === status.total_nodes ? 'val-ok' : 'val-warn'">{{ status.online_nodes }}</span>
        <span class="val-sep">/</span>
        <span>{{ status.total_nodes }}</span>
      </span>
    </div>

    <!-- wsrep_cluster_size -->
    <div class="summary-item">
      <span class="summary-label">wsrep_size</span>
      <span class="summary-value">{{ status.wsrep_cluster_size }}</span>
    </div>

    <!-- Arbitrators -->
    <div class="summary-item" v-if="status.total_arbitrators > 0">
      <span class="summary-label">Арбитраторы</span>
      <span class="summary-value">
        <span :class="status.online_arbitrators > 0 ? 'val-ok' : 'val-error'">{{ status.online_arbitrators }}</span>
        <span class="val-sep">/</span>
        <span>{{ status.total_arbitrators }}</span>
      </span>
    </div>

    <!-- Divider -->
    <div class="summary-sep" />

    <!-- Last update -->
    <div class="summary-item summary-item--ts">
      <span class="summary-label">Обновлено</span>
      <span class="summary-ts">{{ formatRelative(status.last_update_ts) }}</span>
    </div>
  </div>
</template>

<style scoped>
.summary-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
}

/* Subtle left accent */
.summary-bar::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg,
    transparent 0%,
    var(--color-primary) 30%,
    var(--color-primary) 70%,
    transparent 100%
  );
  box-shadow: 0 0 12px var(--color-primary-glow);
}

/* ── Item ── */
.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  font-weight: 600;
}

.summary-value {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.val-ok    { color: var(--color-synced); }
.val-warn  { color: var(--color-degraded); }
.val-error { color: var(--color-offline); }
.val-sep   { color: var(--color-text-faint); font-size: var(--text-sm); }

/* ── Status pill inside bar ── */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: var(--radius-xl);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  border: 1px solid transparent;
}

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 2.5s ease-in-out infinite;
}

.status-pill--healthy {
  background: rgba(34,197,94,0.1);
  color: #22c55e;
  border-color: rgba(34,197,94,0.25);
}
.status-pill--degraded-cluster {
  background: rgba(249,115,22,0.1);
  color: #f97316;
  border-color: rgba(249,115,22,0.25);
}
.status-pill--critical {
  background: rgba(239,68,68,0.1);
  color: #ef4444;
  border-color: rgba(239,68,68,0.25);
}

/* ── Separator ── */
.summary-sep {
  width: 1px;
  height: 36px;
  background: var(--color-border-muted);
  align-self: center;
}

/* ── Timestamp ── */
.summary-ts {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
</style>
