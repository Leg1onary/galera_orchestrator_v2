<template>
  <div class="wizard-step step-done">

    <!-- SUCCESS -->
    <template v-if="store.operationState === 'success'">
      <div class="done-icon-wrap done-icon-wrap--success">
        <i class="pi pi-check" />
      </div>
      <div class="done-text">
        <h2 class="done-title">Recovery complete</h2>
        <p class="done-desc">
          The cluster has been bootstrapped and all reachable nodes have been
          instructed to rejoin. Check the Overview page to confirm node states.
        </p>
      </div>
      <div class="done-stats">
        <div class="done-stat">
          <span class="done-stat-icon done-stat-icon--success"><i class="pi pi-server" /></span>
          <div>
            <span class="done-stat-label">Bootstrap node</span>
            <span class="done-stat-value">{{ bootstrapNodeName }}</span>
          </div>
        </div>
        <div class="done-stat">
          <span class="done-stat-icon done-stat-icon--primary"><i class="pi pi-sync" /></span>
          <div>
            <span class="done-stat-label">Nodes rejoined</span>
            <span class="done-stat-value">{{ store.nodesNeedingRejoin?.length ?? 0 }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- FAILED -->
    <template v-else-if="store.operationState === 'failed'">
      <div class="done-icon-wrap done-icon-wrap--error">
        <i class="pi pi-times" />
      </div>
      <div class="done-text">
        <h2 class="done-title">Recovery failed</h2>
        <p class="done-desc done-desc--error">
          {{ store.operationError ?? 'An error occurred during recovery.' }}
        </p>
      </div>
    </template>

    <!-- CANCELLED -->
    <template v-else>
      <div class="done-icon-wrap done-icon-wrap--neutral">
        <i class="pi pi-ban" />
      </div>
      <div class="done-text">
        <h2 class="done-title">Recovery cancelled</h2>
        <p class="done-desc">The operation was cancelled after the current step completed.</p>
      </div>
    </template>

    <!-- ACTIONS -->
    <div class="done-actions">
      <Button label="Run again" icon="pi pi-refresh" outlined @click="handleRestart" />
      <Button label="Go to Overview" icon="pi pi-home" @click="emit('go-overview')" />
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ 'go-overview': [] }>()
const store = useRecoveryStore()

// Resolve bootstrap node name from clusterStatus by selectedBootstrapNodeId
const bootstrapNodeName = computed(() => {
    if (!store.selectedBootstrapNodeId || !store.clusterStatus?.nodes) return '—'
    const node = (store.clusterStatus.nodes as any[]).find(
        (n: any) => n.id === store.selectedBootstrapNodeId
    )
    return node?.name ?? '—'
})

function handleRestart() {
    store.reset()
    // store.reset() sets step.value = 1, no need for extra emit
}
</script>

<style scoped>
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  height: 100%;
}

.step-done {
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-8) var(--space-6);
}

/* ICON */
.done-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  position: relative;
  flex-shrink: 0;
}
.done-icon-wrap--success {
  background: color-mix(in oklch, var(--color-success) 15%, transparent);
  color: var(--color-success);
  box-shadow: 0 0 0 8px color-mix(in oklch, var(--color-success) 8%, transparent);
}
.done-icon-wrap--error {
  background: color-mix(in oklch, var(--color-error) 15%, transparent);
  color: var(--color-error);
  box-shadow: 0 0 0 8px color-mix(in oklch, var(--color-error) 8%, transparent);
}
.done-icon-wrap--neutral {
  background: var(--color-surface-offset);
  color: var(--color-text-muted);
  box-shadow: 0 0 0 8px var(--color-surface-dynamic);
}

/* TEXT */
.done-text { display: flex; flex-direction: column; gap: var(--space-2); }
.done-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}
.done-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 44ch;
  line-height: 1.6;
  margin: 0 auto;
}
.done-desc--error { color: var(--color-error); }

/* STATS (success only) */
.done-stats {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
  flex-wrap: wrap;
}
.done-stat {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-width: 160px;
  text-align: left;
}
.done-stat-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}
.done-stat-icon--success {
  background: color-mix(in oklch, var(--color-success) 15%, transparent);
  color: var(--color-success);
}
.done-stat-icon--primary {
  background: color-mix(in oklch, var(--color-primary) 15%, transparent);
  color: var(--color-primary);
}
.done-stat > div { display: flex; flex-direction: column; gap: 2px; }
.done-stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-faint);
  font-weight: 600;
}
.done-stat-value {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
}

/* ACTIONS */
.done-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: auto;
}
</style>
