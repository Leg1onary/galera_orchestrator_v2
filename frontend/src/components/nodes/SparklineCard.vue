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
.sparkline-stub { padding: 0.5rem; background: var(--color-surface-offset); border-radius: var(--radius-md); }
.stub-label { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: 0.25rem; }
.stub-placeholder { height: 40px; background: var(--color-surface-dynamic); border-radius: var(--radius-sm); }
</style>