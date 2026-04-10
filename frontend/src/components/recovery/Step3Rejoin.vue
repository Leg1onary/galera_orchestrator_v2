<template>
  <div class="wizard-step">

    <!-- HEADER -->
    <div class="step-header">
      <h2 class="step-title">Step 3 — Rejoin nodes</h2>
      <p class="step-desc">
        Bootstrap node is starting. Remaining nodes will rejoin automatically
        once the primary component is established.
      </p>
    </div>

    <!-- OVERALL PROGRESS -->
    <div class="progress-card">
      <div class="progress-top">
        <div class="progress-state">
          <ProgressSpinner v-if="isActiveState" style="width: 20px; height: 20px" />
          <span v-else-if="store.operationState === 'success'" class="state-icon state-icon--success">
            <i class="pi pi-check" />
          </span>
          <span v-else-if="store.operationState === 'failed'" class="state-icon state-icon--error">
            <i class="pi pi-times" />
          </span>
          <span v-else-if="store.operationState === 'cancelled'" class="state-icon state-icon--neutral">
            <i class="pi pi-ban" />
          </span>
          <span v-else class="state-icon state-icon--neutral">
            <i class="pi pi-clock" />
          </span>
          <span class="state-label">{{ stateLabel }}</span>
        </div>
        <span class="progress-pct">{{ store.progressPct }}%</span>
      </div>
      <ProgressBar :value="store.progressPct" :show-value="false" class="progress-bar" />
      <p v-if="store.progressMessage" class="progress-message">{{ store.progressMessage }}</p>
    </div>

    <!-- PER-NODE LIST -->
    <div class="node-rejoin-list">
      <div
          v-for="node in store.nodesNeedingRejoin"
          :key="node.node_id"
          class="node-rejoin-row"
          :class="`node-rejoin-row--${nodeStatus(node.node_id)}`"
      >
        <div class="node-rejoin-indicator">
          <ProgressSpinner v-if="nodeStatus(node.node_id) === 'running'" style="width: 16px; height: 16px" />
          <i v-else-if="nodeStatus(node.node_id) === 'success'" class="pi pi-check" />
          <i v-else-if="nodeStatus(node.node_id) === 'failed'"  class="pi pi-times" />
          <i v-else class="pi pi-circle" />
        </div>
        <div class="node-rejoin-info">
          <span class="node-rejoin-name">{{ node.node_name }}</span>
          <span class="node-rejoin-host">{{ node.host }}</span>
        </div>
        <span class="node-rejoin-status-label">{{ nodeStatusLabel(node.node_id) }}</span>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="store.operationError" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ store.operationError }}
    </div>

    <!-- CANCEL -->
    <div v-if="isActiveState" class="cancel-row">
      <Button
          label="Cancel operation"
          icon="pi pi-times"
          outlined
          severity="danger"
          size="small"
          :loading="store.cancelling || store.operationState === 'cancel_requested'"
          @click="store.cancelOperation()"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ next: [] }>()
const store = useRecoveryStore()

watch(() => store.operationState, (val) => {
  if (val === 'success') emit('next')
})

const isActiveState = computed(() =>
    store.operationState === 'running' ||
    store.operationState === 'cancel_requested'
)

const stateLabel = computed(() => ({
  pending:          'Pending…',
  running:          'Operation in progress…',
  success:          'Completed successfully',
  failed:           'Operation failed',
  cancel_requested: 'Cancelling…',
  cancelled:        'Cancelled by user',
}[store.operationState ?? 'pending'] ?? ''))

function nodeStatus(nodeId: number): 'running' | 'success' | 'failed' | 'pending' {
  const perNode = store.nodeRejoinStatus?.[nodeId]
  if (perNode) return perNode
  if (store.operationState === 'running')  return 'running'
  if (store.operationState === 'success')  return 'success'
  if (store.operationState === 'failed')   return 'failed'
  return 'pending'
}

function nodeStatusLabel(nodeId: number): string {
  return {
    running: 'Rejoining…',
    success: 'Joined',
    failed:  'Failed',
    pending: 'Waiting',
  }[nodeStatus(nodeId)] ?? ''
}
</script>

<style scoped>
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: 100%;
}

/* HEADER */
.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}
.step-desc { font-size: var(--text-sm); color: var(--color-text-muted); line-height: 1.5; }

/* PROGRESS CARD */
.progress-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.progress-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.progress-state {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.state-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.state-icon {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}
.state-icon--success {
  background: color-mix(in oklch, var(--color-success) 15%, transparent);
  color: var(--color-success);
}
.state-icon--error {
  background: color-mix(in oklch, var(--color-error) 15%, transparent);
  color: var(--color-error);
}
.state-icon--neutral {
  background: var(--color-surface-dynamic);
  color: var(--color-text-muted);
}
.progress-pct {
  font-size: var(--text-sm);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-primary);
}
.progress-bar { height: 6px !important; }
.progress-message {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: 0;
  font-style: italic;
}

/* NODE LIST */
.node-rejoin-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.node-rejoin-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color 200ms ease, background 200ms ease;
}
.node-rejoin-row--running {
  border-color: color-mix(in oklch, var(--color-primary) 40%, transparent);
  background: color-mix(in oklch, var(--color-primary) 5%, var(--color-surface-offset));
}
.node-rejoin-row--success {
  border-color: color-mix(in oklch, var(--color-success) 35%, transparent);
}
.node-rejoin-row--failed {
  border-color: color-mix(in oklch, var(--color-error) 35%, transparent);
}

.node-rejoin-indicator {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.8rem;
}
.node-rejoin-row--success .node-rejoin-indicator { color: var(--color-success); }
.node-rejoin-row--failed  .node-rejoin-indicator { color: var(--color-error); }
.node-rejoin-row--pending .node-rejoin-indicator { color: var(--color-text-faint); }

.node-rejoin-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.node-rejoin-name { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.node-rejoin-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.node-rejoin-status-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-text-faint);
}
.node-rejoin-row--running .node-rejoin-status-label { color: var(--color-primary); }
.node-rejoin-row--success .node-rejoin-status-label { color: var(--color-success); }
.node-rejoin-row--failed  .node-rejoin-status-label { color: var(--color-error); }

/* ERROR */
.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

/* CANCEL */
.cancel-row {
  display: flex;
  justify-content: flex-end;
  margin-top: auto;
}
</style>
