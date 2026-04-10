<template>
  <div class="wizard-step step-done">

    <!-- Success -->
    <template v-if="store.operationState === 'success'">
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
      <!-- MAJOR fix: inline style вместо text-error-color -->
      <p class="done-desc" style="color: var(--color-error)">
        {{ store.operationError ?? 'An error occurred.' }}
      </p>
    </template>

    <!-- Cancelled -->
    <template v-else>
      <div class="done-icon done-icon--neutral">
        <i class="pi pi-ban" />
      </div>
      <h2 class="done-title">Recovery cancelled</h2>
      <p class="done-desc">The operation was cancelled after the current step completed.</p>
    </template>

    <div class="done-actions">
      <!-- MINOR fix: reset() только, переход на Step1 через emit('restart') -->
      <Button
          label="Run again"
          icon="pi pi-refresh"
          outlined
          @click="handleRestart"
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
// BLOCKER fix: раздельный импорт
import Button from 'primevue/button'
import { useRecoveryStore } from '@/stores/recovery'

const emit = defineEmits<{
  'go-overview': []
  'restart': []      // MINOR fix: родитель переводит wizard на Step1
}>()
const store = useRecoveryStore()

function handleRestart() {
  store.reset()
  emit('restart')
}
</script>

<style scoped>
.step-done {
  display: flex;
  flex-direction: column;
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
}
.done-icon--success {
  background: color-mix(in oklch, var(--color-success) 15%, transparent);
  color: var(--color-success);
}
.done-icon--error {
  background: color-mix(in oklch, var(--color-error) 15%, transparent);
  color: var(--color-error);
}
.done-icon--neutral {
  background: var(--color-surface-offset);
  color: var(--color-text-muted);
}

.done-title {
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--space-2);
}
.done-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 40ch;
}

/* MAJOR fix: Tailwind убран, заменён на scoped класс */
.done-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-6);
}
</style>