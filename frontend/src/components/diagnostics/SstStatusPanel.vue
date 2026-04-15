<template>
  <div class="diag-panel anim-fade-in">
    <PanelToolbar
        title="sst_status"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-triangle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <!-- Empty state: no nodes in SST -->
    <div v-else-if="!isLoading && !rows.length" class="empty-state">
      <div class="empty-icon"><i class="pi pi-check-circle" /></div>
      <span class="empty-label">No nodes currently in SST</span>
    </div>

    <!-- SST nodes table -->
    <div v-else class="table-wrap">
      <DataTable
          :value="rows"
          :loading="isLoading"
          dataKey="node_id"
          size="small"
          row-hover
          class="diag-table"
      >
        <Column field="node_id" header="Node ID" style="width: 90px">
          <template #body="{ data }">
            <span class="cell-mono cell-faint">{{ data.node_id }}</span>
          </template>
        </Column>

        <Column field="node_name" header="Node" style="width: 160px">
          <template #body="{ data }">
            <span class="cell-node">{{ data.node_name }}</span>
          </template>
        </Column>

        <Column field="state" header="State" style="width: 180px">
          <template #body="{ data }">
            <span class="state-badge" :class="data.is_stuck ? 'badge--error' : 'badge--warn'">
              <span class="state-dot" />
              {{ data.state }}
            </span>
          </template>
        </Column>

        <Column field="stuck_for_sec" header="Duration" style="width: 130px">
          <template #body="{ data }">
            <span v-if="data.stuck_for_sec !== null" class="cell-duration" :class="{ 'cell-duration--stuck': data.is_stuck }">
              {{ formatDuration(data.stuck_for_sec) }}
            </span>
            <span v-else class="cell-dash">—</span>
          </template>
        </Column>

        <Column field="is_stuck" header="Status" style="width: 110px">
          <template #body="{ data }">
            <span v-if="data.is_stuck" class="stuck-badge">
              <i class="pi pi-exclamation-triangle" />
              STUCK
            </span>
            <span v-else class="ok-badge">
              <i class="pi pi-sync" />
              Syncing
            </span>
          </template>
        </Column>

        <Column header="" style="width: 150px; text-align: right">
          <template #body="{ data }">
            <Button
                icon="pi pi-refresh"
                label="Restart SST"
                size="small"
                severity="warning"
                outlined
                :loading="restartingId === data.node_id"
                :disabled="restartingId !== null"
                v-tooltip.left="`Restart MariaDB on ${data.node_name} to re-initiate SST`"
                class="restart-btn"
                @click="confirmRestart(data)"
            />
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-check-circle" />
            <span>No nodes in SST state</span>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Confirm restart dialog -->
    <ConfirmDialog group="restart-sst">
      <template #message="{ message }">
        <div class="confirm-body">
          <i class="pi pi-exclamation-triangle confirm-icon confirm-icon--warn" />
          <div>
            <div class="confirm-title">{{ message.header }}</div>
            <div class="confirm-text">{{ message.message }}</div>
          </div>
        </div>
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed }  from 'vue'
import { useQuery }       from '@tanstack/vue-query'
import { useConfirm }     from 'primevue/useconfirm'
import { useToast }       from 'primevue/usetoast'
import DataTable     from 'primevue/datatable'
import Column        from 'primevue/column'
import Button        from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import { useClusterStore }                    from '@/stores/cluster'
import { nodesApi, type SstStatusItem }       from '@/api/nodes'
import PanelToolbar                           from './PanelToolbar.vue'
import { useDiagAutoRefresh }                 from '@/composables/useDiagAutoRefresh'

const props        = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const confirm      = useConfirm()
const toast        = useToast()
const restartingId = ref<number | null>(null)

const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey:       computed(() => ['sst-status', clusterStore.selectedClusterId]),
  queryFn:        () => nodesApi.getSstStatus(clusterStore.selectedClusterId!),
  enabled:        computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime:      0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

// Enrich with node names from cluster store nodes list
const rows = computed(() => {
  const items: SstStatusItem[] = data.value ?? []
  return items.map((item) => ({
    ...item,
    node_name: clusterStore.nodes?.find((n) => n.id === item.node_id)?.name ?? `node-${item.node_id}`,
  }))
})

function formatDuration(sec: number): string {
  if (sec < 60)   return `${sec}s`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  return `${h}h ${m}m`
}

function confirmRestart(row: SstStatusItem & { node_name: string }) {
  confirm.require({
    group:       'restart-sst',
    header:      `Restart SST on ${row.node_name}?`,
    message:     `MariaDB will be restarted on ${row.node_name}. The node will re-join the cluster via SST/IST.`,
    icon:        'pi pi-exclamation-triangle',
    acceptLabel: 'Restart',
    rejectLabel: 'Cancel',
    acceptClass: 'p-button-warning',
    accept:      () => doRestart(row),
  })
}

async function doRestart(row: SstStatusItem & { node_name: string }) {
  if (!clusterStore.selectedClusterId) return
  restartingId.value = row.node_id
  try {
    const res = await nodesApi.restartSst(clusterStore.selectedClusterId, row.node_id)
    toast.add({
      severity: res.ok ? 'success' : 'warn',
      summary:  res.ok ? 'SST restart initiated' : 'SST restart: warning',
      detail:   res.message,
      life:     5000,
    })
    await refetch()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(err)
    toast.add({
      severity: 'error',
      summary:  'Restart SST failed',
      detail:   msg,
      life:     6000,
    })
  } finally {
    restartingId.value = null
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-12) var(--space-8);
}

.empty-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in oklch, var(--color-success) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-success) 25%, transparent);
  color: var(--color-success);
  font-size: 1.1rem;
}

.empty-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

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

:deep(.diag-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none;
}

.cell-node {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  color: var(--color-primary);
  font-weight: 600;
}

.cell-mono {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.cell-faint  { color: var(--color-text-faint); }
.cell-dash   { color: var(--color-text-faint); font-size: var(--text-xs); }

.cell-duration {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--color-text-muted);
}
.cell-duration--stuck {
  color: var(--color-error);
  text-shadow: 0 0 8px color-mix(in oklch, var(--color-error) 40%, transparent);
}

.state-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 3px var(--space-3);
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

@keyframes pulse-dot {
  0%, 100% { opacity: 1;    transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.6); }
}

.stuck-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-error);
}
.stuck-badge .pi { font-size: 0.7rem; }

.ok-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-warning);
}
.ok-badge .pi { font-size: 0.7rem; }

.restart-btn {
  white-space: nowrap;
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

.confirm-body {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-2) 0;
}
.confirm-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
  margin-top: 2px;
}
.confirm-icon--warn { color: var(--color-warning); }
.confirm-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}
.confirm-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}
</style>
