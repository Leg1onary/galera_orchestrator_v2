<!--
  NodeMaintenanceTable — таблица нод с состоянием maintenance + desync.
  Actions: Enter / Exit maintenance per node, Desync / Resync per node.
  Rolling restart запускается через store.openWizard().
-->
<template>
  <div class="section-block">
    <!-- Toolbar -->
    <div class="section-toolbar">
      <div class="section-title-wrap">
        <i class="pi pi-wrench section-icon" />
        <h2 class="section-heading">Node maintenance state</h2>
      </div>
      <div class="toolbar-actions">
        <Button
            icon="pi pi-refresh"
            text rounded size="small"
            :loading="store.nodesLoading"
            aria-label="Refresh nodes"
            @click="store.loadNodes()"
        />
        <span
          v-tooltip.top="store.operationRunning ? 'A rolling restart is already in progress' : undefined"
          :class="{ 'btn-wrap-disabled': store.operationRunning }"
        >
          <Button
              label="Rolling restart"
              icon="pi pi-sync"
              size="small"
              :disabled="store.operationRunning"
              :pt="{ root: { style: 'padding-inline: 1rem' } }"
              @click="store.openWizard()"
          />
        </span>
      </div>
    </div>

    <!-- Drift warning -->
    <Message v-if="store.hasDrift" severity="warning" class="drift-message">
      One or more nodes have a <strong>maintenance drift</strong> —
      maintenance is enabled in the database but MariaDB
      <code>read_only</code> is OFF. This may indicate an unexpected restart.
    </Message>

    <!-- Error -->
    <div v-if="store.nodesError" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ store.nodesError }}</span>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <DataTable
          :value="store.nodes"
          :loading="store.nodesLoading"
          dataKey="id"
          size="small"
          row-hover
          class="maint-table"
      >
        <Column field="name" header="Node" :sortable="true">
          <template #body="{ data }">
            <div class="cell-node">
              <span class="cell-node-name">{{ data.name }}</span>
              <span class="cell-node-host">{{ data.host }}</span>
            </div>
          </template>
        </Column>

        <Column field="wsrep_local_state_comment" header="State" style="width: 120px">
          <template #body="{ data }">
            <NodeStateBadge :state="data.wsrep_local_state_comment" />
          </template>
        </Column>

        <Column field="readonly" header="read_only" style="width: 110px">
          <template #body="{ data }">
            <Tag
                :value="data.readonly ? 'ON' : 'OFF'"
                :severity="data.readonly ? 'secondary' : 'success'"
                class="cell-tag"
            />
          </template>
        </Column>

        <Column field="maintenance" header="Maintenance" style="width: 150px">
          <template #body="{ data }">
            <div class="cell-maintenance">
              <Tag
                  :value="data.maintenance ? 'ENABLED' : 'OFF'"
                  :severity="data.maintenance ? 'warning' : 'secondary'"
                  class="cell-tag"
              />
              <i
                  v-if="data.maintenanceDrift"
                  v-tooltip="'Drift: maintenance=ON in DB but read_only=OFF in MariaDB'"
                  class="pi pi-exclamation-triangle drift-icon"
              />
            </div>
          </template>
        </Column>

        <!-- Desync column -->
        <Column field="wsrep_desync" header="wsrep_desync" style="width: 130px">
          <template #body="{ data }">
            <Tag
                v-if="data.wsrep_desync"
                value="DESYNCED"
                severity="warn"
                class="cell-tag"
            />
            <Tag
                v-else
                value="OFF"
                severity="secondary"
                class="cell-tag"
            />
          </template>
        </Column>

        <Column header="Actions" style="width: 220px">
          <template #body="{ data }">
            <div class="cell-actions">
              <!-- Maintenance toggle -->
              <Button
                  v-if="!data.maintenance"
                  label="Enter"
                  icon="pi pi-lock"
                  size="small"
                  outlined
                  :loading="store.nodeActionLoading[data.id]"
                  :disabled="!data.enabled || store.operationRunning"
                  @click="handleToggleMaintenance(data.id, true)"
              />
              <Button
                  v-else
                  label="Exit"
                  icon="pi pi-lock-open"
                  size="small"
                  severity="secondary"
                  :loading="store.nodeActionLoading[data.id]"
                  :disabled="store.operationRunning"
                  @click="handleToggleMaintenance(data.id, false)"
              />

              <!-- Desync / Resync -->
              <Button
                  v-if="!data.wsrep_desync"
                  v-tooltip.top="'Disable Galera flow control on this node (wsrep_desync=ON). Use before heavy operations to avoid slowing down the cluster.'"
                  label="Desync"
                  icon="pi pi-pause"
                  size="small"
                  severity="warn"
                  outlined
                  :loading="store.nodeDesyncLoading[data.id]"
                  :disabled="!data.enabled || store.operationRunning"
                  @click="handleDesync(data, true)"
              />
              <Button
                  v-else
                  v-tooltip.top="'Re-enable Galera flow control (wsrep_desync=OFF). Node will catch up with the cluster.'"
                  label="Resync"
                  icon="pi pi-play"
                  size="small"
                  severity="secondary"
                  :loading="store.nodeDesyncLoading[data.id]"
                  :disabled="!data.enabled || store.operationRunning"
                  @click="handleDesync(data, false)"
              />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-row">
            <i class="pi pi-server" />
            <span>No nodes available</span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button    from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column    from 'primevue/column'
