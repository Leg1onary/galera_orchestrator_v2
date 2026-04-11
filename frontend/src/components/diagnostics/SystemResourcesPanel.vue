<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type NodeResourceRow } from '@/api/diagnostics'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const rows    = ref<NodeResourceRow[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const lastRun = ref<string | null>(null)

async function run() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  try {
    rows.value    = await diagnosticsApi.resources(id)
    lastRun.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
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

function barCls(p: number | null, warnAt: number, critAt: number): string {
  if (p === null) return 'bar-unknown'
  if (p >= critAt) return 'bar-crit'
  if (p >= warnAt) return 'bar-warn'
  return 'bar-ok'
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

    <div v-if="loading && rows.length === 0" class="skeleton-grid">
      <div v-for="i in 3" :key="i" class="skeleton-card" />
    </div>

    <div v-else-if="rows.length === 0 && !error" class="empty-hint">
      <i class="pi pi-info-circle" /> No data.
    </div>

    <div v-else class="cards-grid">
      <div v-for="row in rows" :key="row.node_id" class="res-card" :class="{ 'has-error': !!row.error }">
        <div class="card-head">
          <span class="node-name">{{ row.node_name }}</span>
          <span v-if="row.error" class="err-badge">SSH error</span>
        </div>

        <div v-if="row.error" class="node-err">{{ row.error }}</div>

        <template v-else>
          <!-- CPU -->
          <div class="metric">
            <div class="metric-label">
              <span>CPU</span>
              <span class="metric-val" :class="barCls(row.cpu_percent, 80, 95)">{{ row.cpu_percent !== null ? row.cpu_percent + '%' : '—' }}</span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="barCls(row.cpu_percent, 80, 95)"
                :style="{ width: (row.cpu_percent ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- RAM -->
          <div class="metric">
            <div class="metric-label">
              <span>RAM</span>
              <span class="metric-val" :class="barCls(pct(row.ram_used_bytes, row.ram_total_bytes), 85, 95)">
                {{ fmtBytes(row.ram_used_bytes) }} / {{ fmtBytes(row.ram_total_bytes) }}
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="barCls(pct(row.ram_used_bytes, row.ram_total_bytes), 85, 95)"
                :style="{ width: (pct(row.ram_used_bytes, row.ram_total_bytes) ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- Disk -->
          <div class="metric">
            <div class="metric-label">
              <span>Disk</span>
              <span class="metric-val" :class="barCls(pct(row.disk_used_bytes, row.disk_total_bytes), 80, 90)">
                {{ fmtBytes(row.disk_used_bytes) }} / {{ fmtBytes(row.disk_total_bytes) }}
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="barCls(pct(row.disk_used_bytes, row.disk_total_bytes), 80, 90)"
                :style="{ width: (pct(row.disk_used_bytes, row.disk_total_bytes) ?? 0) + '%' }"
              />
            </div>
          </div>

          <!-- Load / Uptime -->
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">Load avg (1m)</span>
              <span class="meta-val mono">{{ row.load_avg_1 !== null ? row.load_avg_1.toFixed(2) : '—' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Up since</span>
              <span class="meta-val mono">{{ row.uptime_since ?? '—' }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: var(--space-4); }

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
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid oklch(from var(--color-error) l c h / 0.25);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}
.skeleton-card {
  height: 200px;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.res-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.res-card.has-error { border-color: oklch(from var(--color-error) l c h / 0.3); }

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }

.err-badge {
  padding: 2px var(--space-2);
  background: var(--color-error-highlight);
  color: var(--color-error);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}

.node-err {
  font-size: var(--text-xs);
  color: var(--color-error);
  font-family: var(--font-mono, monospace);
  word-break: break-all;
}

.metric { display: flex; flex-direction: column; gap: var(--space-1); }

.metric-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.metric-val { font-weight: 500; }
.metric-val.bar-ok   { color: var(--color-success); }
.metric-val.bar-warn { color: var(--color-warning); }
.metric-val.bar-crit { color: var(--color-error); }
.metric-val.bar-unknown { color: var(--color-text-faint); }

.bar-track {
  height: 4px;
  background: var(--color-surface-offset);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.4s ease;
}
.bar-fill.bar-ok      { background: var(--color-success); }
.bar-fill.bar-warn    { background: var(--color-warning); }
.bar-fill.bar-crit    { background: var(--color-error); }
.bar-fill.bar-unknown { background: var(--color-text-faint); }

.meta-row {
  display: flex;
  gap: var(--space-4);
  margin-top: var(--space-1);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-label { font-size: var(--text-xs); color: var(--color-text-muted); }
.meta-val { font-size: var(--text-xs); color: var(--color-text); }
.mono { font-family: var(--font-mono, monospace); }
</style>
