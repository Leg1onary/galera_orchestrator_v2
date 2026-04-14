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

      <!-- Kill Bulk button: only when a single node is selected -->
      <Button
          v-if="selectedNodeId !== undefined && selectedNodeId !== null"
          icon="pi pi-bolt"
          label="Kill bulk"
          size="small"
          severity="danger"
          outlined
          v-tooltip.bottom="'Kill multiple processes by filter'"
          class="kill-bulk-btn"
          @click="openBulkDialog"
      />
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
          :value="filtered"
          :loading="isLoading"
          dataKey="_key"
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
            <div class="toggle-row" @click.stop="hideSystem = !hideSystem">
              <ToggleSwitch
                  :model-value="hideSystem"
                  @update:model-value="hideSystem = $event"
                  @click.stop
              />
              <span class="toggle-label">Hide system</span>
            </div>
            <span v-if="filtered.length" class="row-count">
              <i class="pi pi-list" style="font-size: 9px; opacity: 0.5" />
              {{ filtered.length }}
            </span>
          </div>
        </template>

        <Column field="node_name" header="Node" style="width: 130px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-node">{{ data.node_name }}</span>
          </template>
        </Column>

        <Column field="id" header="ID" style="width: 70px" :sortable="true">
          <template #body="{ data }">
            <span class="cell-id">{{ data.id }}</span>
          </template>
        </Column>

        <Column field="user" header="User" style="width: 130px" :sortable="true">
          <template #body="{ data }">
            <div class="cell-user-wrap">
              <span class="user-dot" />
              <span class="cell-user">{{ data.user }}</span>
            </div>
          </template>
        </Column>

        <Column field="host" header="Host" style="width: 150px">
          <template #body="{ data }">
            <span class="cell-mono cell-host">{{ data.host }}</span>
          </template>
        </Column>

        <Column field="db" header="DB" style="width: 110px">
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

        <!-- Actions column: Kill button -->
        <Column header="" style="width: 52px; text-align: center">
          <template #body="{ data }">
            <Button
                icon="pi pi-times-circle"
                size="small"
                severity="danger"
                text
                rounded
                :disabled="isSystemProcess(data) || killingId === data._key"
                :loading="killingId === data._key"
                v-tooltip.left="isSystemProcess(data) ? 'System process' : `Kill process #${data.id}`"
                class="kill-btn"
                @click="confirmKill(data)"
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

    <!-- Kill confirm dialog (single) -->
    <ConfirmDialog group="kill-process">
      <template #message="{ message }">
        <div class="confirm-body">
          <i class="pi pi-exclamation-triangle confirm-icon" />
          <div>
            <div class="confirm-title">{{ message.header }}</div>
            <div class="confirm-text">{{ message.message }}</div>
          </div>
        </div>
      </template>
    </ConfirmDialog>

    <!-- ── Kill Bulk dialog ──────────────────────────────────────────────── -->
    <Dialog
        v-model:visible="bulkDialogVisible"
        header="Kill bulk processes"
        :modal="true"
        :closable="true"
        :draggable="false"
        style="width: 420px"
        class="bulk-dialog"
    >
      <div class="bulk-body">
        <!-- Node label -->
        <div class="bulk-node-label">
          <i class="pi pi-server" />
          <span>{{ selectedNodeLabel }}</span>
        </div>

        <!-- Filter selector -->
        <div class="bulk-field">
          <label class="bulk-label">Filter</label>
          <SelectButton
              v-model="bulkFilter"
              :options="bulkFilterOptions"
              option-label="label"
              option-value="value"
              class="bulk-select-btn"
          />
        </div>

        <!-- sleep: min_time -->
        <div v-if="bulkFilter === 'sleep'" class="bulk-field">
          <label class="bulk-label">Kill Sleep connections idle for at least</label>
          <div class="bulk-input-row">
            <InputNumber
                v-model="bulkMinTime"
                :min="1"
                :max="86400"
                show-buttons
                size="small"
                class="bulk-number"
            />
            <span class="bulk-unit">seconds</span>
          </div>
          <span class="bulk-hint">System processes (Daemon, event_scheduler) are always skipped.</span>
        </div>

        <!-- user: username -->
        <div v-if="bulkFilter === 'user'" class="bulk-field">
          <label class="bulk-label">Kill all processes for DB user</label>
          <InputText
              v-model="bulkUser"
              placeholder="e.g. app_user"
              size="small"
              class="bulk-user-input"
          />
          <span class="bulk-hint">System processes are always skipped.</span>
        </div>
      </div>

      <template #footer>
        <div class="bulk-footer">
          <Button
              label="Cancel"
              severity="secondary"
              text
              :disabled="bulkLoading"
              @click="bulkDialogVisible = false"
          />
          <Button
              label="Kill"
              icon="pi pi-bolt"
              severity="danger"
              :loading="bulkLoading"
              :disabled="bulkFilter === 'user' && !bulkUser.trim()"
              @click="executeBulkKill"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed }  from 'vue'
