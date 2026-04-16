<script setup lang="ts">
/**
 * #13 Disk Space Sentinel — Galera-aware disk check.
 * gcache.size vs actual galera.cache, ibdata1, free space.
 */
import { ref, watch, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import PanelToolbar from './PanelToolbar.vue'
import { recoveryAdvancedApi, type DiskSentinelNodeResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const rows    = ref<DiskSentinelNodeResult[]>([])
const loading = ref(false)
const error   = ref<string | null>(null)
const autoRef = ref(false)
let _interval: ReturnType<typeof setInterval> | null = null

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    rows.value = await recoveryAdvancedApi.getDiskSentinel(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })
watch(autoRef, (v) => {
  if (v) { _interval = setInterval(load, 10000) }
  else { if (_interval) clearInterval(_interval); _interval = null }
})

const hasAlerts = computed(() => rows.value.some(r =>
  r.alert_free_space || r.alert_gcache_overflow || r.alert_ibdata1_large
))

function fmtBytes(b: number | null): string {
  if (b === null) return '—'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(1) + ' MB'
  return (b / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function diskUsePct(row: DiskSentinelNodeResult): number | null {
  if (!row.datadir_total_bytes || !row.datadir_free_bytes) return null
  const used = row.datadir_total_bytes - row.datadir_free_bytes
  return Math.round((used / row.datadir_total_bytes) * 100)
}

function diskSeverity(row: DiskSentinelNodeResult): 'danger' | 'warn' | 'secondary' {
  if (row.alert_free_space) return 'danger'
  const pct = diskUsePct(row)
  if (pct !== null && pct > 85) return 'warn'
  return 'secondary'
}
</script>

<template>
  <div class="panel-wrap">
    <PanelToolbar
      title="Disk Space Sentinel"
      icon="pi-database"
      :loading="loading"
      :auto-refresh="autoRef"
      @refresh="load()"
      @toggle-auto="autoRef = !autoRef"
    />

    <Message v-if="hasAlerts" severity="warn" :closable="false">
      Disk space issues detected — check nodes below for details.
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
    >
      <template #empty>
        <div class="panel-empty"><i class="pi pi-inbox" /><span>No data</span></div>
      </template>

      <Column field="node_name" header="Node">
        <template #body="{ data: row }">
          <div class="cell-node">
            <span class="cell-node-name">{{ row.node_name }}</span>
            <span class="cell-node-host">{{ row.host }}</span>
            <span v-if="row.sst_method" class="cell-sst">SST: {{ row.sst_method }}</span>
          </div>
        </template>
      </Column>

      <Column header="Free Space" style="width: 140px">
        <template #body="{ data: row }">
          <div v-if="row.error" class="cell-err">{{ row.error.slice(0, 40) }}</div>
          <div v-else class="cell-disk">
            <Tag
              :value="fmtBytes(row.datadir_free_bytes)"
              :severity="diskSeverity(row)"
              :icon="row.alert_free_space ? 'pi pi-exclamation-triangle' : undefined"
              class="mono-tag"
            />
            <span v-if="diskUsePct(row) !== null" class="disk-pct">
              {{ diskUsePct(row) }}% used
            </span>
          </div>
        </template>
      </Column>

      <Column header="gcache (conf)" style="width: 130px">
        <template #body="{ data: row }">
          <span class="cell-mono">{{ fmtBytes(row.gcache_configured_bytes) }}</span>
        </template>
      </Column>

      <Column header="gcache (file)" style="width: 130px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.alert_gcache_overflow"
            :value="fmtBytes(row.gcache_file_size_bytes)"
            severity="warn"
            icon="pi pi-exclamation-triangle"
            class="mono-tag"
          />
          <span v-else class="cell-mono">{{ fmtBytes(row.gcache_file_size_bytes) }}</span>
        </template>
      </Column>

      <Column header="ibdata1" style="width: 110px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.alert_ibdata1_large"
            :value="fmtBytes(row.ibdata1_size_bytes)"
            severity="warn"
            icon="pi pi-exclamation-triangle"
            class="mono-tag"
          />
          <span v-else class="cell-mono">{{ fmtBytes(row.ibdata1_size_bytes) }}</span>
        </template>
      </Column>
    </DataTable>

    <div class="sentinel-info">
      <i class="pi pi-info-circle" />
      <span>
        <strong>gcache overflow:</strong> file size &gt; configured × 1.2 — next rejoin may force SST instead of IST.
        <strong>ibdata1 large:</strong> &gt;10 GB — cannot shrink without full data dump/restore.
        <strong>Free space alert:</strong> &lt;10 GB on data directory.
      </span>
    </div>
  </div>
</template>

<style scoped>
.panel-wrap { display: flex; flex-direction: column; gap: var(--space-4); }
.panel-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }
.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-sst       { font-size: 0.65rem; color: var(--color-text-faint); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-err       { font-size: var(--text-xs); color: var(--color-error); }
.cell-disk      { display: flex; flex-direction: column; gap: 2px; }
.disk-pct       { font-size: 0.65rem; color: var(--color-text-faint); font-family: var(--font-mono); }
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
.sentinel-info {
  display: flex; gap: var(--space-2); align-items: flex-start;
  font-size: 0.68rem; color: var(--color-text-faint); line-height: 1.6;
  padding-top: var(--space-2); border-top: 1px solid var(--color-border-muted);
}
.sentinel-info .pi { font-size: 0.75rem; margin-top: 1px; flex-shrink: 0; color: var(--color-info); }
.sentinel-info strong { color: var(--color-text-muted); font-weight: 600; }
</style>
