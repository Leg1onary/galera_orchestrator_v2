<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 2 — Select bootstrap node</h2>
      <p class="step-desc">
        The selected node will be started with <code>--wsrep-new-cluster</code>.
        All other nodes will rejoin it in Step 3.
      </p>
    </div>

    <!-- Node selection -->
    <div class="node-list">
      <div
          v-for="node in safeReachableNodes"
          :key="node.node_id"
          class="node-option"
          :class="{
          'node-option--selected':    store.selectedBootstrapNodeId === node.node_id,
          'node-option--recommended': node.node_id === store.recommendedNode?.node_id,
        }"
          @click="store.selectedBootstrapNodeId = node.node_id"
      >
        <RadioButton
            :model-value="store.selectedBootstrapNodeId"
            :value="node.node_id"
            :input-id="`node-${node.node_id}`"
        />
        <div class="node-option-info">
          <div class="node-option-title">
            <span class="node-name">{{ node.node_name }}</span>
            <Tag
                v-if="node.node_id === store.recommendedNode?.node_id"
                value="Recommended"
                severity="success"
                style="font-size: var(--text-xs)"
            />
          </div>
          <span style="font-size: var(--text-xs); color: var(--color-text-muted)">
            {{ node.host }}
          </span>
        </div>
        <div class="node-option-meta">
          <span style="font-family: monospace; font-size: var(--text-sm)">
            seqno: {{ node.seqno }}
          </span>
          <Tag
              :value="node.safe_to_bootstrap === 1 ? 'safe' : 'unsafe'"
              :severity="node.safe_to_bootstrap === 1 ? 'success' : 'warning'"
              style="font-size: var(--text-xs)"
          />
        </div>
      </div>
    </div>

    <!-- Force override warning -->
    <div v-if="selectedIsUnsafe" class="force-warning">
      <i class="pi pi-exclamation-triangle" style="color: var(--color-warning)" />
      <div class="force-warning-body">
        <p style="font-size: var(--text-sm); font-weight: 500; color: var(--color-warning)">
          This node has <code>safe_to_bootstrap=0</code>
        </p>
        <p style="font-size: var(--text-xs); color: var(--color-text-muted); margin-top: var(--space-1)">
          Bootstrapping from an unsafe node may cause data loss if another node
          has a higher seqno. Only proceed if you understand the risk.
        </p>
        <div class="force-checkbox">
          <Checkbox v-model="store.bootstrapForce" :binary="true" input-id="force-cb" />
          <label for="force-cb" style="font-size: var(--text-sm); color: var(--color-warning)">
            I understand — force bootstrap anyway
          </label>
        </div>
      </div>
    </div>

    <!-- Bootstrap error -->
    <div v-if="store.bootstrapError" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ store.bootstrapError }}
    </div>

    <div class="step-actions">
      <Button label="Back" icon="pi pi-arrow-left" outlined size="small" @click="emit('back')" />
      <Button
          label="Start bootstrap"
          icon="pi pi-bolt"
          :disabled="!canProceed"
          :loading="store.bootstrapping"
          @click="handleBootstrap"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import Tag from 'primevue/tag'
import Checkbox from 'primevue/checkbox'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ back: []; next: [] }>()
const store = useRecoveryStore()

// Защитный fallback: store.reachableNodes может быть undefined при анмаунте
const safeReachableNodes = computed(() => store.reachableNodes ?? [])

const selectedNode = computed(() =>
    safeReachableNodes.value.find((n) => n.node_id === store.selectedBootstrapNodeId) ?? null
)

const selectedIsUnsafe = computed(() =>
    selectedNode.value !== null &&
    selectedNode.value.safe_to_bootstrap !== null &&
    selectedNode.value.safe_to_bootstrap !== 1
)

const canProceed = computed(() => {
  if (!store.selectedBootstrapNodeId) return false
  if (selectedIsUnsafe.value && !store.bootstrapForce) return false
  return true
})

watch(() => store.selectedBootstrapNodeId, () => {
  store.bootstrapForce = false
})

async function handleBootstrap() {
  await store.startBootstrap()
  if (!store.bootstrapError) {
    emit('next')
  }
}
</script>

<style scoped>
.wizard-step   { display: flex; flex-direction: column; gap: var(--space-4); }
.step-header   { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title    { font-size: var(--text-lg); font-weight: 600; }
.step-desc     { font-size: var(--text-sm); color: var(--color-text-muted); }

.node-list     { display: flex; flex-direction: column; gap: var(--space-2); }
.node-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
      border-color var(--transition-interactive),
      background var(--transition-interactive);
}
.node-option:hover,
.node-option--selected {
  border-color: var(--color-primary);
  background: var(--color-primary-highlight);
}
.node-option--recommended { border-color: var(--color-success); }

.node-option-info  { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.node-option-title { display: flex; align-items: center; gap: var(--space-2); }
.node-name         { font-weight: 500; }
.node-option-meta  { display: flex; flex-direction: column; align-items: flex-end; gap: var(--space-1); }

.force-warning {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-warning) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-warning) 30%, transparent);
  border-radius: var(--radius-md);
}
.force-warning-body { display: flex; flex-direction: column; gap: var(--space-1); }
.force-checkbox     { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-2); }

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

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
