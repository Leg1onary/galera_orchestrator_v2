<template>
  <div class="diag-panel anim-fade-in">
    <PanelToolbar
        title="active_transactions"
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

      <div class="age-filter">
        <span class="age-label">Min age</span>
        <InputNumber
            v-model="minAgeSec"
            :min="0"
            :max="3600"
            show-buttons
            size="small"
            class="age-input"
            @update:model-value="onAgeChange"
        />
        <span class="age-unit">s</span>
      </div>
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-triangle" />
      <span>{{ error.message }}</span>
    </div>

    <div
        v-for="nodeErr in nodeErrors"
        :key="nodeErr.node_id"
        class="error-alert"
    >
      <i class="pi pi-exclamation-circle" />
      <span><strong>{{ nodeErr.node_name }}</strong>: {{ nodeErr.error }}</span>
    </div>

    <div class="table-wrap">
      <DataTable
          :value="allRows"
          :loading="isLoading"
          dataKey="_key"
          size="small"
          :rows="50"
          paginator
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink"
          sort-field="trx_age_sec"
          :sort-order="-1"
          row-hover
          class="diag-table"
      >
        <template #header>
          <div class="table-header">
            <div class="search-wrap">
              <i class="pi pi-search search-icon" />
              <InputText
                  v-model="search"
                  placeholder="Filter by user, query…"
                  size="small"
                  class="search-input"
              />
            </div>
            <span v-if="allRows.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ allRows.length }}
            </span>
          </div>
        </template>

        <Column field="node_name" header="Node" style="width: 120px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-node">{{ data.node_name }}</span>
          </template>
        </Column>

        <Column field="trx_id" header="TRX ID" style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-id">{{ data.trx_id }}</span>
          </template>
        </Column>

        <Column field="user" header="User" style="width: 130px" :sortable="true">
          <template #body="{ data }">
            <div class="cell-user-wrap">
              <span class="user-dot" />
              <span class="cell-user">{{ data.user ?? '—' }}</span>
            </div>
          </template>
        </Column>

        <Column field="trx_age_sec" header="Age (s)" style="width: 90px" :sortable="true">
          <template #body="{ data }">
            <span
                class="cell-age"
                :class="{
                  'cell-age--crit': data.trx_age_sec >= 300,
                  'cell-age--warn': data.trx_age_sec >= 30 && data.trx_age_sec < 300,
                  'cell-age--ok':   data.trx_age_sec < 30,
                }"
            >{{ data.trx_age_sec }}</span>
          </template>
        </Column>

        <Column field="trx_state" header="State" style="width: 120px" :sortable="true">
          <template #body="{ data }">
            <span class="state-badge" :class="stateBadgeClass(data.trx_state)">
              <span class="state-dot" />
              {{ data.trx_state }}
            </span>
          </template>
        </Column>

        <Column field="trx_mysql_thread_id" header="Thread" style="width: 80px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-id">{{ data.trx_mysql_thread_id }}</span>
          </template>
        </Column>

        <Column field="trx_tables_locked" header="Tbl lock" style="width: 80px" :sortable="true">
          <template #body="{ data }">
            <span :class="data.trx_tables_locked > 0 ? 'cell-lock--active' : 'cell-lock--zero'">
              {{ data.trx_tables_locked }}
            </span>
          </template>
        </Column>

        <Column field="trx_rows_locked" header="Row lock" style="width: 80px" :sortable="true">
          <template #body="{ data }">
            <span :class="data.trx_rows_locked > 0 ? 'cell-lock--active' : 'cell-lock--zero'">
              {{ data.trx_rows_locked }}
            </span>
          </template>
        </Column>

        <Column field="trx_rows_modified" header="Rows mod" style="width: 85px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-id">{{ data.trx_rows_modified }}</span>
          </template>
        </Column>

        <Column field="trx_query" header="Query">
          <template #body="{ data }">
            <span v-if="data.trx_query" class="cell-query" :title="data.trx_query">
              {{ data.trx_query.slice(0, 120) }}{{ data.trx_query.length > 120 ? '…' : '' }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-check-circle" />
            <span>No active long-running transactions</span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed }  from 'vue'
