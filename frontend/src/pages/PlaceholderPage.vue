<script setup lang="ts">
const props = defineProps<{ title?: string }>()
</script>

<template>
  <div class="placeholder-page anim-fade-in">
    <div class="section-title">{{ title ?? 'Coming soon' }}</div>
    <div class="placeholder-body">
      <i class="pi pi-hammer placeholder-icon" />
      <span class="placeholder-text">This page is under construction</span>
    </div>
  </div>
</template>

<style scoped>
.placeholder-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.placeholder-body {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  border-style: dashed;
}

.placeholder-icon {
  font-size: 1rem;
  color: var(--color-text-faint);
}
</style>
