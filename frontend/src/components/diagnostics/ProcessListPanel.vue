<template>
  <div class="diag-panel anim-fade-in">
    <PanelToolbar
        title="process_list"
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
      <i class="pi pi-exclamation-triangle" />
      <span>{{ error.message }}</span>
    </div>

    <div class="table-wrap">
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
          row-hover
          class="diag-table"
      >
        <template #header>
          <div class="table-header">
            <div class="search-wrap">
              <i class="pi pi-search search-icon" />
              <InputText
                  v-model="search"
                  placeholder="Filter by user, db, query…"
                  size="small"
                  class="search-input"
              />
            </div>
            <label class="toggle-row">
              <ToggleSwitch v-model="hideSystem" />
              <span class="toggle-label">Hide system</span>
            </label>
            <span v-if="filtered.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ filtered.length }}
            </span>
          </div>
        </template>

        <Column field="id" header="ID" style="width: 70px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-id">{{ data.id }}</span>
          </template>
        </Column>

        <Column field="user" header="User" style="width: 140px" :sortable="true">
          <template #body="{ data }">
            <div class="cell-user-wrap">
              <span class="user-dot" />
              <span class="cell-user">{{ data.user }}</span>
            </div>
          </template>
        </Column>

        <Column field="host" header="Host" style="width: 160px">
          <template #body="{ data }">
            <span class="cell-mono cell-host">{{ data.host }}</span>
          </template>
        </Column>

        <Column field="db" header="DB" style="width: 120px">
          <template #body="{ data }">
            <span v-if="data.db" class="cell-db">
              <i class="pi pi-database" style="font-size: 9px; opacity: 0.7" />
              {{ data.db }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column field="command" header="Command" style="width: 110px">
          <template #body="{ data }">
            <span class="cell-command">{{ data.command }}</span>
          </template>
        </Column>

        <Column field="time" header="Time (s)" style="width: 100px" :sortable="true">
          <template #body="{ data }">
            <span
              class="cell-time"
              :class="{ 'cell-time--warn': data.time > SLOW_QUERY_SEC, 'cell-time--ok': data.time <= SLOW_QUERY_SEC }"
            >{{ data.time }}</span>
          </template>
        </Column>

        <Column field="state" header="State" style="width: 150px">
          <template #body="{ data }">
            <span v-if="data.state" class="state-badge" :class="stateBadgeClass(data.state)">
              <span class="state-dot" />
              {{ data.state }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column field="info" header="Query">
          <template #body="{ data }">
            <span v-if="data.info" class="cell-query" :title="data.info">
              {{ data.info.slice(0, 120) }}{{ data.info.length > 120 ? '…' : '' }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column header="" style="width: 48px">
          <template #body="{ data }">
            <Button
                v-if="data.command !== 'Daemon'"
                icon="pi pi-times"
                text
                rounded
                size="small"
                severity="danger"
                v-tooltip.left="selectedNodeId ? 'KILL ' + data.id : 'Select a node first'"
                :disabled="!selectedNodeId"
                :loading="killing === data.id"
                @click="handleKill(data)"
            />
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-inbox" />
            <span>No active processes</span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
import DataTable    from 'primevue/datatable'
import Column       from 'primevue/column'
import Button       from 'primevue/button'
import Select       from 'primevue/select'
import InputText    from 'primevue/inputtext'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import { useClusterStore }                  from '@/stores/cluster'
import { diagnosticsApi, type ProcessRow }  from '@/api/diagnostics'
import PanelToolbar                         from './PanelToolbar.vue'
import { useDiagAutoRefresh }               from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                   from '@/composables/useNodeOptions'

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
  queryKey: computed(() => ['diag-processes', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getProcessList(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  let rows: ProcessRow[] = data.value ?? []
  if (hideSystem.value) rows = rows.filter((r) => r.command !== 'Daemon' && r.user !== 'system user')
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    rows = rows.filter((r) =>
        r.user.toLowerCase().includes(q) ||
        (r.db ?? '').toLowerCase().includes(q) ||
        (r.info ?? '').toLowerCase().includes(q)
    )
  }
  return rows
})

function stateBadgeClass(state: string): string {
  const s = state.toLowerCase()
  if (s.includes('lock'))                        return 'badge--warn'
  if (s.includes('kill') || s.includes('quit'))  return 'badge--error'
  if (s === 'sleep')                             return 'badge--faint'
  if (s.includes('send') || s.includes('copy'))  return 'badge--primary'
  if (s.includes('query') || s.includes('exec')) return 'badge--query'
  return 'badge--default'
}

async function handleKill(row: ProcessRow) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return
  killing.value = row.id
  try {
    const res = await diagnosticsApi.killProcess(clusterStore.selectedClusterId, selectedNodeId.value, row.id)
    toast.add({
      severity: res.killed ? 'success' : 'warn',
      summary: res.killed ? `Killed process ${row.id}` : 'Kill failed',
      detail: res.message,
      life: 3000,
    })
    refetch()
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? err.message,
      life: 5000,
    })
  } finally {
    killing.value = null
  }
}
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────── */
.diag-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── Node selector ──────────────────────────────── */
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

