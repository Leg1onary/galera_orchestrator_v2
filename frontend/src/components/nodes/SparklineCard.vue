<!-- src/components/nodes/SparklineCard.vue — stub until charts block -->
<template>
  <div class="sparkline-stub">
    <div class="stub-label">{{ label }}</div>
    <div class="stub-placeholder" />
  </div>
</template>
<script setup lang="ts">
defineProps<{ label: string; data: number[]; color?: string; unit?: string; scale?: number }>()
</script>
<style scoped>
.sparkline-stub {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.stub-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
  margin-bottom: var(--space-2);
}
.stub-placeholder {
  height: 40px;
  background: var(--color-surface-dynamic);
  border-radius: var(--radius-sm);
}
</style>
