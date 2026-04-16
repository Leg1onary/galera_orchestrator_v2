<script setup lang="ts">
/**
 * #8 IST vs SST Decision Helper
 * Shows per-node: gcache size, wsrep_local_cached_downtime, sst_method, ist_likely assessment.
 */
import { ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import { recoveryAdvancedApi, type IstSstNodeInfo } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const rows    = ref<IstSstNodeInfo[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    const res = await recoveryAdvancedApi.getIstSstInfo(props.clusterId)
    rows.value = res.nodes
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })

function fmtBytes(b: number | null): string {
  if (b === null) return '—'
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + ' KB'
  if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(0) + ' MB'
  return (b / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function fmtDowntime(sec: number | null): string {
  if (sec === null) return '—'
  if (sec < 60)  return sec + 's'
  if (sec < 3600) return Math.floor(sec / 60) + 'm'
  return (sec / 3600).toFixed(1) + 'h'
}

const hasSstRisk = () => rows.value.some(r => r.ist_likely === false)
</script>

<template>
  <div class="ist-panel">

    <div class="ist-header">
      <div>
        <h3 class="ist-title">IST vs SST Helper</h3>
        <p class="ist-desc">
          Before rejoining a node, check whether Incremental State Transfer (IST) or full SST will be used.
          SST is expensive — it blocks the donor and transfers the full dataset.
        </p>
      </div>
      <Button icon="pi pi-refresh" label="Check" size="small" :loading="loading" @click="load()" />
    </div>

    <Message v-if="hasSstRisk()" severity="warn" :closable="false">
      One or more nodes will likely trigger a full SST on next rejoin.
      Consider rejoining during low-traffic windows or increasing gcache.size.
    </Message>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <div v-if="loading && !rows.length" class="ist-skeleton">
      <Skeleton v-for="i in 3" :key="i" height="52px" />
    </div>

    <DataTable
      v-else
      :value="rows"
      dataKey="node_id"
      size="small"
      class="settings-table"
    >
      <template #empty>
        <div class="panel-empty"><i class="pi pi-inbox" /><span>No nodes</span></div>
      </template>

      <Column field="node_name" header="Node">
        <template #body="{ data: row }">
          <div class="cell-node">
            <span class="cell-node-name">{{ row.node_name }}</span>
            <span class="cell-node-host">{{ row.host }}</span>
          </div>
        </template>
      </Column>

      <Column header="Assessment" style="width: 120px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.ist_likely === true"
            value="IST likely"
            severity="success"
            icon="pi pi-check"
          />
          <Tag
            v-else-if="row.ist_likely === false"
            value="SST likely"
            severity="warn"
            icon="pi pi-exclamation-triangle"
          />
          <span v-else-if="row.error" class="cell-err">Error</span>
          <span v-else class="cell-muted">Unknown</span>
        </template>
      </Column>

      <Column header="wsrep_local_state" style="width: 150px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ row.wsrep_local_state_comment ?? '—' }}</span>
        </template>
      </Column>

      <Column header="Cached downtime" style="width: 140px">
        <template #body="{ data: row }">
          <span class="cell-mono" :class="(row.wsrep_local_cached_downtime ?? 0) > 600 ? 'cell-warn' : ''">
            {{ fmtDowntime(row.wsrep_local_cached_downtime) }}
          </span>
        </template>
      </Column>

      <Column header="gcache (conf)" style="width: 120px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ fmtBytes(row.gcache_size_bytes) }}</span>
        </template>
      </Column>

      <Column header="gcache (file)" style="width: 120px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ fmtBytes(row.gcache_file_size_bytes) }}</span>
        </template>
      </Column>

      <Column header="SST method" style="width: 100px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.sst_method"
            :value="row.sst_method"
            severity="secondary"
            class="mono-tag"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

    </DataTable>

    <div class="ist-legend">
      <div class="ist-legend-item">
        <Tag value="IST likely" severity="success" /><span>Node was offline &lt;10min AND gcache &gt;128MB — fast incremental sync expected.</span>
      </div>
      <div class="ist-legend-item">
        <Tag value="SST likely" severity="warn" /><span>Long downtime OR small gcache — full data copy will be triggered, blocking the donor.</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ist-panel { display: flex; flex-direction: column; gap: var(--space-4); }
.ist-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); }
.ist-title  { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: -0.02em; }
.ist-desc   { font-size: var(--text-xs); color: var(--color-text-muted); margin: 0; max-width: 60ch; line-height: 1.5; }
.ist-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }
.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-warn      { color: var(--color-warning) !important; font-weight: 700; }
.cell-muted     { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-err       { font-size: var(--text-xs); color: var(--color-error); }
.mono-tag :deep(.p-tag-value) { font-family: var(--font-mono); }
.panel-empty { display: flex; align-items: center; gap: var(--space-3); color: var(--color-text-faint); padding: var(--space-6); font-size: var(--text-sm); }
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
.ist-legend { display: flex; flex-direction: column; gap: var(--space-2); padding-top: var(--space-2); border-top: 1px solid var(--color-border-muted); }
.ist-legend-item { display: flex; align-items: center; gap: var(--space-3); font-size: 0.68rem; color: var(--color-text-faint); }
</style>
