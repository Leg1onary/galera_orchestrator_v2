<template>
  <div class="placeholder-page">
    <div class="placeholder-content">
      <p class="placeholder-icon" aria-hidden="true">🚧</p>
      <h2 class="placeholder-title">{{ pageTitle }}</h2>
      <p class="placeholder-message">
        This page is not yet implemented. It will be built in a future phase.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// Show the page title from route meta, or derive from path
const pageTitle = computed(() => {
  if (route.meta?.title) return route.meta.title
  const path = route.path.replace('/', '') || 'Overview'
  return path.charAt(0).toUpperCase() + path.slice(1)
})
</script>

<style scoped>
.placeholder-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100dvh - var(--header-height) - 36px - var(--space-12));
  padding: var(--space-8);
}

.placeholder-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  max-width: 400px;
}

.placeholder-icon {
  font-size: 3rem;
  line-height: 1;
}

.placeholder-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
}

.placeholder-message {
  font-size: var(--text-base);
  color: var(--color-text-muted);
}
</style>