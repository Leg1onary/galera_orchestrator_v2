<template>
  <div class="wizard-step step-done">
    <template v-if="store.rrStatus?.state === 'finished'">
      <div class="done-icon done-icon--success">
        <i class="pi pi-check" />
      </div>
      <h2 class="done-title">Rolling restart complete</h2>
      <p class="done-desc">
        All {{ store.nodeOrder.length }} nodes have been restarted successfully
        and returned to SYNCED state.
      </p>
    </template>

    <template v-else-if="store.rrStatus?.state === 'failed'">
      <div class="done-icon done-icon--error">
        <i class="pi pi-times" />
      </div>
      <h2 class="done-title">Rolling restart failed</h2>
      <p class="done-desc">
        Failed on node
        <strong>{{ failedNodeName }}</strong>.
      </p>
      <p v-if="store.rrStatus?.error" class="text-sm text-error-color mt-1">
        {{ store.rrStatus.error }}
      </p>
    </template>

    <template v-else>
      <div class="done-icon done-icon--neutral">
        <i class="pi pi-ban" />
      </div>
      <h2 class="done-title">Rolling restart cancelled</h2>
      <p class="done-desc">
        Cancelled after completing
        {{ store.rrStatus?.completed_node_ids.length ?? 0 }} of
        {{ store.nodeOrder.length }} nodes.
      </p>
    </template>

    <div class="flex gap-3 justify-center mt-6">
      <Button label="Close" outlined @click="store.closeWizard()" />
      <Button
          v-if="store.rrStatus?.state !== 'finished'"
          label="Run again"
          icon="pi pi-refresh"
          @click="store.wizardStep = 1"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button } from 'primevue'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

const failedNodeName = computed(() => {
  const id = store.rrStatus?.failed_node_id
  return id ? (store.nodes.find((n) => n.node_id === id)?.node_name ?? `Node #${id}`) : '—'
})
</script>

<style scoped>
.step-done { display: flex; flex-direction: column; align-items: center; text-align: center; padding: var(--space-8) var(--space-4); }
.done-icon {
  width: 64px; height: 64px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem; margin-bottom: var(--space-4);
}
.done-icon--success { background: color-mix(in oklch, var(--color-success) 15%, transparent); color: var(--color-success); }
.done-icon--error   { background: color-mix(in oklch, var(--color-error)   15%, transparent); color: var(--color-error); }
.done-icon--neutral { background: var(--color-surface-offset); color: var(--color-text-muted); }
.done-title { font-size: var(--text-xl); font-weight: 600; margin-bottom: var(--space-2); }
.done-desc  { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 42ch; }
</style>