import { useQuery }       from '@tanstack/vue-query'
import DataTable   from 'primevue/datatable'
import Column      from 'primevue/column'
import Select      from 'primevue/select'
import InputText   from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import { useClusterStore }                                  from '@/stores/cluster'
import { diagnosticsApi, type ActiveTrxNodeResult }         from '@/api/diagnostics'
import PanelToolbar                                         from './PanelToolbar.vue'
import { useDiagAutoRefresh }                               from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                                   from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const minAgeSec      = ref(5)
const search         = ref('')
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

let ageTimer: ReturnType<typeof setTimeout> | null = null
function onAgeChange() {
  if (ageTimer) clearTimeout(ageTimer)
  ageTimer = setTimeout(() => { refetch() }, 600)
}

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-active-trx',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
    minAgeSec.value,
  ]),
  queryFn: () => diagnosticsApi.getActiveTransactions(
    clusterStore.selectedClusterId!,
    selectedNodeId.value,
    minAgeSec.value,
  ),
  enabled:   computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const nodeErrors = computed(() =>
    (data.value ?? []).filter((n: ActiveTrxNodeResult) => n.error)
)

const allRows = computed(() => {
  let rows = (data.value ?? []).flatMap((n: ActiveTrxNodeResult, _ni: number) =>
    n.transactions.map((t, idx) => ({
      ...t,
      node_id:   n.node_id,
      node_name: n.node_name,
      _key:      `${n.node_id}-${t.trx_id}-${idx}`,
    }))
  )
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    rows = rows.filter((r) =>
      (r.user ?? '').toLowerCase().includes(q) ||
      (r.trx_query ?? '').toLowerCase().includes(q)
    )
  }
  return rows
})

function stateBadgeClass(state: string): string {
  const s = (state ?? '').toUpperCase()
  if (s === 'RUNNING')      return 'badge--primary'
  if (s === 'LOCK WAIT')    return 'badge--warn'
  if (s === 'ROLLING BACK') return 'badge--error'
  return 'badge--default'
}
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

.age-filter {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.age-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.age-input { width: 90px; }

.age-unit {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

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

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

.table-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border-muted);
}

.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  min-width: 160px;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  pointer-events: none;
  z-index: 1;
}

.search-input { width: 100% !important; }
:deep(.search-input.p-inputtext) {
  padding-left: calc(var(--space-3) + 16px);
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

.cell-node {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
  font-weight: 600;
}

.cell-id {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}

.cell-user-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.user-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-primary);
  opacity: 0.7;
}

.cell-user { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.cell-dash { color: var(--color-text-faint); font-size: var(--text-xs); }

.cell-age {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.cell-age--ok   { color: var(--color-text-muted); }
.cell-age--warn { color: var(--color-warning); }
.cell-age--crit {
  color: var(--color-error);
  text-shadow: 0 0 8px color-mix(in oklch, var(--color-error) 40%, transparent);
}

.cell-lock--active {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: var(--color-warning);
}
.cell-lock--zero {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
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

.state-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 2px var(--space-3);
  border-radius: var(--radius-full);
  border: 1px solid transparent;
  white-space: nowrap;
}

.state-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}

.badge--default { background: var(--color-surface-3); color: var(--color-text-muted); border-color: var(--color-border); }
.badge--default .state-dot { background: var(--color-text-faint); }
.badge--warn    { background: color-mix(in oklch, var(--color-warning) 12%, transparent); color: var(--color-warning); border-color: color-mix(in oklch, var(--color-warning) 28%, transparent); }
.badge--warn    .state-dot { background: var(--color-warning); animation: pulse-dot 1.2s ease-in-out infinite; }
.badge--error   { background: color-mix(in oklch, var(--color-error) 12%, transparent); color: var(--color-error); border-color: color-mix(in oklch, var(--color-error) 28%, transparent); }
.badge--error   .state-dot { background: var(--color-error); animation: pulse-dot 1.2s ease-in-out infinite; }
.badge--primary { background: var(--color-primary-dim); color: var(--color-primary); border-color: var(--color-primary-glow); }
.badge--primary .state-dot { background: var(--color-primary); }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.7); }
}

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
.empty-row .pi { font-size: 1.5rem; opacity: 0.4; }

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
</style>
