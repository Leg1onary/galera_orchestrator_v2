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
.stat-row { display: flex; justify-content: space-between; padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--color-divider); font-size: var(--text-sm); }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: var(--color-text-muted); }
.stat-value { font-weight: 500; font-family: monospace; }
</style>