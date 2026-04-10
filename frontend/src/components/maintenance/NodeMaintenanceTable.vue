<template>
  <div class="section-block">
    <div class="section-toolbar">
      <h2 class="section-title">Node maintenance state</h2>
      <div class="toolbar-right">
        <Button
            icon="pi pi-refresh"
            text rounded size="small"
            :loading="store.nodesLoading"
            aria-label="Refresh"
            @click="store.loadNodes()"
        />
        <Button
            label="Rolling restart"
            icon="pi pi-sync"
            size="small"
            :disabled="store.operationRunning"
            @click="store.openWizard()"
        />
      </div>
    </div>

    <!-- Drift warning (ТЗ п.14.10) -->
    <!-- MAJOR fix: severity 'warn' → 'warning' -->
    <Message v-if="store.hasDrift" severity="warning" style="margin-bottom: var(--space-3)">
      One or more nodes have a <strong>maintenance drift</strong> —
      maintenance is enabled in the database but MariaDB
      <code>read_only</code> is OFF. This may indicate an unexpected restart.
    </Message>

    <!-- Error -->
    <div v-if="store.nodesError" class="error-alert" style="margin-bottom: var(--space-3)">
      <i class="pi pi-exclamation-circle" />
      {{ store.nodesError }}
    </div>

    <DataTable
        :value="store.nodes"
        :loading="store.nodesLoading"
        dataKey="id"
        size="small"
    >
      <!-- Node name -->
      <Column field="name" header="Node" :sortable="true">
        <template #body="{ data }">
          <span style="font-weight: 500">{{ data.name }}</span>
          <span style="font-size: var(--text-xs); color: var(--color-text-muted); margin-left: var(--space-2); font-family: monospace">
            {{ data.host }}
          </span>
        </template>
      </Column>

      <!-- wsrep state -->
      <!-- MAJOR fix: wsrep_local_state_comment -->
      <Column field="wsrep_local_state_comment" header="State" style="width: 110px">
        <template #body="{ data }">
          <NodeStateBadge :state="data.wsrep_local_state_comment" />
        </template>
      </Column>

      <!-- read_only -->
      <!-- MAJOR fix: data.readonly -->
      <Column field="readonly" header="read_only" style="width: 100px">
        <template #body="{ data }">
          <Tag
              :value="data.readonly ? 'ON' : 'OFF'"
              :severity="data.readonly ? 'secondary' : 'success'"
              style="font-size: var(--text-xs)"
          />
        </template>
      </Column>

      <!-- Maintenance -->
      <!-- MAJOR fix: data.maintenance + data.maintenanceDrift -->
      <Column field="maintenance" header="Maintenance" style="width: 130px">
        <template #body="{ data }">
          <div class="maintenance-cell">
            <!-- MAJOR fix: severity 'warn' → 'warning' -->
            <Tag
                :value="data.maintenance ? 'ENABLED' : 'OFF'"
                :severity="data.maintenance ? 'warning' : 'secondary'"
                style="font-size: var(--text-xs)"
            />
            <i
                v-if="data.maintenanceDrift"
                v-tooltip="'Drift: maintenance=ON in DB but read_only=OFF in MariaDB'"
                class="pi pi-exclamation-triangle"
                style="color: var(--color-warning); font-size: var(--text-xs)"
            />
          </div>
        </template>
      </Column>

      <!-- Actions -->
      <Column header="Actions" style="width: 160px">
        <template #body="{ data }">
          <div class="action-cell">
            <Button
                v-if="!data.maintenance"
                label="Enter"
                icon="pi pi-lock"
                size="small"
                outlined
                :loading="store.nodeActionLoading[data.id]"
                :disabled="!data.enabled || store.operationRunning"
                @click="handleToggle(data.id, true)"
            />
            <Button
                v-else
                label="Exit"
                icon="pi pi-lock-open"
                size="small"
                severity="secondary"
                :loading="store.nodeActionLoading[data.id]"
                :disabled="store.operationRunning"
                @click="handleToggle(data.id, false)"
            />
          </div>
        </template>
      </Column>

      <template #empty>
        <div class="empty-row">No nodes available.</div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
// BLOCKER fix: раздельные импорты
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeStateBadge from '@/components/shared/NodeStateBadge.vue'

const store = useMaintenanceStore()
const toast = useToast()

async function handleToggle(nodeId: number, enter: boolean) {
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
</script>

<style scoped>
.section-block {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
}
.section-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.section-title  { font-size: var(--text-lg); font-weight: 600; }
.toolbar-right  { display: flex; align-items: center; gap: var(--space-2); }

.maintenance-cell { display: flex; align-items: center; gap: var(--space-2); }
.action-cell      { display: flex; gap: var(--space-1); }

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

/* MINOR fix: добавлен empty-row */
.empty-row {
  padding: var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>