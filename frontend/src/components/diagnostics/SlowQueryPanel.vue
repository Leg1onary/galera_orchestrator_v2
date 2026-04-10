<template>
  <div class="diag-panel anim-fade-in">
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
        <template #header>
          <div class="table-header">
            <span class="table-title">
              <i class="pi pi-clock" />
              Slow queries
            </span>
            <span v-if="data?.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ data.length }}
            </span>
          </div>
        </template>

        <Column field="start_time" header="Started" style="width: 160px" :sortable="true">
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
            <span class="cell-time-warn">{{ data.query_time }}</span>
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
            <span v-if="data.db" class="cell-db">
              <i class="pi pi-database" style="font-size: 9px; opacity: 0.7" />
              {{ data.db }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column field="sql_text" header="Query">
          <template #body="{ data }">
            <span class="cell-query" :title="data.sql_text">
              {{ data.sql_text?.slice(0, 120) }}{{ data.sql_text?.length > 120 ? '…' : '' }}
            </span>
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-check-circle" />
            <span>No slow queries found</span>
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
/* ── Layout ──────────────────────────────────────── */
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

/* ── Error alert ───────────────────────────────── */
.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.error-alert .pi { font-size: var(--text-base); flex-shrink: 0; }

/* ── Table wrapper ──────────────────────────────── */
.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

/* ── Table header toolbar ─────────────────────────── */
.table-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border-muted);
}

.table-title {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  flex: 1 1 auto;
}
.table-title .pi {
  font-size: var(--text-sm);
  color: var(--color-warning);
  opacity: 0.8;
}

.row-count {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 2px var(--space-3);
}

/* ── DataTable overrides ───────────────────────────── */
:deep(.diag-table .p-datatable-table) {
  width: 100%;
  table-layout: fixed;
}

:deep(.diag-table .p-datatable-thead > tr > th) {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

:deep(.diag-table .p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-5);
  vertical-align: middle;
  border: none;
  border-bottom: 1px solid var(--color-border-muted);
}

:deep(.diag-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none;
}

/* ── Paginator ───────────────────────────────────── */
:deep(.p-paginator) {
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border-muted);
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-xs);
}
:deep(.p-paginator-page.p-highlight) {
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-color: var(--color-primary-glow);
}

/* ── Cells ───────────────────────────────────────── */
.cell-mono     { font-family: var(--font-mono); }
.cell-muted-sm { font-size: var(--text-xs); color: var(--color-text-muted); }

.cell-dim {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}

.cell-time-warn {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-warning);
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 8px color-mix(in oklch, var(--color-warning) 40%, transparent);
}

.cell-db {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.cell-dash {
  color: var(--color-text-faint);
  font-size: var(--text-xs);
}

.cell-query {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  transition: color var(--transition-fast);
}
:deep(tr:hover) .cell-query { color: var(--color-text); }

/* ── Empty state ────────────────────────────────── */
.empty-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-12) var(--space-8);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
}
.empty-row .pi { font-size: 1.5rem; opacity: 0.4; color: var(--color-success); }
</style>
