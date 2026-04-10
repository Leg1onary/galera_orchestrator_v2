<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Galera variables (wsrep_*)"
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

    <InputText
        v-model="search"
        placeholder="Search variable…"
        size="small"
        class="search-input"
    />

    <DataTable
        :value="filtered"
        :loading="isLoading"
        dataKey="variable_name"
        size="small"
        :rows="100"
        scrollable
        scroll-height="520px"
    >
      <Column field="variable_name" header="Variable" style="width: 340px" :sortable="true">
        <template #body="{ data: row }">
          <span class="var-name">{{ row.variable_name }}</span>
        </template>
      </Column>
      <Column field="value" header="Value">
        <template #body="{ data: row }">
          <span class="var-value" :class="valueClass(row.variable_name, row.value)">
            {{ row.value }}
          </span>
        </template>
      </Column>
      <template #empty><div class="empty-row">No variables found.</div></template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import DataTable  from 'primevue/datatable'
import Column     from 'primevue/column'
import Select     from 'primevue/select'
import InputText  from 'primevue/inputtext'
import { useClusterStore }            from '@/stores/cluster'
import { diagnosticsApi, type KVRow } from '@/api/diagnostics'
import PanelToolbar                   from './PanelToolbar.vue'
import { useDiagAutoRefresh }         from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }             from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const search         = ref('')
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-galera-vars',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
  ]),
  queryFn: () =>
      diagnosticsApi.getGaleraVars(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled:        computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  // MINOR fix: переменные статичны в runtime — кешируем 60s
  staleTime:      60_000,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  const rows: KVRow[] = data.value ?? []
  if (!search.value.trim()) return rows
  const q = search.value.toLowerCase()
  return rows.filter(
      (r) => r.variable_name.toLowerCase().includes(q) || r.value.toLowerCase().includes(q)
  )
})

function valueClass(name: string, value: string): string {
  if (name === 'wsrep_cluster_status' && value !== 'Primary') return 'val--error'
  if (name === 'wsrep_connected'      && value !== 'ON')      return 'val--error'
  if (name === 'wsrep_ready'          && value !== 'ON')      return 'val--warning'
  return ''
}
</script>

<style scoped>
.search-input { width: 100%; margin-bottom: var(--space-3); }
.node-select  { width: 180px; }

.var-name  { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.var-value { font-family: var(--font-mono, monospace); font-size: var(--text-sm); }

.val--warning { color: var(--color-warning); font-weight: 500; }
.val--error   { color: var(--color-error);   font-weight: 500; }

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