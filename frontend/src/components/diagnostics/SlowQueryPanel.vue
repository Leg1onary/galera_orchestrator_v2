<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Slow queries"
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
      <!-- MAJOR fix: utility классы → scoped -->
      <div class="latency-control">
        <span class="latency-label">Min latency (ms)</span>
        <InputNumber
            v-model="minLatencyMs"
            :min="0"
            :step="500"
            size="small"
            class="latency-input"
            @keydown.enter="refetch()"
        />
      </div>
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <DataTable
        :value="data ?? []"
        :loading="isLoading"
        dataKey="query_digest"
        size="small"
        sort-field="avg_latency_ms"
        :sort-order="-1"
    >
      <Column field="query_digest"    header="Query digest">
        <template #body="{ data: row }">
          <!-- MAJOR fix: font-mono text-xs → scoped -->
          <span class="mono-xs">
            {{ row.query_digest.slice(0, 140) }}{{ row.query_digest.length > 140 ? '…' : '' }}
          </span>
        </template>
      </Column>
      <Column field="schema_name"     header="Schema"     style="width: 120px">
        <template #body="{ data: row }">{{ row.schema_name ?? '—' }}</template>
      </Column>
      <Column field="exec_count"      header="Exec"       style="width: 80px"  :sortable="true" />
      <Column field="avg_latency_ms"  header="Avg (ms)"   style="width: 100px" :sortable="true">
        <template #body="{ data: row }">
          <!-- MAJOR fix: utility → scoped классы -->
          <span :class="latencyClass(row.avg_latency_ms)">
            {{ row.avg_latency_ms.toFixed(0) }}
          </span>
        </template>
      </Column>
      <Column field="max_latency_ms"  header="Max (ms)"   style="width: 100px" :sortable="true">
        <template #body="{ data: row }">{{ row.max_latency_ms.toFixed(0) }}</template>
      </Column>
      <Column field="rows_examined_avg" header="Rows exam." style="width: 110px" :sortable="true" />
      <Column field="last_seen"       header="Last seen"  style="width: 160px">
        <template #body="{ data: row }">
          <!-- MAJOR fix: text-xs text-muted-color → scoped -->
          <span class="date-cell">{{ formatDate(row.last_seen) }}</span>
        </template>
      </Column>

      <template #empty>
        <div class="empty-row">No slow queries found.</div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, keepPreviousData } from '@tanstack/vue-query'
// BLOCKER fix: раздельные импорты
import DataTable  from 'primevue/datatable'
import Column     from 'primevue/column'
import Select     from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import { useClusterStore }      from '@/stores/cluster'
import { diagnosticsApi }       from '@/api/diagnostics'
import PanelToolbar             from './PanelToolbar.vue'
import { useDiagAutoRefresh }   from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }       from '@/composables/useNodeOptions'
// MINOR fix: форматирование дат через общий utils
import { formatDateTime }       from '@/utils/time'

const SLOW_MS_ERROR   = 5000
const SLOW_MS_WARNING = 1000

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const minLatencyMs   = ref(1000)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-slow',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
    minLatencyMs.value,
  ]),
  queryFn: () =>
      diagnosticsApi.getSlowQueries(
          clusterStore.selectedClusterId!,
          selectedNodeId.value,
          minLatencyMs.value,
      ),
  enabled:         computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime:       0,
  // MINOR fix: не мигаем при смене minLatencyMs
  placeholderData: keepPreviousData,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

function latencyClass(ms: number): string {
  if (ms > SLOW_MS_ERROR)   return 'val--error'
  if (ms > SLOW_MS_WARNING) return 'val--warning'
  return ''
}

// MINOR fix: единый форматтер из utils/time.ts
function formatDate(iso: string): string {
  return formatDateTime(iso)
}
</script>

<style scoped>
.node-select   { width: 180px; }
.latency-input { width: 100px; }

/* MAJOR fix: utility → scoped */
.latency-control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.latency-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.mono-xs  { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.date-cell {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.val--error   { color: var(--color-error);   font-weight: 500; }
.val--warning { color: var(--color-warning); }

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