import Tag       from 'primevue/tag'
import Message   from 'primevue/message'
import { useToast }   from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeStateBadge from '@/components/shared/NodeStateBadge.vue'
import type { MaintenanceNodeState } from '@/api/maintenance'

const store   = useMaintenanceStore()
const toast   = useToast()
const confirm = useConfirm()

// ── Maintenance toggle ───────────────────────────────────────────────────────
async function handleToggleMaintenance(nodeId: number, enter: boolean) {
  try {
    await store.toggleMaintenance(nodeId, enter)
    toast.add({
      severity: 'success',
      summary: enter ? 'Maintenance enabled' : 'Maintenance disabled',
      life: 2500,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? err.message,
      life: 5000,
    })
  }
}

// ── Desync / Resync ──────────────────────────────────────────────────────────
function handleDesync(node: MaintenanceNodeState, desync: boolean) {
  if (desync) {
    // Десинк — деструктивное действие, требует подтверждения
    confirm.require({
      header:  'Desync node',
      message: `Remove "${node.name}" from Galera flow control? The node will fall behind and catch up on resync.`,
      icon:    'pi pi-pause-circle',
      acceptLabel:   'Desync',
      rejectLabel:   'Cancel',
      acceptClass:   'p-button-warning',
      accept: () => doDesync(node.id, true),
    })
  } else {
    // Ресинк безопасен — без подтверждения
    doDesync(node.id, false)
  }
}

async function doDesync(nodeId: number, desync: boolean) {
  try {
    await store.toggleDesync(nodeId, desync)
    toast.add({
      severity: 'success',
      summary:  desync ? 'Node desynced' : 'Node resynced',
      detail:   desync
        ? 'wsrep_desync = ON — node is out of flow control'
        : 'wsrep_desync = OFF — node back in flow control',
      life: 3000,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary:  'Error',
      detail:   err?.response?.data?.detail ?? err.message,
      life:     5000,
    })
  }
}
</script>

<style scoped>
/* ── Block ───────────────────────────────────────────── */
.section-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* ── Toolbar ─────────────────────────────────────────── */
.section-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-2);
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.section-icon {
  font-size: var(--text-base);
  color: var(--color-text-muted);
}
.section-heading {
  font-size: var(--text-sm);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.btn-wrap-disabled {
  display: inline-flex;
  cursor: not-allowed;
}
.btn-wrap-disabled :deep(.p-button:disabled) {
  pointer-events: none;
}

/* ── Drift / Error ───────────────────────────────────── */
.drift-message {
  margin: 0 var(--space-5);
}

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 var(--space-5);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.error-alert .pi { flex-shrink: 0; }

/* ── Table wrap ──────────────────────────────────────── */
.table-wrap {
  overflow: hidden;
}

/* ── DataTable overrides ─────────────────────────────── */
:deep(.maint-table .p-datatable-thead > tr > th) {
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

:deep(.maint-table .p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-5);
  vertical-align: middle;
  border: none;
  border-bottom: 1px solid var(--color-border-muted, var(--color-border));
}

:deep(.maint-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none;
}

/* ── Cells ───────────────────────────────────────────── */
.cell-node {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cell-node-name {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-text);
}
.cell-node-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.cell-tag {
  font-size: var(--text-xs);
}

.cell-maintenance {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.drift-icon {
  color: var(--color-warning);
  font-size: var(--text-xs);
}

.cell-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  align-items: center;
}

/* ── Empty state ─────────────────────────────────────── */
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
.empty-row .pi {
  font-size: 1.5rem;
  opacity: 0.35;
}
</style>
