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
      <!-- Node selector -->
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

      <!-- min_query_time filter (variant B: compact inline in toolbar) -->
      <div class="mqt-filter">
        <label class="mqt-label" for="mqt-input">
          <i class="pi pi-stopwatch" />
          Min time, s
        </label>
        <InputNumber
            id="mqt-input"
            v-model="minQueryTime"
            :min="0"
            :max="86400"
            :step="0.5"
            :min-fraction-digits="0"
            :max-fraction-digits="1"
            size="small"
            class="mqt-input"
            :allow-empty="false"
            @keydown.enter="refetch()"
        />
      </div>
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

    <!-- slow_query_log=OFF banner (per node) with Enable button -->
    <div
        v-for="n in disabledNodes"
        :key="'off-' + n.node_id"
        class="info-banner"
    >
      <i class="pi pi-info-circle" style="flex-shrink: 0" />
      <div class="banner-body">
        <span>
          <strong>{{ n.node_name }}</strong>: <code>slow_query_log</code> is <strong>OFF</strong> on this node.
        </span>
        <span class="banner-warn">
          <i class="pi pi-exclamation-triangle" />
          Runtime only — will reset after MariaDB restart. May increase disk I/O.
        </span>
      </div>
      <Button
          size="small"
          severity="warning"
          :loading="togglingNodeIds.has(n.node_id)"
          :disabled="togglingNodeIds.has(n.node_id)"
          label="Enable"
          icon="pi pi-power-off"
          class="banner-btn"
          @click="handleToggle(n.node_id, true)"
      />
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
            <span v-if="allRows.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ allRows.length }}
            </span>
            <!-- Disable buttons for nodes where slow log is ON -->
            <div v-if="enabledNodesInView.length" class="toggle-controls">
              <Button
                  v-for="n in enabledNodesInView"
                  :key="'dis-' + n.node_id"
                  size="small"
                  severity="secondary"
                  :loading="togglingNodeIds.has(n.node_id)"
                  :label="`Disable on ${n.node_name}`"
                  icon="pi pi-stop"
                  @click="handleToggle(n.node_id, false)"
              />
            </div>
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

        <!-- Sort by numeric seconds field, display original HH:MM:SS string -->
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
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import DataTable  from 'primevue/datatable'
import Column     from 'primevue/column'
import Select     from 'primevue/select'
import Button     from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useClusterStore }                            from '@/stores/cluster'
import { diagnosticsApi, type SlowQueryNodeResult }  from '@/api/diagnostics'
import PanelToolbar                                  from './PanelToolbar.vue'
import { useDiagAutoRefresh }                        from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                            from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const toast       = useToast()
const queryClient = useQueryClient()

// Track nodes currently being toggled to show spinner and prevent double-click
const togglingNodeIds = ref<Set<number>>(new Set())

// min_query_time filter — 0 means no filter (backend default)
const minQueryTime = ref<number>(0)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-slow',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
    minQueryTime.value,
  ]),
  queryFn: () => diagnosticsApi.getSlowQueries(clusterStore.selectedClusterId!, {
    nodeId:       selectedNodeId.value,
    minQueryTime: minQueryTime.value > 0 ? minQueryTime.value : undefined,
  }),
  enabled:  computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

/**
 * Toggle slow_query_log ON/OFF for a given node.
 * Shows a warning toast on success (runtime only, resets after restart).
 */
async function handleToggle(nodeId: number, enable: boolean): Promise<void> {
  togglingNodeIds.value = new Set([...togglingNodeIds.value, nodeId])
  try {
    const res = await diagnosticsApi.toggleSlowQueryLog(
        clusterStore.selectedClusterId!,
        nodeId,
        enable,
    )
    if (res.error) {
      toast.add({
        severity: 'error',
        summary:  'Toggle failed',
        detail:   res.error,
        life:     5000,
      })
    } else {
      toast.add({
        severity: 'warn',
        summary:  `slow_query_log ${enable ? 'enabled' : 'disabled'}`,
        detail:   `${res.node_name} — runtime change only, resets after restart`,
        life:     6000,
      })
      await queryClient.invalidateQueries({
        queryKey: ['diag-slow', clusterStore.selectedClusterId],
      })
    }
  } catch (e: any) {
    toast.add({
      severity: 'error',
      summary:  'Request failed',
      detail:   e?.message ?? String(e),
      life:     5000,
    })
  } finally {
    const s = new Set(togglingNodeIds.value)
    s.delete(nodeId)
    togglingNodeIds.value = s
  }
}

