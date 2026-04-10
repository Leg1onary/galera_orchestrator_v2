<template>
  <div class="notfound-page">
    <div class="notfound-card anim-fade-in">
      <div class="notfound-code">404</div>
      <h1 class="notfound-title">Page not found</h1>
      <p class="notfound-sub">The page you’re looking for doesn’t exist or has been moved.</p>
      <RouterLink to="/" class="notfound-link">
        <i class="pi pi-arrow-left" />
        Back to dashboard
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.notfound-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: var(--space-4);
}

.notfound-card {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.notfound-code {
  font-size: 6rem;
  font-weight: 800;
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  letter-spacing: -0.04em;
  line-height: 1;
}

.notfound-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.notfound-sub {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 36ch;
}

.notfound-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-primary);
  padding: var(--space-2) var(--space-4);
  border: 1px solid rgba(45,212,191,0.28);
  border-radius: var(--radius-md);
  background: var(--color-primary-dim);
  transition: all var(--transition-normal);
  text-decoration: none;
  margin-top: var(--space-2);
}

.notfound-link:hover {
  background: rgba(45,212,191,0.16);
  border-color: rgba(45,212,191,0.48);
}
</style>
