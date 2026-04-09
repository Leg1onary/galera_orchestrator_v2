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
    <div class="node-list mb-4">
      <div
          v-for="node in store.reachableNodes"
          :key="node.node_id"
          class="node-option"
          :class="{
          'node-option--selected': store.selectedBootstrapNodeId === node.node_id,
          'node-option--recommended': node.node_id === store.recommendedNode?.node_id,
        }"
          @click="store.selectedBootstrapNodeId = node.node_id"
      >
        <RadioButton
            :model-value="store.selectedBootstrapNodeId"
            :value="node.node_id"
            :input-id="`node-${node.node_id}`"
            @update:model-value="store.selectedBootstrapNodeId = node.node_id"
        />
        <div class="node-option-info">
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ node.node_name }}</span>
            <Tag
                v-if="node.node_id === store.recommendedNode?.node_id"
                value="Recommended"
                severity="success"
                class="text-xs"
            />
          </div>
          <span class="text-xs text-muted-color">{{ node.host }}</span>
        </div>
        <div class="node-option-meta">
          <span class="font-mono text-sm">seqno: {{ node.seqno }}</span>
          <Tag
              :value="node.safe_to_bootstrap === 1 ? 'safe' : 'unsafe'"
              :severity="node.safe_to_bootstrap === 1 ? 'success' : 'warn'"
              class="text-xs"
          />
        </div>
      </div>
    </div>

    <!-- Force override warning -->
    <div v-if="selectedIsUnsafe" class="force-warning mb-4">
      <i class="pi pi-exclamation-triangle" style="color: var(--color-warning)" />
      <div>
        <p class="text-sm font-medium" style="color: var(--color-warning)">
          This node has <code>safe_to_bootstrap=0</code>
        </p>
        <p class="text-xs text-muted-color mt-0.5">
          Bootstrapping from an unsafe node may cause data loss if another node
          has a higher seqno. Only proceed if you understand the risk.
        </p>
        <div class="flex items-center gap-2 mt-2">
          <Checkbox v-model="store.bootstrapForce" :binary="true" input-id="force-cb" />
          <label for="force-cb" class="text-sm" style="color: var(--color-warning)">
            I understand — force bootstrap anyway
          </label>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="store.bootstrapError" class="error-alert mb-4">
      <i class="pi pi-times-circle" />
      {{ store.bootstrapError }}
    </div>

    <div class="flex justify-between">
      <Button label="Back" icon="pi pi-arrow-left" outlined size="small" @click="emit('back')" />
      <Button
          label="Start bootstrap"
          icon="pi pi-bolt"
          :disabled="!canProceed"
          :loading="store.bootstrapping"
          @click="store.startBootstrap()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button, RadioButton, Tag, Checkbox } from 'primevue'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ back: [] }>()
const store = useRecoveryStore()

const selectedNode = computed(() =>
    store.reachableNodes.find((n) => n.node_id === store.selectedBootstrapNodeId) ?? null
)

const selectedIsUnsafe = computed(() =>
    selectedNode.value?.safe_to_bootstrap === 0
)

const canProceed = computed(() => {
  if (!store.selectedBootstrapNodeId) return false
  if (selectedIsUnsafe.value && !store.bootstrapForce) return false
  return true
})
</script>

<style scoped>
.node-list { display: flex; flex-direction: column; gap: var(--space-2); }
.node-option {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-interactive), background var(--transition-interactive);
}
.node-option:hover { border-color: var(--color-primary); background: var(--color-primary-highlight); }
.node-option--selected { border-color: var(--color-primary); background: var(--color-primary-highlight); }
.node-option--recommended { border-color: var(--color-success); }
.node-option-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.node-option-meta { display: flex; flex-direction: column; align-items: flex-end; gap: var(--space-1); }
.force-warning {
  display: flex; gap: var(--space-3); padding: var(--space-3) var(--space-4);
  background: color-mix(in oklch, var(--color-warning) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-warning) 30%, transparent);
  border-radius: var(--radius-md);
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