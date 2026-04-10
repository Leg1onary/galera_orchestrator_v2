<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Process list"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    >
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="All nodes"
          size="small"
          class="node-select"
          show-clear
      />
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <div class="table-wrap">
      <DataTable
          :value="filtered"
          :loading="isLoading"
          dataKey="id"
          size="small"
          :rows="50"
          paginator
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink"
          sort-field="time"
          :sort-order="-1"
          class="diag-table"
      >
        <template #header>
          <div class="table-header">
            <InputText
                v-model="search"
                placeholder="Filter by user, db, query…"
                size="small"
                class="search-input"
            />
            <div class="toggle-row">
              <ToggleSwitch v-model="hideSystem" />
              <span class="toggle-label">Hide system</span>
            </div>
          </div>
        </template>

        <Column field="id"      header="ID"       style="width: 70px"  :sortable="true">
          <template #body="{ data }"><span class="cell-mono cell-dim">{{ data.id }}</span></template>
        </Column>
        <Column field="user"    header="User"     style="width: 120px" :sortable="true">
          <template #body="{ data }"><span class="cell-user">{{ data.user }}</span></template>
        </Column>
        <Column field="host"    header="Host"     style="width: 140px">
          <template #body="{ data }"><span class="cell-mono cell-sm">{{ data.host }}</span></template>
        </Column>
        <Column field="db"      header="DB"       style="width: 100px">
          <template #body="{ data }">
            <span v-if="data.db" class="cell-db">{{ data.db }}</span>
            <span v-else class="cell-muted">—</span>
          </template>
        </Column>
        <Column field="command" header="Command"  style="width: 100px">
          <template #body="{ data }"><span class="cell-sm">{{ data.command }}</span></template>
        </Column>
        <Column field="time"    header="Time (s)" style="width: 90px"  :sortable="true">
          <template #body="{ data }">
            <span
              class="cell-mono cell-time"
              :class="{ 'cell-time--warn': data.time > SLOW_QUERY_SEC }"
            >{{ data.time }}</span>
          </template>
        </Column>
        <Column field="state"   header="State"    style="width: 130px">
          <template #body="{ data }">
            <span v-if="data.state" class="state-badge">{{ data.state }}</span>
            <span v-else class="cell-muted">—</span>
          </template>
        </Column>
        <Column field="info"    header="Query">
          <template #body="{ data }">
            <span v-if="data.info" class="cell-mono cell-query" :title="data.info">
              {{ data.info.slice(0, 120) }}{{ data.info.length > 120 ? '…' : '' }}
            </span>
            <span v-else class="cell-muted">—</span>
          </template>
        </Column>
        <Column header="" style="width: 48px">
          <template #body="{ data }">
            <Button
                v-if="data.command !== 'Daemon'"
                icon="pi pi-times"
                text
                rounded
                size="small"
                severity="danger"
                v-tooltip="selectedNodeId ? 'KILL ' + data.id : 'Select a node first'"
                :disabled="!selectedNodeId"
                :loading="killing === data.id"
                @click="handleKill(data)"
            />
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-inbox" />
            No active processes.
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
import DataTable    from 'primevue/datatable'
import Column       from 'primevue/column'
import Button       from 'primevue/button'
import Select       from 'primevue/select'
import InputText    from 'primevue/inputtext'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import { useClusterStore }                  from '@/stores/cluster'
import { diagnosticsApi, type ProcessRow }  from '@/api/diagnostics'
import PanelToolbar                         from './PanelToolbar.vue'
import { useDiagAutoRefresh }               from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                   from '@/composables/useNodeOptions'

const SLOW_QUERY_SEC = 10

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const toast          = useToast()
const selectedNodeId = ref<number | undefined>(undefined)
const search         = ref('')
const hideSystem     = ref(true)
const killing        = ref<number | null>(null)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-processes', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getProcessList(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  let rows: ProcessRow[] = data.value ?? []
  if (hideSystem.value) rows = rows.filter((r) => r.command !== 'Daemon' && r.user !== 'system user')
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    rows = rows.filter((r) =>
        r.user.toLowerCase().includes(q) ||
        (r.db ?? '').toLowerCase().includes(q) ||
        (r.info ?? '').toLowerCase().includes(q)
    )
  }
  return rows
})

async function handleKill(row: ProcessRow) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return
  killing.value = row.id
  try {
    const res = await diagnosticsApi.killProcess(clusterStore.selectedClusterId, selectedNodeId.value, row.id)
    toast.add({ severity: res.killed ? 'success' : 'warn', summary: res.killed ? `Killed process ${row.id}` : 'Kill failed', detail: res.message, life: 3000 })
    refetch()
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err?.response?.data?.detail ?? err.message, life: 5000 })
  } finally {
    killing.value = null
  }
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }
.node-select  { width: 180px; }
.search-input { width: 260px; }

/* TABLE WRAP */
.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-1);
}
.toggle-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.toggle-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* CELL STYLES */
.cell-mono  { font-family: var(--font-mono, monospace); }
.cell-sm    { font-size: var(--text-xs); }
.cell-dim   { color: var(--color-text-faint); font-size: var(--text-xs); font-variant-numeric: tabular-nums; }
.cell-user  { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.cell-db    { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-primary); }
.cell-muted { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-time  { font-size: var(--text-sm); font-variant-numeric: tabular-nums; color: var(--color-text); }
.cell-time--warn { color: var(--color-warning); font-weight: 600; }
.cell-query {
  display: block;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* STATE BADGE */
.state-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: var(--radius-full);
  background: var(--color-surface-dynamic);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

/* ERROR */
.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error);
  font-size: var(--text-sm);
}

/* EMPTY */
.empty-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-8);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
}
</style>
