<template>
  <header class="header">
    <!-- Left: logo + app name -->
    <div class="header__brand">
      <svg
          class="header__logo"
          width="28"
          height="28"
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
      >
        <rect width="40" height="40" rx="8" fill="#1e2436"/>
        <circle cx="20" cy="10" r="4" fill="#38b2ac"/>
        <circle cx="10" cy="28" r="4" fill="#38b2ac"/>
        <circle cx="30" cy="28" r="4" fill="#38b2ac"/>
        <line x1="20" y1="14" x2="10" y2="24" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
        <line x1="20" y1="14" x2="30" y2="24" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
        <line x1="14" y1="28" x2="26" y2="28" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
      </svg>
      <span class="header__title">Galera Orchestrator</span>
    </div>

    <!-- Centre: contour + cluster selectors — STUB Phase 5 -->
    <div class="header__selectors">
      <div class="selector-stub" title="Contour selector — Phase 5">
        <span class="selector-label">Contour</span>
        <span class="selector-value text-muted">—</span>
      </div>
      <span class="selector-divider" aria-hidden="true">/</span>
      <div class="selector-stub" title="Cluster selector — Phase 5">
        <span class="selector-label">Cluster</span>
        <span class="selector-value text-muted">—</span>
      </div>
      <!-- Cluster status indicator — STUB Phase 1 -->
      <span class="cluster-status-badge cluster-status-badge--unknown" title="Cluster status — Phase 1">
        –
      </span>
    </div>

    <!-- Right: user info + logout -->
    <div class="header__actions">
      <span v-if="authStore.username" class="header__username">
        {{ authStore.username }}
      </span>
      <button
          class="btn-logout"
          :disabled="loggingOut"
          @click="handleLogout"
          aria-label="Log out"
      >
        <span v-if="loggingOut" class="btn-spinner-sm" aria-hidden="true" />
        <span>{{ loggingOut ? 'Logging out…' : 'Logout' }}</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()
const loggingOut = ref(false)

async function handleLogout() {
  loggingOut.value = true
  try {
    await authStore.logout()
    await router.push({ name: 'login' })
  } finally {
    loggingOut.value = false
  }
}
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  height: var(--header-height);
  padding: 0 var(--space-6);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

/* Brand */
.header__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.header__logo {
  flex-shrink: 0;
}

.header__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
}

/* Selectors — centre section */
.header__selectors {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  justify-content: center;
  min-width: 0;
}

.selector-stub {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  background-color: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.selector-label {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.selector-value {
  font-size: var(--text-sm);
  font-weight: 500;
}

.selector-divider {
  color: var(--color-text-faint);
  font-size: var(--text-sm);
}

/* Cluster status badge */
.cluster-status-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full, 9999px);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.cluster-status-badge--unknown {
  background-color: var(--color-surface-3);
  color: var(--color-text-faint);
  border: 1px solid var(--color-border);
}

/* Actions — right section */
.header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.header__username {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background-color: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}

.btn-logout:hover:not(:disabled) {
  border-color: var(--color-error);
  color: #fca5a5;
}

.btn-logout:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner-sm {
  width: 12px;
  height: 12px;
  border: 1.5px solid rgba(255,255,255,0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>