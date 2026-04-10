<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 3 — Rejoin nodes</h2>
      <p class="step-desc">
        Bootstrap node is starting. Remaining nodes will rejoin automatically
        once the primary component is established.
      </p>
    </div>

    <!-- Overall progress -->
    <div class="progress-block">
      <div class="progress-header">
        <span>{{ store.progressMessage ?? 'Initialising…' }}</span>
        <span>{{ store.progressPct }}%</span>
      </div>
      <ProgressBar :value="store.progressPct" :show-value="false" style="height: 8px" />
    </div>

    <!-- State badge -->
    <div class="state-badge">
      <ProgressSpinner
          v-if="isActiveState"
          style="width: 20px; height: 20px"
      />
      <i
          v-else-if="store.operationState === 'success'"
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
      <span class="state-label">{{ stateLabel }}</span>
    </div>

    <!-- Per-node rejoin list (MAJOR fix: per-node статус) -->
    <div class="node-rejoin-list">
      <div
          v-for="node in store.nodesNeedingRejoin"
          :key="node.node_id"
          class="node-rejoin-row"
      >
        <span class="node-name">{{ node.node_name }}</span>
        <span class="node-host">{{ node.host }}</span>
        <div class="node-rejoin-status">
          <ProgressSpinner
              v-if="nodeStatus(node.node_id) === 'running'"
              style="width: 16px; height: 16px"
          />
          <i
              v-else-if="nodeStatus(node.node_id) === 'success'"
              class="pi pi-check"
              style="color: var(--color-success)"
          />
          <i
              v-else-if="nodeStatus(node.node_id) === 'failed'"
              class="pi pi-times"
              style="color: var(--color-error)"
          />
          <span
              v-else
              style="color: var(--color-text-faint); font-size: var(--text-xs)"
          >—</span>
        </div>
      </div>
    </div>

    <!-- Error detail -->
    <div v-if="store.operationError" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ store.operationError }}
    </div>

    <!-- Cancel (только пока running / cancel_requested) -->
    <div v-if="isActiveState" class="cancel-row">
      <Button
          label="Cancel"
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
// BLOCKER fix: раздельные импорты
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import { useRecoveryStore } from '@/stores/recovery'

// BLOCKER fix: объявлен emit
const emit = defineEmits<{ next: [] }>()
const store = useRecoveryStore()

// BLOCKER fix: watch на state → переход на Step4
watch(
    () => store.operationState,
    (val) => {
      if (val === 'success') emit('next')
    }
)

// Активные состояния — показываем spinner и кнопку Cancel
const isActiveState = computed(() =>
    store.operationState === 'running' ||
    store.operationState === 'cancel_requested'
)

// MINOR fix: добавлен cancel_requested по ТЗ п.13.6
const stateLabel = computed(() => ({
  pending:          'Pending…',
  running:          'Operation in progress…',
  success:          'Completed successfully',
  failed:           'Operation failed',
  cancel_requested: 'Cancelling…',
  cancelled:        'Cancelled by user',
}[store.operationState ?? 'pending'] ?? ''))

// MAJOR fix: per-node статус из store.nodeRejoinStatus
// Fallback: если store не хранит per-node данные — используем общий state
function nodeStatus(nodeId: number): 'running' | 'success' | 'failed' | 'pending' {
  const perNode = store.nodeRejoinStatus?.[nodeId]
  if (perNode) return perNode
  // fallback на общий state
  if (store.operationState === 'running')  return 'running'
  if (store.operationState === 'success')  return 'success'
  if (store.operationState === 'failed')   return 'failed'
  return 'pending'
}
</script>

<style scoped>
.wizard-step { display: flex; flex-direction: column; gap: var(--space-4); }
.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title  { font-size: var(--text-lg); font-weight: 600; }
.step-desc   { font-size: var(--text-sm); color: var(--color-text-muted); }

.progress-block {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.state-badge {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.state-label { font-size: var(--text-sm); font-weight: 500; }

.node-rejoin-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-rejoin-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
}
.node-name        { font-size: var(--text-sm); font-weight: 500; }
.node-host        { font-size: var(--text-xs); color: var(--color-text-muted); }
.node-rejoin-status { margin-left: auto; display: flex; align-items: center; }

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

.cancel-row {
  display: flex;
  justify-content: flex-end;
}
</style>