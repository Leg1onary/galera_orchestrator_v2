<!--
  Step 3 — Done / Failed / Cancelled.
-->
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
        Failed on node <strong>{{ failedNodeName }}</strong>.
      </p>
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
        {{ store.rrStatus?.completed_node_ids?.length ?? 0 }} of
        {{ store.nodeOrder.length }} nodes.
      </p>
    </template>

    <div class="done-actions">
      <Button label="Close" outlined @click="store.closeWizard()" />
      <!-- Run again available in all non-pending outcomes -->
      <Button
          label="Run again"
          icon="pi pi-refresh"
          @click="store.resetWizard()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import { useMaintenanceStore } from '@/stores/maintenance'

const store = useMaintenanceStore()

const failedNodeName = computed(() => {
  const id = store.rrStatus?.failed_node_id
  return id
      ? (store.nodes.find((n) => n.id === id)?.name ?? `Node #${id}`)
      : '—'
})
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────────── */
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.step-done {
  align-items: center;
  text-align: center;
  padding: var(--space-6) var(--space-4);
}

/* ── Result icon ─────────────────────────────────────── */
.done-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  flex-shrink: 0;
  margin-bottom: var(--space-2);
}
.done-icon--success {
  background: color-mix(in oklch, var(--color-success) 14%, transparent);
  color: var(--color-success);
  box-shadow: 0 0 0 6px color-mix(in oklch, var(--color-success) 8%, transparent);
}
.done-icon--error {
  background: color-mix(in oklch, var(--color-error) 14%, transparent);
  color: var(--color-error);
  box-shadow: 0 0 0 6px color-mix(in oklch, var(--color-error) 8%, transparent);
}
.done-icon--neutral {
  background: var(--color-surface-offset);
  color: var(--color-text-muted);
  box-shadow: 0 0 0 6px var(--color-surface-offset-2);
}

/* ── Text ────────────────────────────────────────────── */
.done-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
}
.done-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 40ch;
  line-height: 1.55;
}
.done-error-detail {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-error);
  background: color-mix(in oklch, var(--color-error) 6%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 20%, transparent);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  max-width: 44ch;
}

/* ── Actions ─────────────────────────────────────────── */
.done-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
  width: 100%;
}
</style>
