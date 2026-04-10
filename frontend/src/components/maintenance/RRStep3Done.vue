<template>
  <!-- MINOR fix: добавлен wizard-step для единообразия -->
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
        Failed on node <strong>{{ failedNodeName }}</strong>.
      </p>
      <!-- MAJOR fix: utility классы → scoped CSS -->
      <p v-if="store.rrStatus?.error" class="done-error-detail">
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

    <!-- MAJOR fix: utility классы → scoped CSS, wizardStep → store.resetWizard() -->
    <div class="done-actions">
      <Button label="Close" outlined @click="store.closeWizard()" />
      <Button
          v-if="store.rrStatus?.state !== 'finished'"
          label="Run again"
          icon="pi pi-refresh"
          @click="store.resetWizard()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
// BLOCKER fix: раздельный импорт
import Button from 'primevue/button'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

// MAJOR fix: n.id, n.name
const failedNodeName = computed(() => {
  const id = store.rrStatus?.failed_node_id
  return id
      ? (store.nodes.find((n) => n.id === id)?.name ?? `Node #${id}`)
      : '—'
})
</script>

<style scoped>
.wizard-step { display: flex; flex-direction: column; gap: var(--space-4); }

.step-done {
  align-items: center;
  text-align: center;
  padding: var(--space-8) var(--space-4);
}

.done-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  margin-bottom: var(--space-4);
  flex-shrink: 0;
}
.done-icon--success { background: color-mix(in oklch, var(--color-success) 15%, transparent); color: var(--color-success); }
.done-icon--error   { background: color-mix(in oklch, var(--color-error)   15%, transparent); color: var(--color-error); }
.done-icon--neutral { background: var(--color-surface-offset); color: var(--color-text-muted); }

.done-title { font-size: var(--text-xl); font-weight: 600; }
.done-desc  { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 42ch; }

/* MAJOR fix: вместо text-sm text-error-color mt-1 */
.done-error-detail {
  font-size: var(--text-sm);
  color: var(--color-error);
  margin-top: var(--space-1);
  max-width: 42ch;
}

/* MAJOR fix: вместо flex gap-3 justify-center mt-6 */
.done-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-6);
}
</style>