/* search — flex-grow */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  min-width: 160px;
  max-width: 480px;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  pointer-events: none;
  z-index: 1;
}

.search-input {
  width: 100% !important;
}
:deep(.search-input.p-inputtext) {
  padding-left: calc(var(--space-3) + 16px);
}

/* ── Toggle row ─────────────────────────────────── */
/*
  Используем <label> вместо <div> — это разрешает PrimeVue ToggleSwitch
  пробрасывать клик на label напрямую через <input type=checkbox>
  Без height/overflow ограничений — PrimeVue рендерит position:relative
  на рут элементе, что мешало flex align-items.
*/
.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  cursor: pointer;
  /* НЕТ height, НЕТ overflow — пусть PrimeVue сам расправляется */
}

.toggle-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  letter-spacing: 0.03em;
  white-space: nowrap;
  user-select: none;
}

/*
  Прямой :deep без вложенного селектора — Vue scoped + :deep(X)
  работает как: [data-v-xxx] .p-toggleswitch
  Устанавливаем position: static — убираем inline position:relative
  чтобы flex мог нормально центрировать элемент.
*/
:deep(.p-toggleswitch) {
  position: static !important;
  display: inline-flex !important;
  align-items: center;
  flex-shrink: 0;
  vertical-align: middle;
}

:deep(.p-toggleswitch-slider) {
  display: flex;
  align-items: center;
  position: relative;
}

/* ── Row count badge ─────────────────────────────── */
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

/* ── DataTable column & cell overrides ──────────────── */
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

/* ── Cells ───────────────────────────────────────── */
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

.cell-user {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.cell-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.cell-db {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.cell-command {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.cell-dash {
  color: var(--color-text-faint);
  font-size: var(--text-xs);
}

/* ── Time cell ───────────────────────────────────── */
.cell-time {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.cell-time--ok   { color: var(--color-text-muted); }
.cell-time--warn {
  color: var(--color-warning);
  text-shadow: 0 0 8px color-mix(in oklch, var(--color-warning) 40%, transparent);
}

/* ── Query cell ───────────────────────────────────── */
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

/* ── State badge ─────────────────────────────────── */
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

.badge--faint { background: var(--color-surface-3); color: var(--color-text-faint); border-color: var(--color-border-muted); }
.badge--faint .state-dot { background: var(--color-text-faint); }

.badge--warn {
  background: color-mix(in oklch, var(--color-warning) 12%, transparent);
  color: var(--color-warning);
  border-color: color-mix(in oklch, var(--color-warning) 28%, transparent);
}
.badge--warn .state-dot { background: var(--color-warning); animation: pulse-dot 1.2s ease-in-out infinite; }

.badge--error {
  background: color-mix(in oklch, var(--color-error) 12%, transparent);
  color: var(--color-error);
  border-color: color-mix(in oklch, var(--color-error) 28%, transparent);
}
.badge--error .state-dot { background: var(--color-error); animation: pulse-dot 1.2s ease-in-out infinite; }

.badge--primary {
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-color: var(--color-primary-glow);
}
.badge--primary .state-dot { background: var(--color-primary); }

.badge--query {
  background: color-mix(in oklch, var(--color-info) 12%, transparent);
  color: var(--color-info);
  border-color: color-mix(in oklch, var(--color-info) 28%, transparent);
}
.badge--query .state-dot { background: var(--color-info); }

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
.empty-row .pi { font-size: 1.5rem; opacity: 0.4; }

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
</style>
