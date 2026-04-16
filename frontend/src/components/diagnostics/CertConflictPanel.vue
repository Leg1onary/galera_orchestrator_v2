<script setup lang="ts">
/**
 * #14 Certificate Conflict Rate Panel
 * wsrep_local_cert_failures, wsrep_local_replays, wsrep_cert_deps_distance, wsrep_local_bf_aborts.
 */
import { ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import PanelToolbar from './PanelToolbar.vue'
import { recoveryAdvancedApi, type CertConflictNodeResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const rows    = ref<CertConflictNodeResult[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const autoRef = ref(false)
let _interval: ReturnType<typeof setInterval> | null = null

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    rows.value = await recoveryAdvancedApi.getCertConflicts(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })
watch(autoRef, (v) => {
  if (v) { _interval = setInterval(load, 5000) }
  else { if (_interval) clearInterval(_interval); _interval = null }
})

const hasAlerts = () => rows.value.some(r => r.alert)
</script>

<template>
  <div class="panel-wrap">
    <PanelToolbar
      title="Cert Conflict Rate"
      icon="pi-file-times"
      :loading="loading"
      :auto-refresh="autoRef"
      @refresh="load()"
      @toggle-auto="autoRef = !autoRef"
    />

    <Message v-if="hasAlerts()" severity="warn" :closable="false">
      Certificate failures detected — concurrent writes to different nodes are conflicting.
      Consider routing writes to a single node or reducing write concurrency.
    </Message>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <div v-if="loading && !rows.length" class="panel-skeleton">
      <Skeleton v-for="i in 3" :key="i" height="42px" />
    </div>

    <DataTable
      v-else
      :value="rows"
      dataKey="node_id"
      size="small"
      class="settings-table"
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

      <Column header="Cert Failures" style="width: 130px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.wsrep_local_cert_failures !== null"
            :value="String(row.wsrep_local_cert_failures)"
            :severity="row.wsrep_local_cert_failures > 0 ? 'warn' : 'secondary'"
            :icon="row.wsrep_local_cert_failures > 0 ? 'pi pi-exclamation-triangle' : undefined"
            class="mono-tag"
          />
          <span v-else-if="row.error" class="cell-err">Error</span>
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

      <Column header="Replays" style="width: 90px">
        <template #body="{ data: row }">
          <span class="cell-mono" :class="(row.wsrep_local_replays ?? 0) > 0 ? 'cell-warn' : ''">
            {{ row.wsrep_local_replays ?? '—' }}
          </span>
        </template>
      </Column>

      <Column header="BF Aborts" style="width: 100px">
        <template #body="{ data: row }">
          <span class="cell-mono" :class="(row.wsrep_local_bf_aborts ?? 0) > 0 ? 'cell-warn' : ''">
            {{ row.wsrep_local_bf_aborts ?? '—' }}
          </span>
        </template>
      </Column>

      <Column header="Cert Deps Dist" style="width: 130px">
        <template #body="{ data: row }">
          <span class="cell-mono">
            {{ row.wsrep_cert_deps_distance !== null ? row.wsrep_cert_deps_distance.toFixed(2) : '—' }}
          </span>
        </template>
      </Column>
    </DataTable>

    <div class="cert-info">
      <i class="pi pi-info-circle" />
      <span>Cert failures = write transactions rejected due to certification conflict. BF Aborts = transactions killed by Galera applier. High values indicate write contention between nodes.</span>
    </div>
  </div>
</template>

<style scoped>
.panel-wrap { display: flex; flex-direction: column; gap: var(--space-4); }
.panel-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }
.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-warn      { color: var(--color-warning) !important; font-weight: 700; }
.cell-muted     { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-err       { font-size: var(--text-xs); color: var(--color-error); }
.mono-tag :deep(.p-tag-value) { font-family: var(--font-mono); }
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
.cert-info {
  display: flex; gap: var(--space-2); align-items: flex-start;
  font-size: 0.68rem; color: var(--color-text-faint); line-height: 1.5;
  padding-top: var(--space-2); border-top: 1px solid var(--color-border-muted);
}
.cert-info .pi { font-size: 0.75rem; margin-top: 1px; flex-shrink: 0; color: var(--color-info); }
</style>
