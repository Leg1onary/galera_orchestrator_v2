<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type NodeResourceRow, type DiskUsageNodeResult } from '@/api/diagnostics'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const rows    = ref<NodeResourceRow[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const lastRun = ref<string | null>(null)

// Per-node disk details state
const diskExpanded  = ref<Record<number, boolean>>({})
const diskLoading   = ref<Record<number, boolean>>({})
const diskData      = ref<Record<number, DiskUsageNodeResult>>({})
const diskError     = ref<Record<number, string>>({})

async function run() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  // reset disk details when refreshing
  diskExpanded.value = {}
  diskData.value     = {}
  diskError.value    = {}
  try {
    rows.value    = await diagnosticsApi.resources(id)
    lastRun.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

async function toggleDiskDetails(nodeId: number) {
  const clusterId = clusterStore.selectedClusterId
  if (!clusterId) return

  // collapse
  if (diskExpanded.value[nodeId]) {
    diskExpanded.value[nodeId] = false
    return
  }

  diskExpanded.value[nodeId] = true

  // already fetched — just show
  if (diskData.value[nodeId]) return

  diskLoading.value[nodeId] = true
  diskError.value[nodeId]   = ''
  try {
    diskData.value[nodeId] = await diagnosticsApi.diskUsage(clusterId, nodeId)
  } catch (e: any) {
    diskError.value[nodeId] = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    diskLoading.value[nodeId] = false
  }
}

watch(() => props.active, (v) => { if (v) run() }, { immediate: true })
watch(() => clusterStore.selectedClusterId, () => { if (props.active) run() })

function pct(used: number | null, total: number | null): number | null {
  if (used === null || total === null || total === 0) return null
  return Math.round((used / total) * 100)
}

function fmtBytes(b: number | null): string {
  if (b === null) return '—'
  if (b >= 1_073_741_824) return (b / 1_073_741_824).toFixed(1) + ' GB'
  if (b >= 1_048_576)     return (b / 1_048_576).toFixed(0) + ' MB'
  return (b / 1024).toFixed(0) + ' KB'
}

function fmtMb(mb: number | null): string {
  if (mb === null) return '—'
  if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB'
  return mb.toFixed(0) + ' MB'
}

type Level = 'ok' | 'warn' | 'crit' | 'unknown'

function level(p: number | null, warnAt: number, critAt: number): Level {
  if (p === null) return 'unknown'
  if (p >= critAt) return 'crit'
  if (p >= warnAt) return 'warn'
  return 'ok'
}

function cardStatusLevel(row: NodeResourceRow): Level {
  if (row.error) return 'crit'
  const levels: Level[] = [
    level(row.cpu_percent, 80, 95),
    level(pct(row.ram_used_bytes, row.ram_total_bytes), 85, 95),
    level(pct(row.disk_used_bytes, row.disk_total_bytes), 80, 90),
  ]
  if (levels.includes('crit'))    return 'crit'
  if (levels.includes('warn'))    return 'warn'
  if (levels.every(l => l === 'unknown')) return 'unknown'
  return 'ok'
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">
        <i class="pi pi-server" />
        <span>System Resources</span>
        <span v-if="lastRun" class="last-run">last run {{ lastRun }}</span>
      </div>
      <button class="btn-run" :disabled="loading" @click="run">
        <i :class="['pi', loading ? 'pi-spin pi-spinner' : 'pi-refresh']" />
        {{ loading ? 'Fetching…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <!-- Skeleton -->
    <div v-if="loading && rows.length === 0" class="cards-grid">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <div class="sk-head" />
        <div class="sk-bar" />
        <div class="sk-bar" />
        <div class="sk-bar" />
        <div class="sk-footer" />
      </div>
    </div>

    <div v-else-if="rows.length === 0 && !error" class="empty-hint">
      <i class="pi pi-info-circle" /> No data.
    </div>

    <div v-else class="cards-grid">
      <div
        v-for="row in rows"
        :key="row.node_id"
        class="res-card"
        :class="`status-${cardStatusLevel(row)}`"
      >
        <!-- Card header -->
        <div class="card-head">
          <div class="node-info">
            <span :class="['status-dot', `dot-${cardStatusLevel(row)}`]" />
            <span class="node-name">{{ row.node_name }}</span>
          </div>
          <span v-if="row.error" class="badge badge-err">SSH error</span>
          <span v-else-if="cardStatusLevel(row) === 'crit'" class="badge badge-err">Critical</span>
          <span v-else-if="cardStatusLevel(row) === 'warn'" class="badge badge-warn">Warning</span>
          <span v-else class="badge badge-ok">Healthy</span>
        </div>

        <div v-if="row.error" class="node-err">
          <i class="pi pi-exclamation-circle" /> {{ row.error }}
        </div>

        <template v-else>
          <div class="divider" />

          <!-- CPU -->
          <div class="metric">
            <div class="metric-top">
              <div class="metric-name">
                <i class="pi pi-microchip metric-icon" />
                <span>CPU</span>
              </div>
              <span class="metric-pct" :class="`pct-${level(row.cpu_percent, 80, 95)}`">
                {{ row.cpu_percent !== null ? row.cpu_percent + '%' : '—' }}
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="`fill-${level(row.cpu_percent, 80, 95)}`"
                :style="{ width: (row.cpu_percent ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- RAM -->
          <div class="metric">
            <div class="metric-top">
              <div class="metric-name">
                <i class="pi pi-database metric-icon" />
                <span>RAM</span>
              </div>
              <span class="metric-pct" :class="`pct-${level(pct(row.ram_used_bytes, row.ram_total_bytes), 85, 95)}`">
                {{ fmtBytes(row.ram_used_bytes) }}
                <span class="pct-total">/ {{ fmtBytes(row.ram_total_bytes) }}</span>
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="`fill-${level(pct(row.ram_used_bytes, row.ram_total_bytes), 85, 95)}`"
                :style="{ width: (pct(row.ram_used_bytes, row.ram_total_bytes) ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- Disk -->
          <div class="metric">
            <div class="metric-top">
              <div class="metric-name">
                <i class="pi pi-hdd metric-icon" />
                <span>Disk</span>
              </div>
              <span class="metric-pct" :class="`pct-${level(pct(row.disk_used_bytes, row.disk_total_bytes), 80, 90)}`">
                {{ fmtBytes(row.disk_used_bytes) }}
                <span class="pct-total">/ {{ fmtBytes(row.disk_total_bytes) }}</span>
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="`fill-${level(pct(row.disk_used_bytes, row.disk_total_bytes), 80, 90)}`"
                :style="{ width: (pct(row.disk_used_bytes, row.disk_total_bytes) ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- Footer stats -->
          <div class="card-footer">
            <div class="stat">
              <span class="stat-label">Load avg (1m)</span>
              <span class="stat-val mono">{{ row.load_avg_1 !== null ? row.load_avg_1.toFixed(2) : '—' }}</span>
            </div>
            <div class="stat-divider" />
            <div class="stat">
              <span class="stat-label">Up since</span>
              <span class="stat-val mono">{{ row.uptime_since ?? '—' }}</span>
            </div>
          </div>

          <!-- Disk Details toggle -->
          <div class="disk-details-toggle" @click="toggleDiskDetails(row.node_id)">
            <i :class="['pi', diskExpanded[row.node_id] ? 'pi-chevron-up' : 'pi-chevron-down']" />
            <span>Disk Details</span>
          </div>

          <!-- Disk Details panel -->
          <div v-if="diskExpanded[row.node_id]" class="disk-details">
            <!-- Loading -->
            <div v-if="diskLoading[row.node_id]" class="disk-loading">
              <i class="pi pi-spin pi-spinner" /> Fetching disk details…
            </div>

            <!-- Error -->
            <div v-else-if="diskError[row.node_id]" class="disk-err">
              <i class="pi pi-exclamation-circle" /> {{ diskError[row.node_id] }}
            </div>

            <template v-else-if="diskData[row.node_id]">
              <!-- ibdata1 + binary logs summary -->
              <div class="disk-summary">
                <div class="disk-stat">
                  <span class="disk-stat-label">ibdata1</span>
                  <span class="disk-stat-val mono">{{ fmtMb(diskData[row.node_id].ibdata1_mb) }}</span>
                </div>
                <div class="disk-stat">
                  <span class="disk-stat-label">Binary logs</span>
                  <span class="disk-stat-val mono">{{ fmtMb(diskData[row.node_id].binary_logs_total_mb) }}</span>
                </div>
              </div>

              <!-- Top tables -->
              <div v-if="diskData[row.node_id].top_tables.length" class="disk-section">
                <div class="disk-section-title">Top 10 tables by size</div>
                <table class="disk-table">
                  <thead>
                    <tr>
                      <th>Schema</th>
                      <th>Table</th>
                      <th class="num">Data</th>
                      <th class="num">Index</th>
                      <th class="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in diskData[row.node_id].top_tables" :key="t.schema + '.' + t.table">
                      <td class="muted">{{ t.schema }}</td>
                      <td>{{ t.table }}</td>
                      <td class="num mono">{{ fmtMb(t.data_mb) }}</td>
                      <td class="num mono">{{ fmtMb(t.index_mb) }}</td>
                      <td class="num mono bold">{{ fmtMb(t.total_mb) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="disk-empty">No user tables found or no DB credentials.</div>

              <!-- Binary logs list -->
              <div v-if="diskData[row.node_id].binary_logs.length" class="disk-section">
                <div class="disk-section-title">Binary logs ({{ diskData[row.node_id].binary_logs.length }})</div>
                <table class="disk-table">
                  <thead>
                    <tr>
                      <th>Log file</th>
                      <th class="num">Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="bl in diskData[row.node_id].binary_logs" :key="bl.log_name">
                      <td class="mono">{{ bl.log_name }}</td>
                      <td class="num mono">{{ fmtBytes(bl.file_size) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- DB error (partial) -->
              <div v-if="diskData[row.node_id].error" class="disk-err">
                <i class="pi pi-exclamation-circle" /> {{ diskData[row.node_id].error }}
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-4);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.last-run {
  font-weight: 400;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin-left: var(--space-2);
}
.btn-run {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-interactive), color var(--transition-interactive);
}
.btn-run:hover:not(:disabled) { background: var(--color-surface-offset); color: var(--color-text); }
.btn-run:disabled { opacity: 0.5; cursor: not-allowed; }

.alert-err {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid oklch(from var(--color-error) l c h / 0.25);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.empty-hint {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-6);
}

.skeleton-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.sk-head, .sk-bar, .sk-footer {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
.sk-head   { height: 20px; width: 60%; }
.sk-bar    { height: 36px; }
.sk-footer { height: 48px; margin-top: var(--space-2); }

.res-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  transition: box-shadow var(--transition-interactive), border-color var(--transition-interactive);
}
.res-card:hover { box-shadow: var(--shadow-md); }
.res-card.status-warn  { border-color: oklch(from var(--color-warning) l c h / 0.35); }
.res-card.status-crit  { border-color: oklch(from var(--color-error)   l c h / 0.35); }

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.node-info { display: flex; align-items: center; gap: var(--space-2); }
.node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
.dot-ok      { background: var(--color-success); box-shadow: 0 0 0 2px oklch(from var(--color-success) l c h / 0.2); }
.dot-warn    { background: var(--color-warning); box-shadow: 0 0 0 2px oklch(from var(--color-warning) l c h / 0.2); }
.dot-crit    { background: var(--color-error);   box-shadow: 0 0 0 2px oklch(from var(--color-error)   l c h / 0.2); }
.dot-unknown { background: var(--color-text-faint); }

.badge {
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
}
.badge-ok   { background: var(--color-success-highlight); color: var(--color-success); }
.badge-warn { background: var(--color-warning-highlight); color: var(--color-warning); }
.badge-err  { background: var(--color-error-highlight);   color: var(--color-error); }

.node-err {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-error);
  font-family: var(--font-mono, monospace);
  word-break: break-all;
  background: var(--color-error-highlight);
  padding: var(--space-3);
  border-radius: var(--radius-md);
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin: 0 calc(-1 * var(--space-2));
}

.metric { display: flex; flex-direction: column; gap: var(--space-2); }

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}
.metric-icon { font-size: 0.7rem; opacity: 0.7; }

.metric-pct {
  font-size: var(--text-sm);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.pct-total {
  font-weight: 400;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin-left: 2px;
}
.pct-ok      { color: var(--color-success); }
.pct-warn    { color: var(--color-warning); }
.pct-crit    { color: var(--color-error); }
.pct-unknown { color: var(--color-text-faint); }

.bar-track {
  height: 6px;
  background: var(--color-surface-offset-2);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  min-width: 2px;
}
.fill-ok      { background: linear-gradient(90deg, var(--color-success), oklch(from var(--color-success) calc(l + 0.08) c h)); }
.fill-warn    { background: linear-gradient(90deg, var(--color-warning), oklch(from var(--color-warning) calc(l + 0.08) c h)); }
.fill-crit    { background: linear-gradient(90deg, var(--color-error),   oklch(from var(--color-error)   calc(l + 0.08) c h)); }
.fill-unknown { background: var(--color-text-faint); }

.card-footer {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}
.stat { display: flex; flex-direction: column; gap: 3px; }
.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stat-val {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}
.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
  flex-shrink: 0;
}
.mono { font-family: var(--font-mono, monospace); font-size: var(--text-xs) !important; }

/* ── Disk Details ── */
.disk-details-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  padding: var(--space-2) 0;
  border-top: 1px solid var(--color-border);
  user-select: none;
  transition: color var(--transition-interactive);
}
.disk-details-toggle:hover { color: var(--color-primary); }
.disk-details-toggle .pi { font-size: 0.65rem; }

.disk-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-3) 0 0;
}

.disk-loading {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.disk-err {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-error);
  background: var(--color-error-highlight);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
}

.disk-summary {
  display: flex;
  gap: var(--space-6);
}
.disk-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.disk-stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.disk-stat-val {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.disk-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.disk-section-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.disk-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
}
.disk-table th {
  text-align: left;
  padding: var(--space-1) var(--space-2);
  color: var(--color-text-faint);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
}
.disk-table th.num,
.disk-table td.num { text-align: right; }
.disk-table td {
  padding: var(--space-1) var(--space-2);
  color: var(--color-text);
  border-bottom: 1px solid oklch(from var(--color-border) l c h / 0.5);
}
.disk-table tr:last-child td { border-bottom: none; }
.disk-table td.muted { color: var(--color-text-muted); }
.disk-table td.bold  { font-weight: 600; }

.disk-empty {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-style: italic;
}
</style>
