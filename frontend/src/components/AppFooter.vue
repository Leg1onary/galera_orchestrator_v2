<!-- ТЗ 6.4: WS статус. Цвет = connected/connecting/disconnected -->
<script setup lang="ts">
import type { WsStatus } from '@/stores/ws'

defineProps<{ wsStatus: WsStatus }>()

const labels: Record<WsStatus, string> = {
  connected:    'Live',
  connecting:   'Connecting…',
  reconnecting: 'Reconnecting…',
  disconnected: 'Disconnected',
}
</script>

<template>
  <footer class="app-footer">
    <div class="footer-left">
      <span :class="['ws-indicator', `ws-${wsStatus}`]" aria-live="polite">
        <span class="ws-dot" />
        {{ labels[wsStatus] }}
      </span>
    </div>
    <div class="footer-right">
      <span class="footer-brand">Galera Orchestrator v2</span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  height: var(--footer-height);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border-muted);
  flex-shrink: 0;
}

.footer-left, .footer-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* ── WS indicator ── */
.ws-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  font-weight: 500;
  letter-spacing: 0.04em;
}

.ws-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background var(--transition-normal);
}

/* Connected */
.ws-connected    { color: #22c55e; }
.ws-connected    .ws-dot {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34,197,94,0.7);
  animation: pulse-dot 3s ease-in-out infinite;
}

/* Connecting */
.ws-connecting   { color: var(--color-warning); }
.ws-connecting   .ws-dot {
  background: var(--color-warning);
  animation: pulse-dot 1s ease-in-out infinite;
}

/* Reconnecting */
.ws-reconnecting { color: var(--color-degraded); }
.ws-reconnecting .ws-dot {
  background: var(--color-degraded);
  animation: pulse-dot 0.8s ease-in-out infinite;
}

/* Disconnected */
.ws-disconnected { color: var(--color-error); }
.ws-disconnected .ws-dot {
  background: var(--color-error);
  box-shadow: 0 0 6px rgba(239,68,68,0.6);
}

/* ── Brand ── */
.footer-brand {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-weight: 400;
}

@media (prefers-reduced-motion: reduce) {
  .ws-dot { animation: none !important; }
}
</style>
