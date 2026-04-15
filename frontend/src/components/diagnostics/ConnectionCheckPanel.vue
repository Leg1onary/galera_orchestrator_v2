<script setup lang="ts">
import { ref, computed, toRef } from 'vue'
import DataTable from 'primevue/datatable'
import Column    from 'primevue/column'
import { useClusterStore } from '@/stores/cluster'
import { useSettingsStore } from '@/stores/settings'
import { diagnosticsApi, type ConnectionCheckRow, type CheckAllResponse } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore  = useClusterStore()
const settingsStore = useSettingsStore()

const intervalMs = computed(() => settingsStore.pollingIntervalSec * 1000)
const { autoRefresh } = useDiagAutoRefresh(toRef(props, 'active'), intervalMs)

const nodes   = ref<ConnectionCheckRow[]>([])
const arbs    = ref<ConnectionCheckRow[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const fetchedAt = ref<string | null>(null)

async function runCheck() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  try {
    const res: CheckAllResponse = await diagnosticsApi.checkAll(id)
    nodes.value   = res.nodes        ?? []
    arbs.value    = res.arbitrators  ?? []
    fetchedAt.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

// Latency display: arbitrator rows may use latency_ssh_ms or ssh_latency_ms
function arbLatency(row: ConnectionCheckRow): number | null {
  return row.latency_ssh_ms ?? row.ssh_latency_ms ?? null
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
    <PanelToolbar
      title="connection_check"
      :loading="loading"
      :fetched-at="fetchedAt"
      :auto-refresh="autoRefresh"
      @refresh="runCheck"
      @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <div v-if="nodes.length === 0 && arbs.length === 0 && !loading && !error" class="empty-hint">
      <i class="pi pi-info-circle" />
      Click <b>Refresh</b> to test SSH and DB connectivity for all nodes and arbitrators.
    </div>

    <!-- Nodes -->
    <template v-if="nodes.length > 0">
      <div class="section-label">Nodes</div>
      <DataTable
        :value="nodes"
        class="conn-table"
        :row-hover="true"
        size="small"
      >
        <Column field="node_name" header="Name">
          <template #body="{ data: row }">
            <span class="name-cell">{{ row.node_name }}</span>
          </template>
        </Column>
        <Column field="host" header="Host">
          <template #body="{ data: row }">
            <span class="mono">{{ row.host }}</span>
          </template>
        </Column>
        <Column header="SSH" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center">
              <i :class="['pi', statusIcon(row.ssh_ok).icon, statusIcon(row.ssh_ok).cls]" />
            </div>
          </template>
        </Column>
        <Column header="DB" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center">
              <i :class="['pi', statusIcon(row.db_ok).icon, statusIcon(row.db_ok).cls]" />
            </div>
          </template>
        </Column>
        <Column header="SSH Latency" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center mono">{{ fmtLatency(row.ssh_latency_ms) }}</div>
          </template>
        </Column>
        <Column header="DB Latency" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center mono">{{ fmtLatency(row.db_latency_ms) }}</div>
          </template>
        </Column>
        <Column header="SSH Error">
          <template #body="{ data: row }">
            <span class="error-cell mono">{{ row.ssh_error ?? '—' }}</span>
          </template>
        </Column>
        <Column header="DB Error">
          <template #body="{ data: row }">
            <span class="error-cell mono">{{ row.db_error ?? '—' }}</span>
          </template>
        </Column>
      </DataTable>
    </template>

    <!-- Arbitrators -->
    <template v-if="arbs.length > 0">
      <div class="section-label" style="margin-top: var(--space-6)">Arbitrators</div>
      <DataTable
        :value="arbs"
        class="conn-table"
        :row-hover="true"
        size="small"
      >
        <Column field="node_name" header="Name">
          <template #body="{ data: row }">
            <span class="name-cell">{{ row.node_name }}</span>
          </template>
        </Column>
        <Column field="host" header="Host">
          <template #body="{ data: row }">
            <span class="mono">{{ row.host }}</span>
          </template>
        </Column>
        <Column header="SSH" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center">
              <i :class="['pi', statusIcon(row.ssh_ok).icon, statusIcon(row.ssh_ok).cls]" />
            </div>
          </template>
        </Column>
        <Column header="garbd" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center">
              <i :class="['pi', statusIcon(row.garbd_running).icon, statusIcon(row.garbd_running).cls]" />
            </div>
          </template>
        </Column>
        <Column header="SSH Latency" header-class="center-header">
          <template #body="{ data: row }">
            <div class="center mono">{{ fmtLatency(arbLatency(row)) }}</div>
          </template>
        </Column>
        <Column header="SSH Error">
          <template #body="{ data: row }">
            <span class="error-cell mono">{{ row.ssh_error ?? '—' }}</span>
          </template>
        </Column>
      </DataTable>
    </template>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: var(--space-4); }

.alert-err {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid rgba(248,113,113,0.25);
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

/* ── DataTable overrides ── */
:deep(.conn-table .p-datatable-table-container) {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
:deep(.conn-table .p-datatable-thead > tr > th) {
  padding: var(--space-2) var(--space-3) !important;
  font-size: var(--text-xs) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted) !important;
  background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.conn-table .p-datatable-thead > tr > th.center-header) {
  text-align: center !important;
}
:deep(.conn-table .p-datatable-tbody > tr > td) {
  padding: var(--space-2) var(--space-3) !important;
  border-bottom: 1px solid var(--color-border) !important;
  color: var(--color-text);
  vertical-align: middle;
}
:deep(.conn-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none !important;
}
:deep(.conn-table .p-datatable-tbody > tr:hover > td) {
  background: var(--color-surface-2) !important;
}

.center      { text-align: center; }
.mono        { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.name-cell   { font-weight: 500; }
.error-cell  { color: var(--color-text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }

.st-ok      { color: var(--color-success); }
.st-err     { color: var(--color-error); }
.st-unknown { color: var(--color-text-faint); }
</style>
