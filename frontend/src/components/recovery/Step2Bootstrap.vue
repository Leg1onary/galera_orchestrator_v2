<template>
  <div class="wizard-step">

    <!-- HEADER -->
    <div class="step-header">
      <h2 class="step-title">Step 2 — Select bootstrap node</h2>
      <p class="step-desc">
        The selected node will be started with
        <code class="inline-code">--wsrep-new-cluster</code>.
        All other nodes will rejoin it in Step 3.
      </p>
    </div>

    <!-- NODE LIST -->
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
          <div class="node-option-header">
            <span class="node-option-name">{{ node.node_name }}</span>
            <span class="node-option-host">{{ node.host }}</span>
          </div>
          <div class="node-option-badges">
            <span
              class="node-stb"
              :class="node.safe_to_bootstrap === 1 ? 'node-stb--safe' : 'node-stb--unsafe'"
            >
              {{ node.safe_to_bootstrap === 1 ? 'safe_to_bootstrap' : 'unsafe' }}
            </span>
            <span
              v-if="node.node_id === store.recommendedNode?.node_id"
              class="node-recommended"
            >
              <i class="pi pi-star-fill" /> Recommended
            </span>
          </div>
        </div>

        <div class="node-option-seqno">
          <span class="seqno-label">seqno</span>
          <span class="seqno-value">{{ node.seqno }}</span>
        </div>
      </div>
    </div>

    <!-- FORCE OVERRIDE WARNING -->
    <div v-if="selectedIsUnsafe" class="force-warning">
      <div class="force-warning-icon"><i class="pi pi-exclamation-triangle" /></div>
      <div class="force-warning-body">
        <p class="force-warning-title">This node has <code class="inline-code">safe_to_bootstrap=0</code></p>
        <p class="force-warning-text">
          Bootstrapping from an unsafe node may cause data loss if another node
          has a higher seqno. Only proceed if you understand the risk.
        </p>
        <label class="force-checkbox">
          <Checkbox v-model="store.bootstrapForce" :binary="true" input-id="force-cb" />
          <span>I understand — force bootstrap anyway</span>
        </label>
      </div>
    </div>

    <!-- BOOTSTRAP ERROR -->
    <div v-if="store.bootstrapError" class="error-alert">
      <i class="pi pi-times-circle" />
      {{ store.bootstrapError }}
    </div>

    <!-- ACTIONS -->
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
import Checkbox from 'primevue/checkbox'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ back: []; next: [] }>()
const store = useRecoveryStore()

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

watch(() => store.selectedBootstrapNodeId, () => { store.bootstrapForce = false })

async function handleBootstrap() {
  await store.startBootstrap()
  if (!store.bootstrapError) emit('next')
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
.inline-code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background: var(--color-surface-offset);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  color: var(--color-primary);
}

/* NODE LIST */
.node-list { display: flex; flex-direction: column; gap: var(--space-2); }

.node-option {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    border-color var(--transition-interactive),
    background var(--transition-interactive),
    box-shadow var(--transition-interactive);
}
.node-option:hover {
  border-color: color-mix(in oklch, var(--color-primary) 50%, transparent);
  background: color-mix(in oklch, var(--color-primary) 5%, var(--color-surface-offset));
}
.node-option--selected {
  border-color: var(--color-primary);
  background: color-mix(in oklch, var(--color-primary) 8%, transparent);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--color-primary) 15%, transparent);
}
.node-option--recommended {
  border-color: color-mix(in oklch, var(--color-success) 50%, transparent);
}
.node-option--selected.node-option--recommended {
  border-color: var(--color-success);
  background: color-mix(in oklch, var(--color-success) 8%, transparent);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--color-success) 15%, transparent);
}

.node-option-info { flex: 1; display: flex; flex-direction: column; gap: var(--space-2); }
.node-option-header { display: flex; align-items: center; gap: var(--space-3); }
.node-option-name { font-size: var(--text-base); font-weight: 600; color: var(--color-text); }
.node-option-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.node-option-badges { display: flex; align-items: center; gap: var(--space-2); }

.node-stb {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.node-stb--safe {
  background: color-mix(in oklch, var(--color-success) 14%, transparent);
  color: var(--color-success);
  border: 1px solid color-mix(in oklch, var(--color-success) 30%, transparent);
}
.node-stb--unsafe {
  background: color-mix(in oklch, var(--color-warning) 14%, transparent);
  color: var(--color-warning);
  border: 1px solid color-mix(in oklch, var(--color-warning) 30%, transparent);
}

.node-recommended {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: color-mix(in oklch, var(--color-success) 14%, transparent);
  color: var(--color-success);
  border: 1px solid color-mix(in oklch, var(--color-success) 30%, transparent);
}
.node-recommended .pi { font-size: 0.6rem; }

.node-option-seqno {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}
.seqno-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-faint);
  font-weight: 600;
}
.seqno-value {
  font-family: var(--font-mono);
  font-size: var(--text-base);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

/* FORCE WARNING */
.force-warning {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: color-mix(in oklch, var(--color-warning) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-warning) 30%, transparent);
  border-radius: var(--radius-md);
}
.force-warning-icon {
  font-size: 1.1rem;
  color: var(--color-warning);
  flex-shrink: 0;
  margin-top: 2px;
}
.force-warning-body { display: flex; flex-direction: column; gap: var(--space-2); }
.force-warning-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-warning);
  margin: 0;
}
.force-warning-text {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
  margin: 0;
}
.force-checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-warning);
  font-weight: 500;
  margin-top: var(--space-1);
}

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

/* ACTIONS */
.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  margin-top: auto;
}
</style>
