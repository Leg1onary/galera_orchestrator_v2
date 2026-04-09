<template>
  <div class="section-block">
    <div class="section-toolbar">
      <h2 class="section-title">Node maintenance state</h2>
      <div class="flex items-center gap-2">
        <Button
            icon="pi pi-refresh"
            text
            rounded
            size="small"
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

    <!-- Drift warning -->
    <Message v-if="store.hasDrift" severity="warn" class="mb-3">
      One or more nodes have a <strong>maintenance drift</strong> —
      maintenance is enabled in the database but MariaDB
      <code>read_only</code> is OFF. This may indicate an unexpected restart.
    </Message>

    <!-- Error -->
    <div v-if="store.nodesError" class="error-alert mb-3">
      <i class="pi pi-exclamation-circle" />
      {{ store.nodesError }}
    </div>

    <DataTable
        :value="store.nodes"
        :loading="store.nodesLoading"
        dataKey="node_id"
        size="small"
    >
      <Column field="node_name" header="Node" :sortable="true">
        <template #body="{ data }">
          <span class="font-medium">{{ data.node_name }}</span>
          <span class="text-xs text-muted-color ml-2 font-mono">{{ data.host }}</span>
        </template>
      </Column>

      <Column field="wsrep_state" header="State" style="width: 110px">
        <template #body="{ data }">
          <NodeStateBadge :state="data.wsrep_state" />
        </template>
      </Column>

      <Column field="read_only" header="read_only" style="width: 100px">
        <template #body="{ data }">
          <Tag
              :value="data.read_only ? 'ON' : 'OFF'"
              :severity="data.read_only ? 'secondary' : 'success'"
              class="text-xs"
          />
        </template>
      </Column>

      <Column field="maintenance" header="Maintenance" style="width: 130px">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <Tag
                :value="data.maintenance ? 'ENABLED' : 'OFF'"
                :severity="data.maintenance ? 'warn' : 'secondary'"
                class="text-xs"
            />
            <!-- Drift indicator -->
            <i
                v-if="data.maintenance_drift"
                v-tooltip="'Drift: maintenance=ON in DB but read_only=OFF in MariaDB'"
                class="pi pi-exclamation-triangle text-xs"
                style="color: var(--color-warning)"
            />
          </div>
        </template>
      </Column>

      <Column header="Actions" style="width: 160px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button
                v-if="!data.maintenance"
                label="Enter"
                icon="pi pi-lock"
                size="small"
                outlined
                :loading="store.nodeActionLoading[data.node_id]"
                :disabled="!data.enabled || store.operationRunning"
                @click="handleToggle(data.node_id, true)"
            />
            <Button
                v-else
                label="Exit"
                icon="pi pi-lock-open"
                size="small"
                severity="secondary"
                :loading="store.nodeActionLoading[data.node_id]"
                :disabled="store.operationRunning"
                @click="handleToggle(data.node_id, false)"
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
import { useToast, DataTable, Column, Button, Tag, Message } from 'primevue'
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
.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
}
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
</style>