<template>
  <div class="diag-panel">
    <PanelToolbar
        title="galera_status"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ error.message }}</span>
    </div>

    <template v-else-if="data && data.length">
      <!-- KEY METRICS STRIP -->
      <div class="metrics-grid">
        <div
            v-for="m in pinnedMetrics"
            :key="m.key"
            class="metric-card"
            :class="'metric-card--' + (m.accent || 'neutral')"
        >
          <span class="metric-label">{{ m.label }}</span>
          <span class="metric-value" :class="m.valueClass">{{ m.value }}</span>
        </div>
      </div>

      <!-- PER-NODE TABLES -->
      <div v-for="node in data" :key="node.node_id" class="node-block">
        <div class="node-block-header">
          <div class="node-dot" />
          <span class="node-block-name">{{ node.node_name }}</span>
          <span class="node-sep">/</span>
          <span class="node-block-host">{{ node.host }}</span>
        </div>
        <div class="vars-table">
          <div v-for="(val, key) in node.status" :key="key" class="vars-row">
            <span class="vars-key">{{ key }}</span>
            <span class="vars-val" :class="statusClass(String(key), String(val))">{{ val }}</span>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-chart-bar" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useClusterStore }   from '@/stores/cluster'
import { diagnosticsApi }    from '@/api/diagnostics'
import PanelToolbar          from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-galera-status', clusterStore.selectedClusterId]),
  queryFn: () => diagnosticsApi.getGaleraStatus(clusterStore.selectedClusterId!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const PINNED_KEYS = [
  { key: 'wsrep_cluster_size',        label: 'Cluster size',  accent: 'neutral' },
  { key: 'wsrep_cluster_status',      label: 'Cluster status', accent: 'dynamic' },
  { key: 'wsrep_connected',           label: 'Connected',      accent: 'dynamic' },
  { key: 'wsrep_ready',               label: 'Ready',          accent: 'dynamic' },
  { key: 'wsrep_local_state_comment', label: 'Local state',    accent: 'dynamic' },
  { key: 'wsrep_flow_control_paused', label: 'FC paused',      accent: 'dynamic' },
]

const pinnedMetrics = computed(() => {
  if (!data.value?.length) return []
  const st = data.value[0].status as Record<string, unknown>
  return PINNED_KEYS
    .filter((m) => m.key in st)
    .map((m) => ({
      ...m,
      value: String(st[m.key]),
      valueClass: metricClass(m.key, String(st[m.key])),
    }))
})

function metricClass(key: string, val: string): string {
  if (key === 'wsrep_cluster_status') return val === 'Primary' ? 'val-success' : 'val-error'
  if (key === 'wsrep_connected' || key === 'wsrep_ready') return val === 'ON' ? 'val-success' : 'val-error'
  if (key === 'wsrep_local_state_comment') return val === 'Synced' ? 'val-success' : 'val-warning'
  if (key === 'wsrep_flow_control_paused') return parseFloat(val) > 0 ? 'val-warning' : 'val-success'
  return ''
}

function statusClass(key: string, val: string): string {
  return metricClass(key, val)
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

/* METRICS GRID */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--space-3);
}

.metric-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-border);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.metric-card:has(.val-success)::before { background: var(--color-synced); }
.metric-card:has(.val-warning)::before { background: var(--color-warning); }
.metric-card:has(.val-error)::before   { background: var(--color-error); }

.metric-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
  color: var(--color-text-faint);
  font-family: var(--font-mono);
}

.metric-value {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}

/* NODE BLOCKS */
.node-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-block-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.node-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  flex-shrink: 0;
}

.node-block-name {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
  font-family: var(--font-mono);
}

.node-sep {
  color: var(--color-text-faint);
  font-size: var(--text-xs);
}

.node-block-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

/* VARS TABLE */
.vars-table { display: flex; flex-direction: column; }

.vars-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--color-border-muted);
  transition: background var(--transition-fast);
}

.vars-row:last-child { border-bottom: none; }

.vars-row:nth-child(even) { background: rgba(255,255,255,0.015); }

.vars-row:hover { background: var(--color-surface-3); }

.vars-key {
  flex: 0 0 280px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  word-break: break-all;
}

.vars-val {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  word-break: break-all;
}

.val-success { color: var(--color-synced)  !important; font-weight: 700; }
.val-warning { color: var(--color-warning) !important; font-weight: 700; }
.val-error   { color: var(--color-error)   !important; font-weight: 700; }

/* ERROR */
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error); font-size: var(--text-sm);
}

/* EMPTY */
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm);
}

.empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-3); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
</style>