import { useQuery }       from '@tanstack/vue-query'
import { useConfirm }     from 'primevue/useconfirm'
import { useToast }       from 'primevue/usetoast'
import DataTable     from 'primevue/datatable'
import Column        from 'primevue/column'
import Select        from 'primevue/select'
import SelectButton  from 'primevue/selectbutton'
import InputText     from 'primevue/inputtext'
import InputNumber   from 'primevue/inputnumber'
import ToggleSwitch  from 'primevue/toggleswitch'
import Button        from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import Dialog        from 'primevue/dialog'
import { useClusterStore }                              from '@/stores/cluster'
import { diagnosticsApi, type ProcessListNodeResult }  from '@/api/diagnostics'
import PanelToolbar                                    from './PanelToolbar.vue'
import { useDiagAutoRefresh }                          from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                              from '@/composables/useNodeOptions'

const SLOW_QUERY_SEC = 10

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const search         = ref('')
const hideSystem     = ref(true)
const killingId      = ref<string | null>(null)
const confirm        = useConfirm()
const toast          = useToast()
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

// ── Bulk kill state ────────────────────────────────────────────────────────
const bulkDialogVisible = ref(false)
const bulkFilter        = ref<'sleep' | 'user'>('sleep')
const bulkMinTime       = ref(5)
const bulkUser          = ref('')
const bulkLoading       = ref(false)

const bulkFilterOptions = [
  { label: 'Sleep', value: 'sleep' },
  { label: 'User',  value: 'user'  },
]

const selectedNodeLabel = computed(() => {
  if (selectedNodeId.value === undefined || selectedNodeId.value === null) return ''
  return nodeOptions.value.find((o) => o.value === selectedNodeId.value)?.label ?? String(selectedNodeId.value)
})

function openBulkDialog() {
  bulkFilter.value  = 'sleep'
  bulkMinTime.value = 5
  bulkUser.value    = ''
  bulkDialogVisible.value = true
}

async function executeBulkKill() {
  if (!clusterStore.selectedClusterId || selectedNodeId.value == null) return

  bulkLoading.value = true
  try {
    const body =
      bulkFilter.value === 'sleep'
        ? { filter: 'sleep' as const, min_time: bulkMinTime.value }
        : { filter: 'user'  as const, user: bulkUser.value.trim() }

    const result = await diagnosticsApi.killProcesses(
      clusterStore.selectedClusterId,
      selectedNodeId.value,
      body,
    )

    bulkDialogVisible.value = false

    const summary = `Killed ${result.killed.length}, skipped ${result.skipped}`
    const hasErrors = result.errors.length > 0

    toast.add({
      severity: hasErrors ? 'warn' : 'success',
      summary:  hasErrors ? 'Kill bulk: partial' : 'Kill bulk: done',
      detail:   hasErrors
        ? `${summary}. Errors: ${result.errors.join('; ')}`
        : summary,
      life: hasErrors ? 8000 : 4000,
    })

    await refetch()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(err)
    toast.add({
      severity: 'error',
      summary:  'Kill bulk failed',
      detail:   msg,
      life:     6000,
    })
  } finally {
    bulkLoading.value = false
  }
}
// ──────────────────────────────────────────────────────────────────────────

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-processes', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn:  () => diagnosticsApi.getProcessList(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled:  computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const nodeErrors = computed(() =>
    (data.value ?? []).filter((n: ProcessListNodeResult) => n.error)
)

const allRows = computed(() =>
    (data.value ?? []).flatMap((n: ProcessListNodeResult) =>
        n.processes.map((p, idx) => ({
            ...p,
            node_id:   n.node_id,
            node_name: n.node_name,
            _key:      `${n.node_id}-${p.id}-${idx}`,
        }))
    )
)

