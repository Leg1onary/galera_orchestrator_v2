<template>
  <div class="not-found">
    <div class="not-found__content">
      <p class="not-found__code">404</p>
      <h1 class="not-found__title">Page not found</h1>
      <p class="not-found__message">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <RouterLink to="/" class="not-found__home-link">
        ← Back to Overview
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
// Static page — no data dependencies
</script>

<style scoped>
.not-found {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg);
  padding: var(--space-4);
}

.not-found__content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.not-found__code {
  font-size: 6rem;
  font-weight: 700;
  color: var(--color-border);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.not-found__title {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-text);
}

.not-found__message {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  max-width: 40ch;
}

.not-found__home-link {
  display: inline-flex;
  align-items: center;
  padding: var(--space-3) var(--space-6);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: border-color var(--transition-interactive),
  background-color var(--transition-interactive);
}

.not-found__home-link:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-highlight);
}
</style>