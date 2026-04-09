<template>
  <div class="app-layout">
    <!-- Fixed top header -->
    <AppHeader class="app-layout__header" />

    <div class="app-layout__body">
      <!-- Fixed left sidebar -->
      <AppSidebar class="app-layout__sidebar" />

      <!-- Main content area — all page content renders here -->
      <main class="app-layout__main" id="main-content">
        <RouterView />
      </main>
    </div>

    <!-- Footer — always visible at bottom -->
    <footer class="app-layout__footer">
      <span class="footer-version">
        Galera Orchestrator v{{ appVersion }}
      </span>
      <span class="footer-ws-status">
        <span
            class="footer-ws-dot"
            :style="{ backgroundColor: wsStore.statusColor }"
            :aria-label="'WebSocket: ' + wsStore.statusLabel"
            role="status"
        />
        <span class="footer-ws-label">{{ wsStore.statusLabel }}</span>
      </span>
    </footer>
  </div>
</template>

<script setup>
import { useWsStore } from '@/stores/ws.js'
import { useAuthStore } from '@/stores/auth.js'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'

const wsStore = useWsStore()
const authStore = useAuthStore()

// App version shown in footer — hardcoded for Phase 0,
// Phase 1 will read this from GET /api/settings/system or a config endpoint
const appVersion = '2.0.0'
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  background-color: var(--color-bg);
}

/* Fixed header at top */
.app-layout__header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-height);
  z-index: 100;
}

/* Body: sidebar + main side by side, below header */
.app-layout__body {
  display: flex;
  flex: 1;
  margin-top: var(--header-height);
  /* Reserve space for footer */
  margin-bottom: 36px;
}

/* Fixed left sidebar */
.app-layout__sidebar {
  position: fixed;
  top: var(--header-height);
  left: 0;
  bottom: 36px; /* footer height */
  width: var(--sidebar-width);
  z-index: 90;
  overflow-y: auto;
}

/* Scrollable main content */
.app-layout__main {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-6);
  overflow-y: auto;
  min-height: calc(100dvh - var(--header-height) - 36px);
}

/* Footer bar */
.app-layout__footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  z-index: 100;
}

.footer-version {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}

.footer-ws-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.footer-ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  transition: background-color var(--transition-normal);
}

.footer-ws-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* Responsive: collapse sidebar on narrow screens */
@media (max-width: 768px) {
  .app-layout__sidebar {
    display: none;
  }
  .app-layout__main {
    margin-left: 0;
  }
}
</style>