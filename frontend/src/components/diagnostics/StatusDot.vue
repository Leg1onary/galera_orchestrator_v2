<template>
  <span :class="['status-dot-wrap', ok === null ? 'dot-unknown' : ok ? 'dot-ok' : 'dot-fail']">
    <span class="dot" />
    <span class="dot-label">{{ ok === null ? '?' : ok ? 'OK' : 'FAIL' }}</span>
  </span>
</template>

<script setup lang="ts">
defineProps<{ ok: boolean | null }>()
</script>

<style scoped>
.status-dot-wrap {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.03em;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.dot-ok   .dot { background: var(--color-success); }
.dot-fail .dot { background: var(--color-error); }
.dot-unknown .dot { background: var(--color-text-faint); }

.dot-ok    .dot-label { color: var(--color-success); }
.dot-fail  .dot-label { color: var(--color-error); }
.dot-unknown .dot-label { color: var(--color-text-faint); }
</style>
