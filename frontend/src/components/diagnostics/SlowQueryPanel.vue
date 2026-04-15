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

    <!-- Network / query-level error -->
    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ error.message }}</span>
    </div>

    <!-- Per-node SSH/DB errors -->
    <div
        v-for="n in errorNodes"
        :key="'err-' + n.node_id"
        class="error-alert"
    >
      <i class="pi pi-exclamation-circle" />
      <span><strong>{{ n.node_name }}</strong>: {{ n.error }}</span>
    </div>

    <!-- slow_query_log=OFF banner (per node) -->
    <div
        v-for="n in disabledNodes"
        :key="'off-' + n.node_id"
        class="info-banner"
    >
      <i class="pi pi-info-circle" />
      <span>
        <strong>{{ n.node_name }}</strong>: <code>slow_query_log</code> is <strong>OFF</strong>
        <span class="banner-hint">&mdash; runtime only, resets on node/MariaDB restart</span>
      </span>
      <Button
          label="Enable"
          icon="pi pi-play"
          size="small"
          severity="warn"
          :loading="togglingNodeId === n.node_id"
          :disabled="togglingNodeId !== null"
          class="toggle-btn"
          @click="toggleSlowLog(n.node_id, true)"
      />
    </div>

    <!-- slow_query_log=ON banner (per node) -->
    <div
        v-for="n in enabledNodes"
        :key="'on-' + n.node_id"
        class="success-banner"
    >
      <i class="pi pi-check-circle" />
      <span>
        <strong>{{ n.node_name }}</strong>: <code>slow_query_log</code> is <strong>ON</strong>
        <span class="banner-hint">&mdash; runtime only, resets on node/MariaDB restart</span>
      </span>
      <Button
          label="Disable"
          icon="pi pi-stop-circle"
          size="small"
          severity="secondary"
          :loading="togglingNodeId === n.node_id"
          :disabled="togglingNodeId !== null"
          class="toggle-btn"
          @click="toggleSlowLog(n.node_id, false)"
      />
    </div>

    <!-- ── Filters ── -->
    <div class="filters-bar">
      <div class="filter-group">
        <label class="filter-label">Query time &ge;</label>
        <div class="filter-input-wrap">
          <InputNumber
              v-model="filterMinSec"
              :min="0"
              :max="3600"
              :step="0.5"
              :min-fraction-digits="0"
              :max-fraction-digits="1"
              size="small"
              class="filter-number"
              suffix=" s"
          />
        </div>
      </div>

      <div class="filter-group">
        <label class="filter-label">Database</label>
        <MultiSelect
            v-model="filterDbs"
            :options="dbOptions"
            placeholder="All"
            size="small"
            class="filter-multiselect"
            :max-selected-labels="2"
            show-clear
        />
      </div>

      <div class="filter-group">
        <label class="filter-label">User / Host</label>
        <InputText
            v-model="filterUser"
            placeholder="contains…"
            size="small"
            class="filter-text"
        />
      </div>

      <div class="filter-group">
        <label class="filter-label">Query text</label>
        <InputText
            v-model="filterQuery"
            placeholder="contains…"
            size="small"
            class="filter-text"
        />
      </div>

      <Button
          v-if="isFiltered"
          label="Reset"
          icon="pi pi-times"
          size="small"
          severity="secondary"
          text
          class="reset-btn"
          @click="resetFilters"
      />
    </div>

    <div class="table-wrap">
      <DataTable
          :value="filteredRows"
          :loading="isLoading"
          dataKey="_key"
          size="small"
          :rows="50"
          paginator
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink"
          sort-field="_query_time_sec"
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
            <span v-if="filteredRows.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ filteredRows.length }}
              <template v-if="filteredRows.length !== allRows.length">
                <span class="row-count-total">/ {{ allRows.length }}</span>
              </template>
            </span>
          </div>
        </template>

        <Column field="node_name" header="Node" style="width: 120px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-node">{{ data.node_name }}</span>
          </template>
        </Column>

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

        <Column field="_query_time_sec" header="Query time" style="width: 110px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-time-warn">{{ data.query_time }}</span>
          </template>
        </Column>

        <Column field="_lock_time_sec" header="Lock time" style="width: 110px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ data.lock_time }}</span>
          </template>
        </Column>

        <Column field="rows_examined" header="Rows exam." style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ fmtNum(data.rows_examined) }}</span>
          </template>
        </Column>

        <Column field="rows_sent" header="Rows sent" style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-mono cell-dim">{{ fmtNum(data.rows_sent) }}</span>
          </template>
        </Column>

        <Column field="db" header="DB" style="width: 100px">
          <template #body="{ data }">
            <span v-if="data.db" class="cell-db">
              <i class="pi pi-database" style="font-size: 9px; opacity: 0.7" />
              {{ data.db }}
            </span>
            <span v-else class="cell-dash">&mdash;</span>
          </template>
        </Column>

        <Column field="sql_text" header="Query">
          <template #body="{ data }">
            <span class="cell-query" :title="data.sql_text">
              {{ data.sql_text?.slice(0, 120) }}{{ data.sql_text?.length > 120 ? '\u2026' : '' }}
            </span>
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-check-circle" />
            <span>{{ allRows.length ? 'No rows match current filters' : 'No slow queries found' }}</span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed }  from 'vue'
