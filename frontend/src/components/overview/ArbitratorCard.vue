<script setup lang="ts">
// ── Types (ТЗ 7.4) ────────────────────────────────────────────────────────
interface ArbitratorLive {
  id: number
  name: string
  host: string
  state: 'online' | 'degraded' | 'offline'
  ssh_ok: boolean
  garbd_running: boolean
  latency_ssh_ms: number | null
}

defineProps<{ arbitrator: ArbitratorLive }>()

// Цвета состояний арбитратора (ТЗ 7.4)
// Согласованы с NodeCard: online=SYNCED, degraded=warn, offline=OFFLINE
const STATE_COLORS: Record<ArbitratorLive['state'], string> = {
  online:   '#22c55e',
  degraded: '#f97316',
  offline:  '#ef4444',
}
</script>

<template>
  <div class="arb-card">
    <div class="arb-header">
      <span
          class="state-dot"
          :style="{ background: STATE_COLORS[arbitrator.state] ?? '#94a3b8' }"
      />
      <span class="arb-name">{{ arbitrator.name }}</span>
      <span class="arb-host">{{ arbitrator.host }}</span>
    </div>
    <div class="arb-metrics">
      <div class="metric">
        <span class="mk">SSH</span>
        <span class="mv">
          <i :class="arbitrator.ssh_ok ? 'pi pi-check' : 'pi pi-times'" />
        </span>
      </div>
      <div class="metric">
        <span class="mk">garbd</span>
        <span class="mv">{{ arbitrator.garbd_running ? 'running' : 'stopped' }}</span>
      </div>
      <div class="metric">
        <span class="mk">Latency</span>
        <span class="mv">
          {{ arbitrator.latency_ssh_ms != null ? `${arbitrator.latency_ssh_ms}ms` : '—' }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.arb-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.arb-header { display: flex; align-items: center; gap: var(--space-2); }
.state-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.arb-name { font-weight: 600; font-size: var(--text-sm); }
.arb-host { font-size: var(--text-xs); color: var(--color-text-muted); margin-left: auto; }
.arb-metrics { display: flex; gap: var(--space-4); }
.metric { display: flex; flex-direction: column; gap: var(--space-1); }
.mk {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}
.mv { font-size: var(--text-sm); font-weight: 600; }
</style>