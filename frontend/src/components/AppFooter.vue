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
    <span :class="['ws-indicator', `ws-${wsStatus}`]" aria-live="polite">
      <span class="ws-dot" />
      {{ labels[wsStatus] }}
    </span>
    <span class="footer-copy">Galera Orchestrator v2</span>
  </footer>
</template>

<style scoped>
.app-footer {
  background: var(--p-surface-section);
  border-top: 1px solid var(--p-content-border-color);
  color: var(--p-text-muted-color);
}

.ws-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ws-connected    .ws-dot { background: var(--p-green-500); }
.ws-connecting   .ws-dot { background: var(--p-yellow-400); animation: pulse 1s infinite; }
.ws-reconnecting .ws-dot { background: var(--p-orange-400); animation: pulse 1s infinite; }
.ws-disconnected .ws-dot { background: var(--p-red-500); }

.ws-connected    { color: var(--p-green-600); }
.ws-connecting   { color: var(--p-yellow-600); }
.ws-reconnecting { color: var(--p-orange-500); }
.ws-disconnected { color: var(--p-red-600); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

@media (prefers-reduced-motion: reduce) {
  .ws-dot { animation: none !important; }
}
</style>