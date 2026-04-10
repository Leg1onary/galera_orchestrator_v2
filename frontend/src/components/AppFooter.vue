<script setup lang="ts">
import { useOperationsStore } from '@/stores/operations'
import { computed } from 'vue'

const opsStore = useOperationsStore()

const activeOp = computed(() => opsStore.activeOperation)
const isRunning = computed(() =>
  activeOp.value && ['pending', 'running', 'cancel_requested'].includes(activeOp.value.status)
)
</script>

<template>
  <footer class="app-footer">
    <div class="footer-left">
      <span class="footer-build">Galera Orchestrator v2</span>
    </div>
    <div class="footer-center">
      <template v-if="isRunning && activeOp">
        <span class="footer-op-dot footer-op-dot--running" />
        <span class="footer-op-text">{{ activeOp.type }} &mdash; {{ activeOp.status }}</span>
      </template>
    </div>
    <div class="footer-right">
      <span class="footer-hint text-faint text-xs">v2</span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  height: var(--footer-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  border-top: 1px solid var(--color-border-muted);
  flex-shrink: 0;
  background: var(--color-bg);
  gap: var(--space-4);
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.footer-center {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  flex: 1;
  justify-content: center;
}

.footer-build {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-family: var(--font-mono);
}

.footer-op-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.footer-op-dot--running {
  background: var(--color-primary);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.footer-op-text {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
}
</style>