import { useQuery }       from '@tanstack/vue-query'
import { useToast }       from 'primevue/usetoast'
import DataTable   from 'primevue/datatable'
import Column      from 'primevue/column'
import Select      from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import Button      from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText   from 'primevue/inputtext'
import { useClusterStore }                            from '@/stores/cluster'
import { diagnosticsApi, type SlowQueryNodeResult }  from '@/api/diagnostics'
import PanelToolbar                                  from './PanelToolbar.vue'
import { useDiagAutoRefresh }                        from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                            from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const toast          = useToast()
const togglingNodeId = ref<number | null>(null)

// ── Filters ──────────────────────────────────────────────────────────────────
const filterMinSec = ref<number>(1)
const filterDbs    = ref<string[]>([])
const filterUser   = ref('')
const filterQuery  = ref('')

const DEFAULT_MIN_SEC = 1

const isFiltered = computed(() =>
    filterMinSec.value !== DEFAULT_MIN_SEC ||
    filterDbs.value.length > 0 ||
    filterUser.value.trim() !== '' ||
    filterQuery.value.trim() !== ''
)

function resetFilters() {
  filterMinSec.value = DEFAULT_MIN_SEC
  filterDbs.value    = []
  filterUser.value   = ''
  filterQuery.value  = ''
}

// ── Data ─────────────────────────────────────────────────────────────────────
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-slow', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn:  () => diagnosticsApi.getSlowQueries(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled:  computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

function hmsToSec(hms: string | null | undefined): number {
  if (!hms) return 0
  const parts = hms.split(':').map(Number)
  if (parts.length !== 3 || parts.some(isNaN)) return 0
  return parts[0] * 3600 + parts[1] * 60 + parts[2]
}

function fmtNum(val: number | null | undefined): string {
  if (val == null) return '\u2014'
  return Number(val).toLocaleString()
}

const disabledNodes = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => n.slow_log_enabled === false)
)

const enabledNodes = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => n.slow_log_enabled === true)
)

const errorNodes = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => !!n.error)
)

const allRows = computed(() =>
    (data.value ?? [])
        .filter((n: SlowQueryNodeResult) => n.slow_log_enabled !== false && !n.error)
        .flatMap((n: SlowQueryNodeResult, ni: number) =>
            n.rows.map((r, ri) => ({
                ...r,
                node_name:       n.node_name,
                node_id:         n.node_id,
                _key:            `${n.node_id}-${ni}-${ri}`,
                _query_time_sec: hmsToSec(r.query_time),
                _lock_time_sec:  hmsToSec(r.lock_time),
            }))
        )
)

