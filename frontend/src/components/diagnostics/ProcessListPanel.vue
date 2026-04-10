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
    >
      <template #header>
        <!-- MAJOR fix: utility классы → scoped CSS -->
        <div class="table-header">
          <InputText
              v-model="search"
              placeholder="Filter by user, db, query…"
              size="small"
              class="search-input"
          />
          <ToggleSwitch v-model="hideSystem" />
          <span class="hide-label">Hide system</span>
        </div>
      </template>

      <Column field="id"      header="ID"       style="width: 70px"  :sortable="true" />
      <Column field="user"    header="User"     style="width: 120px" :sortable="true" />
      <Column field="host"    header="Host"     style="width: 140px">
        <template #body="{ data }">
          <!-- MAJOR fix: font-mono text-xs → scoped класс -->
          <span class="mono-xs">{{ data.host }}</span>
        </template>
      </Column>
      <Column field="db"      header="DB"       style="width: 100px">
        <template #body="{ data }">{{ data.db ?? '—' }}</template>
      </Column>
      <Column field="command" header="Command"  style="width: 100px" />
      <Column field="time"    header="Time (s)" style="width: 90px"  :sortable="true">
        <template #body="{ data }">
          <!-- MAJOR fix: utility классы → scoped -->
          <span :class="data.time > SLOW_QUERY_SEC ? 'val--warning' : ''">
            {{ data.time }}
          </span>
        </template>
      </Column>
      <Column field="state"   header="State"    style="width: 130px">
        <template #body="{ data }">{{ data.state ?? '—' }}</template>
      </Column>
      <Column field="info"    header="Query">
        <template #body="{ data }">
          <span
              v-if="data.info"
              class="mono-xs query-cell"
              :title="data.info"
          >
            {{ data.info.slice(0, 120) }}{{ data.info.length > 120 ? '…' : '' }}
          </span>
          <!-- MAJOR fix: text-muted-color → scoped -->
          <span v-else class="text-muted">—</span>
        </template>
      </Column>
      <Column header="" style="width: 70px">
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
        <div class="empty-row">No active processes.</div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
// BLOCKER fix: раздельные импорты
import DataTable    from 'primevue/datatable'
import Column       from 'primevue/column'
import Button       from 'primevue/button'
import Select       from 'primevue/select'
import InputText    from 'primevue/inputtext'
import ToggleSwitch from 'primevue/toggleswitch'
// BLOCKER fix: useToast из правильного пути
import { useToast } from 'primevue/usetoast'
import { useClusterStore }                  from '@/stores/cluster'
import { diagnosticsApi, type ProcessRow }  from '@/api/diagnostics'
import PanelToolbar                         from './PanelToolbar.vue'
import { useDiagAutoRefresh }               from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                   from '@/composables/useNodeOptions'

// MINOR fix: константа вместо хардкода
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
  queryKey: computed(() => [
    'diag-processes',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
  ]),
  queryFn: () =>
      diagnosticsApi.getProcessList(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled:        computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime:      0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  let rows: ProcessRow[] = data.value ?? []
  if (hideSystem.value) {
    rows = rows.filter((r) => r.command !== 'Daemon' && r.user !== 'system user')
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    rows = rows.filter(
        (r) =>
            r.user.toLowerCase().includes(q) ||
            (r.db   ?? '').toLowerCase().includes(q) ||
            (r.info ?? '').toLowerCase().includes(q),
    )
  }
  return rows
})

async function handleKill(row: ProcessRow) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return
  killing.value = row.id
  try {
    const res = await diagnosticsApi.killProcess(
        clusterStore.selectedClusterId,
        selectedNodeId.value,
        row.id,
    )
    toast.add({
      severity: res.killed ? 'success' : 'warn',
      summary:  res.killed ? `Killed process ${row.id}` : 'Kill failed',
      detail:   res.message,
      life:     3000,
    })
    refetch()
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary:  'Error',
      detail:   err?.response?.data?.detail ?? err.message,
      life:     5000,
    })
  } finally {
    killing.value = null
  }
}
</script>

<style scoped>
.node-select  { width: 180px; }
.search-input { width: 260px; }

/* MAJOR fix: utility классы → scoped */
.table-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.hide-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.mono-xs   { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.val--warning { color: var(--color-warning); font-weight: 500; }
.text-muted   { color: var(--color-text-muted); }

.query-cell {
  display: block;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  margin-bottom: var(--space-3);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.empty-row {
  padding: var(--space-4);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>