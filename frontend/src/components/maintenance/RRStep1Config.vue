<!--
  Step 1 — Configure restart order.
  Drag-to-reorder нод через VueUse useSortable.
  Таймаут ожидания SYNCED.
-->
<template>
  <div class="wizard-step">

    <!-- Header -->
    <div class="step-header">
      <h2 class="step-title">Configure restart order</h2>
      <p class="step-desc">
        Drag nodes to set the restart order. The next node starts only after
        the previous one reaches <strong>SYNCED</strong>.
      </p>
    </div>

    <!-- Drag list -->
    <div class="node-order-section">
      <div v-if="localOrder.length === 0" class="node-order-empty">
        <i class="pi pi-info-circle" />
        <span>No nodes available to reorder.</span>
      </div>
      <div v-else ref="sortableEl" class="node-order-list">
        <div
            v-for="nodeId in localOrder"
            :key="nodeId"
            class="node-order-item"
            :data-id="nodeId"
        >
          <i class="pi pi-bars drag-handle" />
          <div class="node-order-info">
            <span class="node-name">{{ nodeName(nodeId) }}</span>
            <span class="node-host">{{ nodeHost(nodeId) }}</span>
          </div>
          <NodeStateBadge :state="nodeState(nodeId)" />
        </div>
      </div>
    </div>

    <!-- Timeout setting -->
    <div class="timeout-row">
      <div class="timeout-label-wrap">
        <i class="pi pi-clock" style="font-size: var(--text-sm); color: var(--color-text-muted)" />
        <label class="field-label">
          Wait for SYNCED timeout
          <span class="field-label-hint">(seconds)</span>
        </label>
      </div>
      <InputNumber
          v-model="store.waitTimeoutSec"
          :min="30"
          :max="1800"
          :step="30"
          show-buttons
          size="small"
          style="width: 140px"
      />
      <span class="timeout-hint">
        If a node doesn’t reach SYNCED within this time, the operation fails.
      </span>
    </div>

    <!-- Error -->
    <div v-if="startError" class="error-alert">
      <i class="pi pi-times-circle" />
      <span>{{ startError }}</span>
    </div>

    <!-- Actions -->
    <div class="step-actions">
      <Button
          label="Start rolling restart"
          icon="pi pi-sync"
          :loading="starting"
          :disabled="store.nodeOrder.length === 0"
          @click="handleStart"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import Button      from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useSortable } from '@vueuse/integrations/useSortable'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeStateBadge from '@/components/shared/NodeStateBadge.vue'

const store      = useMaintenanceStore()
const sortableEl = ref<HTMLElement | null>(null)
const starting   = ref(false)
const startError = ref<string | null>(null)

const localOrder = ref<number[]>([...store.nodeOrder])

watch(() => store.nodeOrder, (val) => {
  localOrder.value = [...val]
})

const { stop } = useSortable(sortableEl, localOrder, {
  handle: '.drag-handle',
  animation: 150,
  onUpdate: () => store.setNodeOrder([...localOrder.value]),
})
onUnmounted(() => stop())

function nodeName(id: number) {
  return store.nodes.find((n) => n.id === id)?.name ?? `Node #${id}`
}
function nodeHost(id: number) {
  return store.nodes.find((n) => n.id === id)?.host ?? ''
}
function nodeState(id: number) {
  return store.nodes.find((n) => n.id === id)?.wsrep_local_state_comment ?? null
}

async function handleStart() {
  starting.value   = true
  startError.value = null
  try {
    await store.startRollingRestart()
  } catch (err: any) {
    startError.value = err?.response?.data?.detail ?? err.message
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────────── */
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
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
  line-height: 1.6;
}

/* ── Node order section ───────────────────────────────── */
.node-order-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 60px;
}

.node-order-empty {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
  background: var(--color-surface-2);
}

.node-order-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.node-order-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  user-select: none;
  transition:
      background    var(--transition-interactive),
      border-color  var(--transition-interactive),
      box-shadow    var(--transition-interactive);
}
.node-order-item:hover {
  background: var(--color-surface-offset);
  box-shadow: var(--shadow-sm);
}
.drag-handle {
  cursor: grab;
  font-size: var(--text-base);
  color: var(--color-text-faint);
  flex-shrink: 0;
  transition: color var(--transition-interactive);
}
.drag-handle:hover  { color: var(--color-text-muted); }
.drag-handle:active { cursor: grabbing; }

.node-order-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.node-name {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-host {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* ── Timeout row ─────────────────────────────────────── */
.timeout-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.timeout-label-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1 1 auto;
  min-width: 160px;
}
.field-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.field-label-hint {
  color: var(--color-text-muted);
  font-weight: 400;
}
.timeout-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  flex: 1 1 100%;
  margin-top: calc(-1 * var(--space-1));
}

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
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}
</style>
