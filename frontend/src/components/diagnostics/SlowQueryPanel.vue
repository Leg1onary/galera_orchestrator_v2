<template>
  <div class="diag-panel">
    <PanelToolbar
        title="slow_query_log"
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
      <span>{{ error.message }}</span>
    </div>

    <div class="table-wrap">
      <DataTable
          :value="data ?? []"
          :loading="isLoading"
          dataKey="start_time"
          size="small"
          :rows="50"
          paginator
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink"
          sort-field="query_time"
          :sort-order="-1"
          row-hover
          class="diag-table"
      >
        <Column field="start_time" header="Started" style="width: 170px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-muted-sm">{{ data.start_time }}</span>
          </template>
        </Column>

        <Column field="user_host" header="User / Host" style="width: 180px">
          <template #body="{ data }">
            <span class="cell-mono cell-muted-sm">{{ data.user_host }}</span>
          </template>
        </Column>

        <Column field="query_time" header="Query time" style="width: 110px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-time-warn">{{ data.query_time }}</span>
          </template>
        </Column>

        <Column field="lock_time" header="Lock time" style="width: 110px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ data.lock_time }}</span>
          </template>
        </Column>

        <Column field="rows_examined" header="Rows exam." style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ data.rows_examined }}</span>
          </template>
        </Column>

        <Column field="rows_sent" header="Rows sent" style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ data.rows_sent }}</span>
          </template>
        </Column>

        <Column field="db" header="DB" style="width: 100px">
          <template #body="{ data }">
            <span v-if="data.db" class="cell-db">{{ data.db }}</span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column field="sql_text" header="Query">
          <template #body="{ data }">
            <span class="cell-mono cell-query" :title="data.sql_text">
              {{ data.sql_text?.slice(0, 120) }}{{ data.sql_text?.length > 120 ? '…' : '' }}
            </span>
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-check-circle" />
            No slow queries found.
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
import DataTable  from 'primevue/datatable'
import Column     from 'primevue/column'
import Select     from 'primevue/select'
import { useClusterStore }   from '@/stores/cluster'
import { diagnosticsApi }    from '@/api/diagnostics'
import PanelToolbar          from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }     from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-slow', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getSlowQueries(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)
</script>

<style scoped>
.diag-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.node-select {
  width: 160px;
  min-width: 140px;
  flex-shrink: 0;
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.cell-mono       { font-family: var(--font-mono); }
.cell-muted-sm   { font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-dim        { font-size: var(--text-xs); color: var(--color-text-faint); font-variant-numeric: tabular-nums; }
.cell-time-warn  { font-size: var(--text-sm); font-weight: 700; color: var(--color-warning); font-variant-numeric: tabular-nums; }
.cell-db         { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-primary); }
.cell-dash       { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-query {
  display: block;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.empty-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-10);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
}
</style>
