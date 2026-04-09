<!-- ТЗ 6.4: WS статус. Цвет = connected/connecting/disconnected -->
<script setup lang="ts">
import type { WsStatus } from '@/stores/ws'

defineProps<{ wsStatus: WsStatus }>()

const labels: Record<WsStatus, string> = {
  connected:    'Live',
  connecting:   'Connecting…',
  disconnected: 'Disconnected',
}
</script>

<template>
  <footer class="app-footer">
    <span :class="['ws-indicator', `ws-${wsStatus}`]">
      <span class="ws-dot" />
      {{ labels[wsStatus] }}
    </span>
    <span class="footer-copy">Galera Orchestrator v2</span>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 32px;
  padding: 0 1.5rem;
  background: #1a1f2e;
  border-top: 1px solid #2a3040;
  flex-shrink: 0;
  font-size: 0.75rem;
  color: #94a3b8;
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

.ws-connected    .ws-dot { background: #22c55e; }
.ws-connecting   .ws-dot { background: #f59e0b; animation: pulse 1s infinite; }
.ws-disconnected .ws-dot { background: #ef4444; }

.ws-connected    { color: #16a34a; }
.ws-connecting   { color: #d97706; }
.ws-disconnected { color: #dc2626; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
</style>