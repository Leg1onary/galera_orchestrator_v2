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
    <div ref="sortableEl" class="node-order-list mb-4">
      <div
          v-for="nodeId in store.nodeOrder"
          :key="nodeId"
          class="node-order-item"
          :data-id="nodeId"
      >
        <i class="pi pi-bars drag-handle text-muted-color" />
        <div class="node-order-info">
          <span class="font-medium">{{ nodeName(nodeId) }}</span>
          <span class="font-mono text-xs text-muted-color">{{ nodeHost(nodeId) }}</span>
        </div>
        <NodeStateBadge :state="nodeState(nodeId)" />
      </div>
    </div>

    <!-- Timeout setting -->
    <div class="timeout-row mb-4">
      <label class="field-label">
        Wait for SYNCED timeout
        <span class="text-muted-color font-normal">(seconds)</span>
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
      <span class="text-xs text-muted-color">
        If a node doesn't reach SYNCED within this time, the operation fails.
      </span>
    </div>

    <!-- Error from startRollingRestart -->
    <div v-if="startError" class="error-alert mb-4">
      <i class="pi pi-times-circle" />
      {{ startError }}
    </div>

    <div class="flex justify-end">
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
import { ref, onMounted, onUnmounted } from 'vue'
import { Button, InputNumber } from 'primevue'
import { useSortable } from '@vueuse/integrations/useSortable'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeStateBadge from '@/components/shared/NodeStateBadge.vue'

const store = useMaintenanceStore()
const sortableEl = ref<HTMLElement | null>(null)
const starting = ref(false)
const startError = ref<string | null>(null)

// VueUse useSortable — drag-to-reorder без внешней drag library
const { stop } = useSortable(sortableEl, store.nodeOrder, {
  handle: '.drag-handle',
  animation: 150,
  onUpdate: () => {
    // useSortable мутирует массив in-place — store реактивно обновится
  },
})
onUnmounted(() => stop())

function nodeName(id: number) {
  return store.nodes.find((n) => n.node_id === id)?.node_name ?? `Node #${id}`
}
function nodeHost(id: number) {
  return store.nodes.find((n) => n.node_id === id)?.host ?? ''
}
function nodeState(id: number) {
  return store.nodes.find((n) => n.node_id === id)?.wsrep_state ?? 'UNKNOWN'
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
.node-order-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-order-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: default;
  user-select: none;
}
.drag-handle { cursor: grab; font-size: 1rem; }
.drag-handle:active { cursor: grabbing; }
.node-order-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.timeout-row {
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.field-label { font-size: var(--text-sm); font-weight: 500; }
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
</style>