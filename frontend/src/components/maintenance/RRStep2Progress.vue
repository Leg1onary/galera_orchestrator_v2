<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 2 — Restarting nodes</h2>
      <p class="step-desc">
        Each node is restarted sequentially. The next node starts only after
        the previous one reaches <strong>SYNCED</strong>.
      </p>
    </div>

    <!-- Overall progress -->
    <div class="progress-block mb-4">
      <div class="flex justify-between text-xs text-muted-color mb-1">
        <span>{{ store.rrStatus?.message ?? 'Initialising…' }}</span>
        <span>{{ store.rrStatus?.progress_pct ?? 0 }}%</span>
      </div>
      <ProgressBar
          :value="store.rrStatus?.progress_pct ?? 0"
          :show-value="false"
          style="height: 8px"
      />
    </div>

    <!-- Per-node status list -->
    <div class="node-progress-list mb-4">
      <div
          v-for="nodeId in store.nodeOrder"
          :key="nodeId"
          class="node-progress-row"
          :class="{
          'row--current':   store.rrStatus?.current_node_id === nodeId,
          'row--completed': store.rrStatus?.completed_node_ids.includes(nodeId),
          'row--failed':    store.rrStatus?.failed_node_id === nodeId,
          'row--pending':   isPending(nodeId),
        }"
      >
        <!-- Status icon -->
        <div class="row-icon">
          <ProgressSpinner
              v-if="store.rrStatus?.current_node_id === nodeId"
              style="width: 18px; height: 18px"
          />
          <i
              v-else-if="store.rrStatus?.completed_node_ids.includes(nodeId)"
              class="pi pi-check"
              style="color: var(--color-success)"
          />
          <i
              v-else-if="store.rrStatus?.failed_node_id === nodeId"
              class="pi pi-times"
              style="color: var(--color-error)"
          />
          <i
              v-else
              class="pi pi-circle"
              style="color: var(--color-text-faint)"
          />
        </div>

        <div class="row-info">
          <span class="font-medium text-sm">{{ nodeName(nodeId) }}</span>
          <span class="font-mono text-xs text-muted-color">{{ nodeHost(nodeId) }}</span>
        </div>

        <div class="row-status">
          <span
              v-if="store.rrStatus?.current_node_id === nodeId"
              class="text-xs text-primary-color font-medium"
          >
            Restarting…
          </span>
          <span
              v-else-if="store.rrStatus?.completed_node_ids.includes(nodeId)"
              class="text-xs text-success-color"
          >
            SYNCED
          </span>
          <span
              v-else-if="store.rrStatus?.failed_node_id === nodeId"
              class="text-xs text-error-color"
          >
            Failed
          </span>
          <span v-else class="text-xs text-muted-color">Waiting</span>
        </div>
      </div>
    </div>

    <!-- Operation error -->
    <div v-if="store.rrStatus?.error" class="error-alert mb-4">
      <i class="pi pi-times-circle" />
      {{ store.rrStatus.error }}
    </div>

    <!-- Cancel button — только пока running -->
    <div v-if="store.operationRunning" class="flex justify-end">
      <Button
          label="Cancel after current node"
          icon="pi pi-times"
          outlined
          severity="danger"
          size="small"
          :loading="store.cancelling"
          @click="store.cancelOperation()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, ProgressBar, ProgressSpinner } from 'primevue'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

function nodeName(id: number) {
  return store.nodes.find((n) => n.node_id === id)?.node_name ?? `Node #${id}`
}
function nodeHost(id: number) {
  return store.nodes.find((n) => n.node_id === id)?.host ?? ''
}
function isPending(nodeId: number) {
  const s = store.rrStatus
  if (!s) return true
  return (
      s.current_node_id !== nodeId &&
      !s.completed_node_ids.includes(nodeId) &&
      s.failed_node_id !== nodeId
  )
}
</script>

<style scoped>
.progress-block {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-md);
}
.node-progress-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-progress-row {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--transition-interactive), background var(--transition-interactive);
}
.row--current   { border-color: var(--color-primary); background: var(--color-primary-highlight); }
.row--completed { border-color: var(--color-success);  background: color-mix(in oklch, var(--color-success) 8%, transparent); }
.row--failed    { border-color: var(--color-error);    background: color-mix(in oklch, var(--color-error) 8%, transparent); }
.row-icon { width: 24px; display: flex; justify-content: center; }
.row-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.row-status { min-width: 80px; text-align: right; }
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
</style>