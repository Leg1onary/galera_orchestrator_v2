<script setup lang="ts">
import { ref } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ConnectionCheckRow, type CheckAllResponse } from '@/api/diagnostics'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const nodes   = ref<ConnectionCheckRow[]>([])
const arbs    = ref<ConnectionCheckRow[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const lastRun = ref<string | null>(null)

async function runCheck() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  try {
    const res: CheckAllResponse = await diagnosticsApi.checkAll(id)
    nodes.value   = res.nodes        ?? []
    arbs.value    = res.arbitrators  ?? []
    lastRun.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

function statusIcon(ok: boolean | null | undefined) {
  if (ok === null || ok === undefined) return { icon: 'pi-minus-circle', cls: 'st-unknown' }
  return ok ? { icon: 'pi-check-circle', cls: 'st-ok' } : { icon: 'pi-times-circle', cls: 'st-err' }
}

function fmtLatency(ms: number | null | undefined) {
  if (ms === null || ms === undefined) return '—'
  return ms < 1 ? '<1 ms' : `${Math.round(ms)} ms`
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">
        <i class="pi pi-wifi" />
        <span>Connection Check</span>
        <span v-if="lastRun" class="last-run">last run {{ lastRun }}</span>
      </div>
      <button class="btn-run" :disabled="loading" @click="runCheck">
        <i :class="['pi', loading ? 'pi-spin pi-spinner' : 'pi-play']" />
        {{ loading ? 'Checking…' : 'Run Check' }}
      </button>
    </div>

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <div v-if="nodes.length === 0 && arbs.length === 0 && !loading && !error" class="empty-hint">
      <i class="pi pi-info-circle" />
      Click <b>Run Check</b> to test SSH and DB connectivity for all nodes and arbitrators.
    </div>

    <!-- Nodes -->
    <template v-if="nodes.length > 0">
      <div class="section-label">Nodes</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Host</th>
              <th class="center">SSH</th>
              <th class="center">DB</th>
              <th class="center">SSH Latency</th>
              <th class="center">DB Latency</th>
              <th>SSH Error</th>
              <th>DB Error</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in nodes" :key="row.node_id">
              <td class="name-cell">{{ row.node_name }}</td>
              <td class="mono">{{ row.host }}</td>
              <td class="center">
                <i :class="['pi', statusIcon(row.ssh_ok).icon, statusIcon(row.ssh_ok).cls]" />
              </td>
              <td class="center">
                <i :class="['pi', statusIcon(row.db_ok).icon, statusIcon(row.db_ok).cls]" />
              </td>
              <td class="center mono">{{ fmtLatency(row.ssh_latency_ms) }}</td>
              <td class="center mono">{{ fmtLatency(row.db_latency_ms) }}</td>
              <td class="error-cell mono">{{ row.ssh_error ?? '—' }}</td>
              <td class="error-cell mono">{{ row.db_error ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Arbitrators -->
    <template v-if="arbs.length > 0">
      <div class="section-label" style="margin-top: var(--space-6)">Arbitrators</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Host</th>
              <th class="center">SSH</th>
              <th class="center">garbd</th>
              <th class="center">SSH Latency</th>
              <th>SSH Error</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in arbs" :key="row.node_id">
              <td class="name-cell">{{ row.node_name }}</td>
              <td class="mono">{{ row.host }}</td>
              <td class="center">
                <i :class="['pi', statusIcon(row.ssh_ok).icon, statusIcon(row.ssh_ok).cls]" />
              </td>
              <td class="center">
                <i :class="['pi', statusIcon(row.garbd_running).icon, statusIcon(row.garbd_running).cls]" />
              </td>
              <td class="center mono">{{ fmtLatency(row.latency_ssh_ms ?? row.ssh_latency_ms) }}</td>
              <td class="error-cell mono">{{ row.ssh_error ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
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
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-interactive);
}
.btn-run:hover:not(:disabled) { background: var(--color-primary-hover); }
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
  padding: var(--space-5) var(--space-6);
  background: var(--color-surface-2);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.section-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
thead { background: var(--color-surface-2); }
th {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
}
td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--color-surface-2); }

.center { text-align: center; }
.mono { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.name-cell { font-weight: 500; }
.error-cell { color: var(--color-text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.st-ok      { color: var(--color-success); }
.st-err     { color: var(--color-error); }
.st-unknown { color: var(--color-text-faint); }
</style>