const filtered = computed(() => {
  let rows = allRows.value
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

function isSystemProcess(row: { command: string; user: string }): boolean {
  return row.command === 'Daemon' || row.user === 'system user'
}

function stateBadgeClass(state: string): string {
  const s = state.toLowerCase()
  if (s.includes('lock'))                        return 'badge--warn'
  if (s.includes('kill') || s.includes('quit'))  return 'badge--error'
  if (s === 'sleep')                             return 'badge--faint'
  if (s.includes('send') || s.includes('copy'))  return 'badge--primary'
  if (s.includes('query') || s.includes('exec')) return 'badge--query'
  return 'badge--default'
}

function confirmKill(row: { _key: string; id: number; node_id: number; node_name: string; user: string; host: string }) {
  confirm.require({
    group:   'kill-process',
    header:  `Kill process #${row.id}?`,
    message: `${row.user}@${row.host} on ${row.node_name}`,
    icon:    'pi pi-exclamation-triangle',
    acceptLabel:  'Kill',
    rejectLabel:  'Cancel',
    acceptClass:  'p-button-danger',
    accept: () => doKill(row),
  })
}

async function doKill(row: { _key: string; id: number; node_id: number; node_name: string }) {
  killingId.value = row._key
  try {
    await diagnosticsApi.killProcess(
      clusterStore.selectedClusterId!,
      row.node_id,
      row.id,
    )
    toast.add({
      severity: 'success',
      summary:  'Process killed',
      detail:   `#${row.id} on ${row.node_name}`,
      life:     3000,
    })
    await refetch()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(err)
    toast.add({
      severity: 'error',
      summary:  'Kill failed',
      detail:   msg,
      life:     5000,
    })
  } finally {
    killingId.value = null
  }
}
</script>

<style scoped>
.diag-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: 15px;
}

.node-select {
  width: 160px;
  min-width: 140px;
  flex-shrink: 0;
}

.kill-bulk-btn {
  flex-shrink: 0;
  white-space: nowrap;
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

.search-input { width: 100% !important; }
:deep(.search-input.p-inputtext) {
  padding-left: calc(var(--space-3) + 16px);
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  cursor: pointer;
  user-select: none;
}

.toggle-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

:deep(.p-toggleswitch) {
  position: static !important;
  display: inline-flex !important;
  align-items: center;
  flex-shrink: 0;
  vertical-align: middle;
  pointer-events: none;
}

:deep(.p-toggleswitch-slider) {
  display: flex;
  align-items: center;
  position: relative;
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
.cell-host { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-text-muted); }

.cell-db {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.cell-command { font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-dash    { color: var(--color-text-faint); font-size: var(--text-xs); }

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
.badge--faint   { background: var(--color-surface-3); color: var(--color-text-faint); border-color: var(--color-border-muted); }
.badge--faint   .state-dot { background: var(--color-text-faint); }
.badge--warn    { background: color-mix(in oklch, var(--color-warning) 12%, transparent); color: var(--color-warning); border-color: color-mix(in oklch, var(--color-warning) 28%, transparent); }
.badge--warn    .state-dot { background: var(--color-warning); animation: pulse-dot 1.2s ease-in-out infinite; }
.badge--error   { background: color-mix(in oklch, var(--color-error) 12%, transparent); color: var(--color-error); border-color: color-mix(in oklch, var(--color-error) 28%, transparent); }
.badge--error   .state-dot { background: var(--color-error); animation: pulse-dot 1.2s ease-in-out infinite; }
.badge--primary { background: var(--color-primary-dim); color: var(--color-primary); border-color: var(--color-primary-glow); }
.badge--primary .state-dot { background: var(--color-primary); }
.badge--query   { background: color-mix(in oklch, var(--color-info) 12%, transparent); color: var(--color-info); border-color: color-mix(in oklch, var(--color-info) 28%, transparent); }
.badge--query   .state-dot { background: var(--color-info); }

.kill-btn {
  opacity: 0;
  transition: opacity var(--transition-fast);
}
:deep(tr:hover) .kill-btn { opacity: 1; }
:deep(tr) .kill-btn.p-button-loading { opacity: 1; }

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

.confirm-body {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-2) 0;
}
.confirm-icon {
  font-size: 1.4rem;
  color: var(--color-warning);
  flex-shrink: 0;
  margin-top: 2px;
}
.confirm-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}
.confirm-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

/* ── Bulk dialog styles ─────────────────────────────────────────────────── */
.bulk-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-2) 0 var(--space-4);
}

.bulk-node-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  background: var(--color-primary-dim, color-mix(in oklch, var(--color-primary) 10%, transparent));
  border: 1px solid var(--color-primary-glow, color-mix(in oklch, var(--color-primary) 25%, transparent));
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
}

.bulk-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.bulk-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.bulk-select-btn {
  width: 100%;
}

:deep(.bulk-select-btn .p-selectbutton) {
  width: 100%;
  display: flex;
}

:deep(.bulk-select-btn .p-togglebutton) {
  flex: 1;
  justify-content: center;
}

.bulk-input-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.bulk-number {
  width: 120px;
}

.bulk-unit {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.bulk-user-input {
  width: 100%;
}

.bulk-hint {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  line-height: 1.4;
}

.bulk-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