/**
 * Convert "HH:MM:SS" to total seconds for correct numeric sorting.
 * Falls back to 0 if the format is unexpected.
 */
function hmsToSec(hms: string | null | undefined): number {
  if (!hms) return 0
  const parts = hms.split(':').map(Number)
  if (parts.length !== 3 || parts.some(isNaN)) return 0
  return parts[0] * 3600 + parts[1] * 60 + parts[2]
}

/** Format large numbers with locale-aware thousand separators. */
function fmtNum(val: number | null | undefined): string {
  if (val == null) return '—'
  return Number(val).toLocaleString()
}

// Nodes where slow_query_log is explicitly OFF
const disabledNodes = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => n.slow_log_enabled === false && !n.error)
)

// Nodes that returned an SSH/DB error (slow_log_enabled === null and error present)
const errorNodes = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => !!n.error)
)

// Nodes currently visible in the view where slow log is ON (to show Disable buttons)
const enabledNodesInView = computed(() =>
    (data.value ?? []).filter((n: SlowQueryNodeResult) => n.slow_log_enabled === true && !n.error)
)

// Flatten rows from all nodes that are enabled and error-free, annotate with
// node_name and pre-computed numeric sort fields.
const allRows = computed(() =>
    (data.value ?? [])
        .filter((n: SlowQueryNodeResult) => n.slow_log_enabled !== false && !n.error)
        .flatMap((n: SlowQueryNodeResult, ni: number) =>
            n.rows.map((r, ri) => ({
                ...r,
                node_name:       n.node_name,
                node_id:         n.node_id,
                _key:            `${n.node_id}-${ni}-${ri}`,
                // Numeric seconds for correct sort (HH:MM:SS strings sort wrong for values >= 10h)
                _query_time_sec: hmsToSec(r.query_time),
                _lock_time_sec:  hmsToSec(r.lock_time),
            }))
        )
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

/* ── min_query_time filter ────────────────────────────────────────────────── */
.mqt-filter {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.mqt-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  user-select: none;
  cursor: default;
}
.mqt-label .pi { font-size: var(--text-xs); opacity: 0.7; }

.mqt-input {
  width: 80px;
}
:deep(.mqt-input .p-inputtext) {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-align: right;
  font-variant-numeric: tabular-nums;
  padding: var(--space-1) var(--space-2);
}

/* ── alerts ───────────────────────────────────────────────────────────────── */
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
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-warning) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
  color: var(--color-warning);
  font-size: var(--text-sm);
}
.info-banner > .pi { font-size: var(--text-base); }
.info-banner code  { font-family: var(--font-mono); font-size: 0.85em; opacity: 0.9; }

.banner-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1 1 auto;
}

.banner-warn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  opacity: 0.75;
}
.banner-warn .pi { font-size: var(--text-xs); }

.banner-btn {
  flex-shrink: 0;
  margin-left: auto;
}

/* ── table ────────────────────────────────────────────────────────────────── */
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
  flex-wrap: wrap;
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
  padding: 2px var(--space-3);
}

.toggle-controls {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

:deep(.diag-table .p-datatable-table) { width: 100%; table-layout: fixed; }

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

.cell-node    { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-primary); font-weight: 600; }
.cell-mono    { font-family: var(--font-mono); }
.cell-muted-sm { font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-dim     { font-size: var(--text-xs); color: var(--color-text-faint); font-variant-numeric: tabular-nums; }
.cell-dash    { color: var(--color-text-faint); font-size: var(--text-xs); }

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
