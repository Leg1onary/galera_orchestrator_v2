<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Slow queries"
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
      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-color">Min latency (ms)</span>
        <InputNumber
            v-model="minLatencyMs"
            :min="0"
            :step="500"
            size="small"
            style="width: 100px"
            @keydown.enter="refetch()"
        />
      </div>
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />{{ (error as any)?.message }}
    </div>

    <DataTable
        :value="data ?? []"
        :loading="isLoading"
        dataKey="query_digest"
        size="small"
        sort-field="avg_latency_ms"
        :sort-order="-1"
    >
      <Column field="query_digest" header="Query digest">
        <template #body="{ data: row }">
          <span class="font-mono text-xs">
            {{ row.query_digest.slice(0, 140) }}{{ row.query_digest.length > 140 ? '…' : '' }}
          </span>
        </template>
      </Column>
      <Column field="schema_name" header="Schema" style="width: 120px">
        <template #body="{ data: row }">{{ row.schema_name ?? '—' }}</template>
      </Column>
      <Column field="exec_count" header="Exec" style="width: 80px" :sortable="true" />
      <Column field="avg_latency_ms" header="Avg (ms)" style="width: 100px" :sortable="true">
        <template #body="{ data: row }">
          <span :class="row.avg_latency_ms > 5000 ? 'text-error-color font-medium' : row.avg_latency_ms > 1000 ? 'text-warning-color' : ''">
            {{ row.avg_latency_ms.toFixed(0) }}
          </span>
        </template>
      </Column>
      <Column field="max_latency_ms" header="Max (ms)" style="width: 100px" :sortable="true">
        <template #body="{ data: row }">{{ row.max_latency_ms.toFixed(0) }}</template>
      </Column>
      <Column field="rows_examined_avg" header="Rows exam." style="width: 110px" :sortable="true" />
      <Column field="last_seen" header="Last seen" style="width: 160px">
        <template #body="{ data: row }">
          <span class="text-xs text-muted-color">{{ formatDate(row.last_seen) }}</span>
        </template>
      </Column>
      <template #empty><div class="empty-row">No slow queries found.</div></template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { DataTable, Column, Select, InputNumber } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions } from '@/composables/useNodeOptions'   // ← fix

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const minLatencyMs = ref(1000)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()   // ← fix

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-slow', clusterStore.selectedClusterId, selectedNodeId.value, minLatencyMs.value]),
  queryFn: () => diagnosticsApi.getSlowQueries(clusterStore.selectedClusterId!, selectedNodeId.value, minLatencyMs.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>