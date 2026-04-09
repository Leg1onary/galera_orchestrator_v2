<template>
  <div class="wizard-step step-done">
    <!-- Success -->
    <template v-if="store.operationState === 'finished'">
      <div class="done-icon done-icon--success">
        <i class="pi pi-check" />
      </div>
      <h2 class="done-title">Recovery complete</h2>
      <p class="done-desc">
        The cluster has been bootstrapped and all reachable nodes have been
        instructed to rejoin. Check the Overview page to confirm node states.
      </p>
    </template>

    <!-- Failed -->
    <template v-else-if="store.operationState === 'failed'">
      <div class="done-icon done-icon--error">
        <i class="pi pi-times" />
      </div>
      <h2 class="done-title">Recovery failed</h2>
      <p class="done-desc text-error-color">{{ store.operationError ?? 'An error occurred.' }}</p>
    </template>

    <!-- Cancelled -->
    <template v-else>
      <div class="done-icon done-icon--neutral">
        <i class="pi pi-ban" />
      </div>
      <h2 class="done-title">Recovery cancelled</h2>
      <p class="done-desc">The operation was cancelled after the current step completed.</p>
    </template>

    <div class="flex gap-3 justify-center mt-6">
      <Button
          label="Run again"
          icon="pi pi-refresh"
          outlined
          @click="store.reset(); store.scan()"
      />
      <Button
          label="Go to Overview"
          icon="pi pi-home"
          @click="emit('go-overview')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from 'primevue'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{ 'go-overview': [] }>()
const store = useRecoveryStore()
</script>

<style scoped>
.step-done { display: flex; flex-direction: column; align-items: center; text-align: center; padding: var(--space-8) var(--space-4); }
.done-icon {
  width: 64px; height: 64px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem;
  margin-bottom: var(--space-4);
}
.done-icon--success { background: color-mix(in oklch, var(--color-success) 15%, transparent); color: var(--color-success); }
.done-icon--error   { background: color-mix(in oklch, var(--color-error)   15%, transparent); color: var(--color-error); }
.done-icon--neutral { background: var(--color-surface-offset); color: var(--color-text-muted); }
.done-title { font-size: var(--text-xl); font-weight: 600; margin-bottom: var(--space-2); }
.done-desc  { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 40ch; }
</style>