// Unique DB list for multiselect — derived from loaded data
const dbOptions = computed(() => {
  const set = new Set<string>()
  for (const row of allRows.value) {
    if (row.db) set.add(row.db)
  }
  return [...set].sort()
})

const filteredRows = computed(() => {
  const minSec    = filterMinSec.value ?? 0
  const dbs       = filterDbs.value
  const userTerm  = filterUser.value.trim().toLowerCase()
  const queryTerm = filterQuery.value.trim().toLowerCase()

  return allRows.value.filter((row) => {
    if (row._query_time_sec < minSec) return false
    if (dbs.length && !dbs.includes(row.db ?? '')) return false
    if (userTerm  && !row.user_host?.toLowerCase().includes(userTerm))  return false
    if (queryTerm && !row.sql_text?.toLowerCase().includes(queryTerm))  return false
    return true
  })
})

// ── Toggle slow_query_log ─────────────────────────────────────────────────────
async function toggleSlowLog(nodeId: number, enable: boolean) {
  togglingNodeId.value = nodeId
  try {
    await diagnosticsApi.setSlowQueryLog(clusterStore.selectedClusterId!, nodeId, enable)
    toast.add({
      severity: 'success',
      summary: `slow_query_log ${enable ? 'enabled' : 'disabled'}`,
      detail: 'Changes are runtime only and will reset on node/MariaDB restart.',
      life: 5000,
    })
    await refetch()
  } catch (err: any) {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail ?? err?.message ?? 'Unknown error'
    toast.add({
      severity: 'error',
      summary: status === 403 ? 'Insufficient privileges' : 'Failed to change slow_query_log',
      detail,
      life: 8000,
    })
  } finally {
    togglingNodeId.value = null
  }
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

/* ── Banners ── */
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

.info-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-warning) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
  color: var(--color-warning);
  font-size: var(--text-sm);
}
.info-banner .pi  { font-size: var(--text-base); flex-shrink: 0; }
.info-banner code { font-family: var(--font-mono); font-size: 0.85em; opacity: 0.9; }

.success-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-success) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-success) 25%, transparent);
  color: var(--color-success);
  font-size: var(--text-sm);
}
.success-banner .pi  { font-size: var(--text-base); flex-shrink: 0; }
.success-banner code { font-family: var(--font-mono); font-size: 0.85em; opacity: 0.9; }

.banner-hint {
  font-size: var(--text-xs);
  opacity: 0.7;
  margin-left: var(--space-1);
}

.toggle-btn { margin-left: auto; flex-shrink: 0; }

/* ── Filters bar ── */
.filters-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.filter-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.filter-number     { width: 110px; }
.filter-multiselect { width: 180px; }
.filter-text       { width: 180px; }

.reset-btn { margin-left: auto; align-self: flex-end; }

/* ── Table ── */
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
.table-title .pi { font-size: var(--text-sm); color: var(--color-warning); opacity: 0.8; }

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
  padding: 3px var(--space-3);
}
.row-count-total {
  color: var(--color-text-faint);
  opacity: 0.6;
}

:deep(.diag-table .p-datatable-table) { width: 100%; table-layout: fixed; }

:deep(.diag-table .p-datatable-thead > tr > th) {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-faint);
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

:deep(.diag-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6);
  vertical-align: middle;
  border: none;
  border-bottom: 1px solid var(--color-border-muted);
}

:deep(.diag-table .p-datatable-tbody > tr:last-child > td) { border-bottom: none; }

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

.cell-node     { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-primary); font-weight: 600; }
.cell-mono     { font-family: var(--font-mono); }
.cell-muted-sm { font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-dim      { font-size: var(--text-xs); color: var(--color-text-faint); font-variant-numeric: tabular-nums; }
.cell-dash     { color: var(--color-text-faint); font-size: var(--text-xs); }

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
