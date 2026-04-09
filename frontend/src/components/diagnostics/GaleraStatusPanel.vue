<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Galera status (wsrep_*)"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = !autoRefresh"
    >
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="All nodes"
          size="small"
          style="width: 180px"
          show-clear
      />
    </PanelToolbar>

    <!-- fix: блок ошибки, которого не было в оригинале -->
    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />{{ (error as any)?.message }}
    </div>

    <InputText v-model="search" placeholder="Search status variable…" size="small" class="mb-3 w-full" />

    <DataTable
        :value="filtered"
        :loading="isLoading"
        dataKey="variable_name"
        size="small"
        scrollable
        scroll-height="520px"
    >
      <Column field="variable_name" header="Status variable" style="width: 340px" :sortable="true">
        <template #body="{ data: row }">
          <span class="font-mono text-xs">{{ row.variable_name }}</span>
        </template>
      </Column>
      <Column field="value" header="Value">
        <template #body="{ data: row }">
          <span class="font-mono text-sm" :class="valueClass(row.variable_name, row.value)">
            {{ row.value }}
          </span>
        </template>
      </Column>
      <template #empty><div class="empty-row">No status variables found.</div></template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { DataTable, Column, Select, InputText } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type KVRow } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions } from '@/composables/useNodeOptions'   // ← fix

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const search = ref('')
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()   // ← fix

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({  // ← fix: добавили error
  queryKey: computed(() => ['diag-galera-status', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getGaleraStatus(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  const rows: KVRow[] = data.value ?? []
  if (!search.value.trim()) return rows
  const q = search.value.toLowerCase()
  return rows.filter((r) => r.variable_name.toLowerCase().includes(q) || r.value.toLowerCase().includes(q))
})

function valueClass(name: string, value: string) {
  if (name === 'wsrep_flow_control_sent' && parseInt(value) > 0) return 'text-warning-color font-medium'
  if (name === 'wsrep_cluster_size' && parseInt(value) < 2) return 'text-error-color font-medium'
  if (name === 'wsrep_local_state_comment' && value !== 'Synced') return 'text-warning-color'
  return ''
}
</script>