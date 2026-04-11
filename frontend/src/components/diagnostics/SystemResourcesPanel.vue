<template>
  <div class="diag-panel">
    <div class="toolbar">
      <span class="toolbar-title">system_resources</span>
      <div class="toolbar-actions">
        <span v-if="fetchedAt" class="fetched-at">{{ fetchedAt }}</span>
        <button class="btn-refresh" :disabled="isLoading" @click="run">
          <i :class="['pi', isLoading ? 'pi-spin pi-spinner' : 'pi-play']" />
          <span>{{ isLoading ? 'Collecting…' : 'Run check' }}</span>
        </button>
      </div>
    </div>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <template v-else-if="rows && rows.length">
      <div v-for="row in rows" :key="row.node_id" class="resource-card">
        <div class="rc-header">
          <div class="node-dot" />
          <span class="rc-name">{{ row.node_name }}</span>
          <span v-if="row.error" class="rc-error-badge">error</span>
        </div>

        <div v-if="row.error" class="rc-error-msg">{{ row.error }}</div>

        <template v-else>
          <div class="rc-metrics">
            <!-- CPU -->
            <div class="metric">
              <div class="metric-label">CPU</div>
              <div class="metric-bar-wrap">
                <div
                    class="metric-bar"
                    :class="barClass(row.cpu_percent)"
                    :style="{ width: (row.cpu_percent ?? 0) + '%' }"
                />
              </div>
              <div :class="['metric-val', severityClass(row.cpu_percent, 80, 95)]">{{ row.cpu_percent != null ? row.cpu_percent + '%' : '—' }}</div>
            </div>
            <!-- RAM -->
            <div class="metric">
              <div class="metric-label">RAM</div>
              <div class="metric-bar-wrap">
                <div
                    class="metric-bar"
                    :class="barClass(ramPct(row))"
                    :style="{ width: (ramPct(row) ?? 0) + '%' }"
                />
              </div>
              <div :class="['metric-val', severityClass(ramPct(row), 85, 95)]">
                {{ row.ram_used_bytes != null && row.ram_total_bytes ? fmtBytes(row.ram_used_bytes) + ' / ' + fmtBytes(row.ram_total_bytes) : '—' }}
              </div>
            </div>
            <!-- Disk -->
            <div class="metric">
              <div class="metric-label">Disk</div>
              <div class="metric-bar-wrap">
                <div
                    class="metric-bar"
                    :class="barClass(diskPct(row))"
                    :style="{ width: (diskPct(row) ?? 0) + '%' }"
                />
              </div>
              <div :class="['metric-val', severityClass(diskPct(row), 80, 90)]">
                {{ row.disk_used_bytes != null && row.disk_total_bytes ? fmtBytes(row.disk_used_bytes) + ' / ' + fmtBytes(row.disk_total_bytes) : '—' }}
              </div>
            </div>
          </div>

          <div class="rc-extra">
            <span class="extra-item">
              <span class="extra-label">Load avg</span>
              <span class="extra-val">{{ row.load_avg_1 != null ? row.load_avg_1.toFixed(2) : '—' }}</span>
            </span>
            <span class="extra-sep">·</span>
            <span class="extra-item">
              <span class="extra-label">Uptime since</span>
              <span class="extra-val">{{ row.uptime_since ?? '—' }}</span>
            </span>
          </div>
        </template>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-server" /></div>
      <p>Click <strong>Run check</strong> to collect system metrics via SSH.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { useClusterStore }  from '@/stores/cluster'
import { diagnosticsApi, type NodeResourceRow } from '@/api/diagnostics'

defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const fetchedAt    = ref<string | null>(null)
const rows         = ref<NodeResourceRow[] | null>(null)
const error        = ref<Error | null>(null)

const { mutate, isPending: isLoading } = useMutation({
  mutationFn: () => diagnosticsApi.resources(clusterStore.selectedClusterId!),
  onSuccess: (data) => {
    rows.value      = data
    fetchedAt.value = new Date().toLocaleTimeString()
    error.value     = null
  },
  onError: (e: unknown) => {
    error.value = e instanceof Error ? e : new Error(String(e))
  },
})

function run() {
  if (!clusterStore.selectedClusterId) return
  mutate()
}

function ramPct(row: NodeResourceRow): number | null {
  if (row.ram_used_bytes == null || !row.ram_total_bytes) return null
  return Math.round((row.ram_used_bytes / row.ram_total_bytes) * 100)
}

function diskPct(row: NodeResourceRow): number | null {
  if (row.disk_used_bytes == null || !row.disk_total_bytes) return null
  return Math.round((row.disk_used_bytes / row.disk_total_bytes) * 100)
}

function fmtBytes(b: number): string {
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB'
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB'
  return (b / 1e3).toFixed(0) + ' KB'
}

function severityClass(val: number | null, warn: number, crit: number): string {
  if (val == null) return ''
  if (val >= crit) return 'val-crit'
  if (val >= warn) return 'val-warn'
  return ''
}

function barClass(val: number | null): string {
  if (val == null) return ''
  if (val >= 95) return 'bar-crit'
  if (val >= 80) return 'bar-warn'
  return 'bar-ok'
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.toolbar-title {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
  letter-spacing: 0.03em;
}

.toolbar-actions { display: flex; align-items: center; gap: var(--space-3); }

.fetched-at {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px var(--space-4);
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-normal);
}

.btn-refresh:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-refresh:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-refresh .pi { font-size: 0.7rem; }

/* RESOURCE CARDS */
.resource-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.rc-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.node-dot {
  width: 6px; height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  flex-shrink: 0;
}

.rc-name {
  font-size: var(--text-sm);
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text);
}

.rc-error-badge {
  margin-left: var(--space-2);
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  background: rgba(248,113,113,0.15);
  color: var(--color-error);
}

.rc-error-msg {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-error);
  font-family: var(--font-mono);
}

.rc-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
}

.metric {
  display: grid;
  grid-template-columns: 60px 1fr 140px;
  align-items: center;
  gap: var(--space-3);
}

.metric-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.metric-bar-wrap {
  height: 6px;
  background: var(--color-surface-offset);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.metric-bar {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.4s ease;
}

.bar-ok   { background: var(--color-success); }
.bar-warn { background: var(--color-warning); }
.bar-crit { background: var(--color-error); }

.metric-val {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.val-warn { color: var(--color-warning); font-weight: 700; }
.val-crit { color: var(--color-error); font-weight: 700; }

.rc-extra {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-border-muted);
}

.extra-item { display: flex; align-items: center; gap: var(--space-2); }
.extra-label { font-size: var(--text-xs); color: var(--color-text-faint); }
.extra-val   { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-text-muted); }
.extra-sep   { color: var(--color-text-faint); }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error); font-size: var(--text-sm);
}

.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm); text-align: center;
}

.empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-3); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
</style>
