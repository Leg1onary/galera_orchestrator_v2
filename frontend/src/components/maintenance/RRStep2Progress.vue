<!--
  Step 2 — Restarting nodes.
  Показывает общий прогресс и статус каждой ноды.
-->
<template>
  <div class="wizard-step">
    <!-- Header -->
    <div class="step-header">
      <h2 class="step-title">Restarting nodes</h2>
      <p class="step-desc">
        Each node is restarted sequentially. The next node starts only after
        the previous one reaches <strong>SYNCED</strong>.
      </p>
    </div>

    <!-- Overall progress -->
    <div class="progress-block">
      <div class="progress-meta">
        <span class="progress-message">{{ store.rrStatus?.message ?? 'Initialising…' }}</span>
        <span class="progress-pct">{{ store.rrStatus?.progress_pct ?? 0 }}%</span>
      </div>
      <ProgressBar
          :value="store.rrStatus?.progress_pct ?? 0"
          :show-value="false"
          class="progress-bar"
      />
    </div>

    <!-- Per-node list -->
    <div class="node-progress-list">
      <div
          v-for="nodeId in store.nodeOrder"
          :key="nodeId"
          class="node-progress-row"
          :class="`row--${statusMap.get(nodeId) ?? 'pending'}`"
      >
        <!-- Status icon -->
        <div class="row-icon">
          <ProgressSpinner v-if="statusMap.get(nodeId) === 'current'" class="spinner-sm" />
          <i v-else-if="statusMap.get(nodeId) === 'completed'" class="pi pi-check icon--success" />
          <i v-else-if="statusMap.get(nodeId) === 'failed'"    class="pi pi-times icon--error" />
          <i v-else                                             class="pi pi-circle icon--faint" />
        </div>

        <!-- Node info -->
        <div class="row-info">
          <span class="row-name">{{ nodeName(nodeId) }}</span>
          <span class="row-host">{{ nodeHost(nodeId) }}</span>
        </div>

        <!-- Status label -->
        <div class="row-status">
          <span v-if="statusMap.get(nodeId) === 'current'"     class="status-label status--current">Restarting…</span>
          <span v-else-if="statusMap.get(nodeId) === 'completed'" class="status-label status--done">SYNCED</span>
          <span v-else-if="statusMap.get(nodeId) === 'failed'"    class="status-label status--fail">Failed</span>
          <span v-else                                             class="status-label status--wait">Waiting</span>
        </div>
      </div>
    </div>

    <!-- Operation error -->
    <div v-if="store.rrStatus?.error" class="error-alert">
      <i class="pi pi-times-circle" />
      <span>{{ store.rrStatus.error }}</span>
    </div>

    <!-- Cancel -->
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
import Button          from 'primevue/button'
import ProgressBar     from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

type NodeStatus = 'current' | 'completed' | 'failed' | 'pending'
const statusMap = computed((): Map<number, NodeStatus> => {
  const map = new Map<number, NodeStatus>()
  const s   = store.rrStatus
  for (const nodeId of store.nodeOrder) {
    if (s?.current_node_id === nodeId)               map.set(nodeId, 'current')
    else if (s?.completed_node_ids.includes(nodeId)) map.set(nodeId, 'completed')
    else if (s?.failed_node_id === nodeId)           map.set(nodeId, 'failed')
    else                                             map.set(nodeId, 'pending')
  }
  return map
})

function nodeName(id: number) {
  return store.nodes.find((n) => n.id === id)?.name ?? `Node #${id}`
}
function nodeHost(id: number) {
  return store.nodes.find((n) => n.id === id)?.host ?? ''
}
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────────── */
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── Header ──────────────────────────────────────────── */
.step-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.step-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
}
.step-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.55;
}

/* ── Progress block ──────────────────────────────────── */
.progress-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.progress-message {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
.progress-pct {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
:deep(.progress-bar) {
  height: 6px;
  border-radius: var(--radius-full);
}

/* ── Node list ───────────────────────────────────────── */
.node-progress-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.node-progress-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition:
      border-color  var(--transition-interactive),
      background    var(--transition-interactive);
}
.row--current {
  border-color: var(--color-primary);
  background: color-mix(in oklch, var(--color-primary) 6%, var(--color-surface));
}
.row--completed {
  border-color: color-mix(in oklch, var(--color-success) 40%, var(--color-border));
  background: color-mix(in oklch, var(--color-success) 5%, var(--color-surface));
}
.row--failed {
  border-color: color-mix(in oklch, var(--color-error) 40%, var(--color-border));
  background: color-mix(in oklch, var(--color-error) 5%, var(--color-surface));
}

.row-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.spinner-sm { width: 18px !important; height: 18px !important; }
.icon--success { color: var(--color-success); font-size: var(--text-base); }
.icon--error   { color: var(--color-error);   font-size: var(--text-base); }
.icon--faint   { color: var(--color-text-faint); font-size: var(--text-sm); }

.row-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.row-name {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.row-host {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.row-status {
  flex-shrink: 0;
  min-width: 80px;
  text-align: right;
}
.status-label     { font-size: var(--text-xs); font-weight: 600; }
.status--current  { color: var(--color-primary); }
.status--done     { color: var(--color-success); }
.status--fail     { color: var(--color-error); }
.status--wait     { color: var(--color-text-faint); font-weight: 400; }

/* ── Error ───────────────────────────────────────────── */
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
.error-alert .pi { flex-shrink: 0; }

/* ── Actions ─────────────────────────────────────────── */
.step-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}
</style>
