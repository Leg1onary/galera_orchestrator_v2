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
    <div class="progress-block">
      <div class="progress-meta">
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
    <!-- MAJOR fix: statusMap вместо повторных .includes() в template -->
    <div class="node-progress-list">
      <div
          v-for="nodeId in store.nodeOrder"
          :key="nodeId"
          class="node-progress-row"
          :class="`row--${statusMap.get(nodeId) ?? 'pending'}`"
      >
        <!-- Status icon -->
        <div class="row-icon">
          <ProgressSpinner
              v-if="statusMap.get(nodeId) === 'current'"
              class="spinner-sm"
          />
          <i v-else-if="statusMap.get(nodeId) === 'completed'" class="pi pi-check icon--success" />
          <i v-else-if="statusMap.get(nodeId) === 'failed'"    class="pi pi-times icon--error" />
          <i v-else                                             class="pi pi-circle icon--faint" />
        </div>

        <div class="row-info">
          <span class="row-name">{{ nodeName(nodeId) }}</span>
          <span class="row-host">{{ nodeHost(nodeId) }}</span>
        </div>

        <div class="row-status">
          <span v-if="statusMap.get(nodeId) === 'current'"    class="status-label status--current">Restarting…</span>
          <span v-else-if="statusMap.get(nodeId) === 'completed'" class="status-label status--completed">SYNCED</span>
          <span v-else-if="statusMap.get(nodeId) === 'failed'"    class="status-label status--failed">Failed</span>
          <span v-else                                             class="status-label status--pending">Waiting</span>
        </div>
      </div>
    </div>

    <!-- Operation error -->
    <div v-if="store.rrStatus?.error" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ store.rrStatus.error }}
    </div>

    <!-- Cancel button — только пока running -->
    <div v-if="store.operationRunning" class="step-actions">
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
import { computed } from 'vue'
// BLOCKER fix: раздельные импорты
import Button         from 'primevue/button'
import ProgressBar    from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

// MAJOR fix: O(n) Map вместо O(n²) .includes() в template
type NodeStatus = 'current' | 'completed' | 'failed' | 'pending'
const statusMap = computed((): Map<number, NodeStatus> => {
  const map = new Map<number, NodeStatus>()
  const s = store.rrStatus
  for (const nodeId of store.nodeOrder) {
    if (s?.current_node_id === nodeId)              map.set(nodeId, 'current')
    else if (s?.completed_node_ids.includes(nodeId)) map.set(nodeId, 'completed')
    else if (s?.failed_node_id === nodeId)           map.set(nodeId, 'failed')
    else                                             map.set(nodeId, 'pending')
  }
  return map
})

// MAJOR fix: n.id, n.name
function nodeName(id: number) {
  return store.nodes.find((n) => n.id === id)?.name ?? `Node #${id}`
}
function nodeHost(id: number) {
  return store.nodes.find((n) => n.id === id)?.host ?? ''
}
</script>

<style scoped>
.wizard-step { display: flex; flex-direction: column; gap: var(--space-4); }
.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title  { font-size: var(--text-lg); font-weight: 600; }
.step-desc   { font-size: var(--text-sm); color: var(--color-text-muted); }

.progress-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-md);
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.node-progress-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-progress-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition:
      border-color var(--transition-interactive),
      background   var(--transition-interactive);
}
.row--current   { border-color: var(--color-primary); background: var(--color-primary-highlight); }
.row--completed { border-color: var(--color-success); background: color-mix(in oklch, var(--color-success) 8%, transparent); }
.row--failed    { border-color: var(--color-error);   background: color-mix(in oklch, var(--color-error)   8%, transparent); }

.row-icon  { width: 24px; display: flex; justify-content: center; flex-shrink: 0; }
/* MINOR fix: spinner размер через класс */
.spinner-sm { width: 18px; height: 18px; }

.icon--success { color: var(--color-success); }
.icon--error   { color: var(--color-error); }
.icon--faint   { color: var(--color-text-faint); }

.row-info  { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.row-name  { font-weight: 500; font-size: var(--text-sm); }
.row-host  { font-family: monospace; font-size: var(--text-xs); color: var(--color-text-muted); }

.row-status    { min-width: 80px; text-align: right; }
.status-label  { font-size: var(--text-xs); }
.status--current   { color: var(--color-primary);      font-weight: 500; }
.status--completed { color: var(--color-success); }
.status--failed    { color: var(--color-error); }
.status--pending   { color: var(--color-text-muted); }

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

.step-actions { display: flex; justify-content: flex-end; }
</style>