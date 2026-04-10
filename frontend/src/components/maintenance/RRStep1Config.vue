<!--
  Конфигурация rolling restart:
  - порядок нод (drag-to-reorder через VueUse useSortable)
  - таймаут ожидания SYNCED
-->
<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 1 — Configure restart order</h2>
      <p class="step-desc">
        Drag nodes to set the restart order. The next node starts only after
        the previous one reaches <strong>SYNCED</strong>.
      </p>
    </div>

    <!-- Drag list -->
    <div ref="sortableEl" class="node-order-list">
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

    <!-- Timeout setting -->
    <div class="timeout-row">
      <label class="field-label">
        Wait for SYNCED timeout
        <span class="field-label-hint">(seconds)</span>
      </label>
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
        If a node doesn't reach SYNCED within this time, the operation fails.
      </span>
    </div>

    <!-- Error -->
    <div v-if="startError" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ startError }}
    </div>

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
import { ref, onMounted, onUnmounted, watch } from 'vue'
// BLOCKER fix: раздельные импорты
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useSortable } from '@vueuse/integrations/useSortable'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeStateBadge from '@/components/shared/NodeStateBadge.vue'

const store = useMaintenanceStore()
const sortableEl = ref<HTMLElement | null>(null)
const starting   = ref(false)
const startError = ref<string | null>(null)

// MAJOR fix: локальная копия чтобы не мутировать Pinia-массив напрямую
const localOrder = ref<number[]>([...store.nodeOrder])

// Sync store → localOrder при внешнем изменении (например reset)
watch(() => store.nodeOrder, (val) => {
  localOrder.value = [...val]
})

// MAJOR fix: инициализация после mount, onUpdate → store.setNodeOrder
const { stop } = useSortable(sortableEl, localOrder, {
  handle: '.drag-handle',
  animation: 150,
  onUpdate: () => {
    store.setNodeOrder([...localOrder.value])
  },
})
onUnmounted(() => stop())

// MAJOR fix: n.id, n.name, n.wsrep_local_state_comment
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
  starting.value = true
  startError.value = null
  try {
    await store.startRollingRestart()
    // store переключает wizardStep → 2
  } catch (err: any) {
    startError.value = err?.response?.data?.detail ?? err.message
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
.wizard-step  { display: flex; flex-direction: column; gap: var(--space-4); }
.step-header  { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title   { font-size: var(--text-lg); font-weight: 600; }
.step-desc    { font-size: var(--text-sm); color: var(--color-text-muted); }

.node-order-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-order-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: default;
  user-select: none;
}
.drag-handle        { cursor: grab; font-size: 1rem; color: var(--color-text-muted); }
.drag-handle:active { cursor: grabbing; }
.node-order-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.node-name { font-weight: 500; }
.node-host { font-family: monospace; font-size: var(--text-xs); color: var(--color-text-muted); }

.timeout-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.field-label      { font-size: var(--text-sm); font-weight: 500; }
.field-label-hint { color: var(--color-text-muted); font-weight: 400; }
.timeout-hint     { font-size: var(--text-xs); color: var(--color-text-muted); }

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