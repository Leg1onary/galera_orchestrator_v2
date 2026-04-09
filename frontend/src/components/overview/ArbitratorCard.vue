<!-- src/components/overview/ArbitratorCard.vue -->
<script setup lang="ts">
defineProps<{ arbitrator: any }>()
const stateColors = { online: '#22c55e', degraded: '#f59e0b', offline: '#ef4444' }
</script>
<template>
  <div class="arb-card">
    <div class="arb-header">
      <span class="state-dot" :style="{ background: stateColors[arbitrator.state as keyof typeof stateColors] ?? '#94a3b8' }" />
      <span class="arb-name">{{ arbitrator.name }}</span>
      <span class="arb-host">{{ arbitrator.host }}</span>
    </div>
    <div class="arb-metrics">
      <div class="metric"><span class="mk">SSH</span><span class="mv">{{ arbitrator.ssh_ok ? '✓' : '✗' }}</span></div>
      <div class="metric"><span class="mk">garbd</span><span class="mv">{{ arbitrator.garbd_running ? 'running' : 'stopped' }}</span></div>
      <div class="metric"><span class="mk">Latency</span><span class="mv">{{ arbitrator.latency_ssh_ms ?? '—' }}ms</span></div>
    </div>
  </div>
</template>
<style scoped>
.arb-card { background: var(--surface-card); border: 1px solid var(--surface-border); border-radius: 8px; padding: 0.875rem; display: flex; flex-direction: column; gap: 0.625rem; }
.arb-header { display: flex; align-items: center; gap: 0.5rem; }
.state-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.arb-name { font-weight: 600; font-size: 0.875rem; }
.arb-host { font-size: 0.72rem; color: var(--text-color-secondary); margin-left: auto; }
.arb-metrics { display: flex; gap: 1rem; }
.metric { display: flex; flex-direction: column; gap: 2px; }
.mk { font-size: 0.68rem; text-transform: uppercase; color: var(--text-color-secondary); }
.mv { font-size: 0.82rem; font-weight: 600; }
</style>