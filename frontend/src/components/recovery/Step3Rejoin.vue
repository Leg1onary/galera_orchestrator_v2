<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 3 — Rejoin nodes</h2>
      <p class="step-desc">
        Bootstrap node is starting. Remaining nodes will rejoin automatically
        once the primary component is established.
      </p>
    </div>

    <!-- Overall progress bar -->
    <div class="progress-block mb-4">
      <div class="flex justify-between text-xs text-muted-color mb-1">
        <span>{{ store.progressMessage ?? 'Initialising…' }}</span>
        <span>{{ store.progressPct }}%</span>
      </div>
      <ProgressBar :value="store.progressPct" :show-value="false" style="height: 8px" />
    </div>

    <!-- State badge -->
    <div class="flex items-center gap-2 mb-4">
      <ProgressSpinner
          v-if="store.operationState === 'running'"
          style="width: 20px; height: 20px"
      />
      <i
          v-else-if="store.operationState === 'finished'"
          class="pi pi-check-circle"
          style="color: var(--color-success); font-size: 1.25rem"
      />
      <i
          v-else-if="store.operationState === 'failed'"
          class="pi pi-times-circle"
          style="color: var(--color-error); font-size: 1.25rem"
      />
      <i
          v-else-if="store.operationState === 'cancelled'"
          class="pi pi-ban"
          style="color: var(--color-text-muted); font-size: 1.25rem"
      />
      <span class="text-sm font-medium">{{ stateLabel }}</span>
    </div>

    <!-- Nodes rejoin list -->
    <div class="node-rejoin-list mb-4">
      <div
          v-for="node in store.nodesNeedingRejoin"
          :key="node.node_id"
          class="node-rejoin-row"
      >
        <span class="text-sm font-medium">{{ node.node_name }}</span>
        <span class="text-xs text-muted-color">{{ node.host }}</span>
        <ProgressSpinner
            v-if="store.operationState === 'running'"
            style="width: 16px; height: 16px; margin-left: auto"
        />
        <i
            v-else-if="store.operationState === 'finished'"
            class="pi pi-check"
            style="color: var(--color-success); margin-left: auto"
        />
      </div>
    </div>

    <!-- Error detail -->
    <div v-if="store.operationError" class="error-alert mb-4">
      <i class="pi pi-times-circle" />
      {{ store.operationError }}
    </div>

    <!-- Cancel (only while running) -->
    <div v-if="store.operationState === 'running'" class="flex justify-end">
      <Button
          label="Cancel"
          icon="pi pi-times"
          outlined
          severity="danger"
          size="small"
          :loading="store.cancelling"
          @click="store.cancelOperation()"
      />
    </div>

    <!-- note: кнопка Finish появляется в Step4Done, переход туда по WS-событию -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button, ProgressBar, ProgressSpinner } from 'primevue'
import { useRecoveryStore } from '@/stores/recovery'

const store = useRecoveryStore()

const stateLabel = computed(() => ({
  pending:   'Pending…',
  running:   'Operation in progress…',
  finished:  'Completed successfully',
  failed:    'Operation failed',
  cancelled: 'Cancelled by user',
}[store.operationState ?? 'pending'] ?? ''))
</script>

<style scoped>
.progress-block { padding: var(--space-3) var(--space-4); background: var(--color-surface); border-radius: var(--radius-md); }
.node-rejoin-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-rejoin-row {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
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