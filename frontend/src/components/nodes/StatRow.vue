<template>
  <div class="stat-row">
    <span class="stat-label">{{ label }}</span>
    <span class="stat-value">{{ value ?? '—' }}</span>
  </div>
</template>
<script setup lang="ts">
defineProps<{ label: string; value?: string | number | null }>()
</script>
<style scoped>
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--color-divider);
  font-size: var(--text-sm);
  gap: var(--space-4);
  min-height: 36px;
}
.stat-row:last-child { border-bottom: none; }
.stat-label {
  color: var(--color-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}
.stat-value {
  font-weight: 500;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-text);
  text-align: right;
  word-break: break-all;
}
</style>
