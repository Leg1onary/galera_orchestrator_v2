<script setup lang="ts">
/**
 * #11 Flow Control Monitor
 * Live wsrep_flow_control_paused per node.
 * Alert if paused > 5%.
 */
import { ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import PanelToolbar from './PanelToolbar.vue'
import { recoveryAdvancedApi, type FlowControlNodeResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const rows    = ref<FlowControlNodeResult[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const autoRef = ref(false)
let _interval: ReturnType<typeof setInterval> | null = null

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    rows.value = await recoveryAdvancedApi.getFlowControl(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error loading flow control data'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })
watch(autoRef, (v) => {
  if (v) { _interval = setInterval(load, 5000) }
  else { if (_interval) clearInterval(_interval); _interval = null }
})

function fmtPaused(v: number | null): string {
  if (v === null) return '—'
  return (v * 100).toFixed(2) + '%'
}
function fmtFloat(v: number | null): string {
  if (v === null) return '—'
  return v.toFixed(4)
}
function pausedSeverity(v: number | null): 'danger' | 'warn' | 'secondary' {
  if (v === null) return 'secondary'
  if (v > 0.1) return 'danger'
  if (v > 0.05) return 'warn'
  return 'secondary'
}
const hasAlerts = () => rows.value.some(r => r.alert)
</script>

<template>
  <div class="panel-wrap">
    <PanelToolbar
      title="Flow Control Monitor"
      icon="pi-wave-pulse"
      :loading="loading"
      :auto-refresh="autoRef"
      @refresh="load()"
      @toggle-auto="autoRef = !autoRef"
    />

    <Message v-if="hasAlerts()" severity="warn" :closable="false" class="fc-alert-msg">
      <span>Flow control is active on one or more nodes — write throughput is being throttled.</span>
    </Message>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <div v-if="loading && !rows.length" class="panel-skeleton">
      <Skeleton v-for="i in 3" :key="i" height="42px" class="mb-2" />
    </div>

    <DataTable
      v-else
      :value="rows"
      dataKey="node_id"
      size="small"
      class="settings-table fc-table"
      :loading="loading && rows.length > 0"
    >
      <template #empty>
        <div class="panel-empty"><i class="pi pi-inbox" /><span>No data</span></div>
      </template>

      <Column field="node_name" header="Node">
        <template #body="{ data: row }">
          <div class="cell-node">
            <span class="cell-node-name">{{ row.node_name }}</span>
            <span class="cell-node-host">{{ row.host }}</span>
          </div>
        </template>
      </Column>

      <Column header="Paused" style="width: 120px">
        <template #body="{ data: row }">
          <span v-if="row.error" class="cell-err">SSH/DB error</span>
          <Tag
            v-else
            :value="fmtPaused(row.wsrep_flow_control_paused)"
            :severity="pausedSeverity(row.wsrep_flow_control_paused)"
            :icon="row.alert ? 'pi pi-exclamation-triangle' : undefined"
            class="mono-tag"
          />
        </template>
      </Column>

      <Column header="FC Sent" style="width: 90px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ row.wsrep_flow_control_sent ?? '—' }}</span>
        </template>
      </Column>

      <Column header="FC Recv" style="width: 90px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ row.wsrep_flow_control_recv ?? '—' }}</span>
        </template>
      </Column>

      <Column header="Recv Queue Avg" style="width: 130px">
        <template #body="{ data: row }">
          <span class="cell-mono" :class="(row.wsrep_local_recv_queue_avg ?? 0) > 1 ? 'cell-warn' : ''">
            {{ fmtFloat(row.wsrep_local_recv_queue_avg) }}
          </span>
        </template>
      </Column>

      <Column header="Send Queue Avg" style="width: 130px">
        <template #body="{ data: row }">
          <span class="cell-mono" :class="(row.wsrep_local_send_queue_avg ?? 0) > 1 ? 'cell-warn' : ''">
            {{ fmtFloat(row.wsrep_local_send_queue_avg) }}
          </span>
        </template>
      </Column>
    </DataTable>

    <div class="fc-legend">
      <span class="fc-legend-item"><span class="fc-dot fc-dot--ok" />0% — No throttling</span>
      <span class="fc-legend-item"><span class="fc-dot fc-dot--warn" />&gt;5% — Warn threshold</span>
      <span class="fc-legend-item"><span class="fc-dot fc-dot--err" />&gt;10% — Alert: writes throttled</span>
    </div>
  </div>
</template>

<style scoped>
.panel-wrap { display: flex; flex-direction: column; gap: var(--space-4); }
.panel-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }
.mb-2 { margin-bottom: var(--space-2); }

.fc-alert-msg { width: 100%; }

.cell-node        { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name   { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host   { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono        { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-warn        { color: var(--color-warning) !important; font-weight: 700; }
.cell-err         { font-size: var(--text-xs); color: var(--color-error); }
.mono-tag :deep(.p-tag-value) { font-family: var(--font-mono); font-size: var(--text-xs); }

.panel-empty {
  display: flex; align-items: center; gap: var(--space-3);
  color: var(--color-text-faint); padding: var(--space-6); font-size: var(--text-sm);
}

:deep(.settings-table .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.settings-table .p-datatable-thead > tr > th) {
  padding: var(--space-4) var(--space-6) !important; font-size: var(--text-xs) !important;
  font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--color-text-faint) !important; background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important; vertical-align: middle;
}
:deep(.settings-table .p-datatable-tbody > tr:hover > td) { background: rgba(45,212,191,0.04) !important; }

.fc-legend {
  display: flex; gap: var(--space-4); flex-wrap: wrap;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-muted);
}
.fc-legend-item { display: flex; align-items: center; gap: var(--space-2); font-size: 0.68rem; color: var(--color-text-faint); }
.fc-dot { width: 7px; height: 7px; border-radius: 50%; }
.fc-dot--ok   { background: var(--color-synced); }
.fc-dot--warn { background: var(--color-warning); }
.fc-dot--err  { background: var(--color-error); }
</style>
