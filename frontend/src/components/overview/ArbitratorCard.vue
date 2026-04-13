<script setup lang="ts">
import { computed } from 'vue'

interface ArbitratorLive {
  ssh_ok: boolean
  garbd_running: boolean
  ssh_latency_ms: number | null
  last_check_ts: string | null
  state: string
  error: string | null
}

interface Arbitrator {
  id: number
  name: string
  host: string
  ssh_port?: number
  dc_name?: string | null
  live?: ArbitratorLive | null
}

const props = defineProps<{ arbitrator: Arbitrator }>()

const isReachable = computed(() =>
  !!(props.arbitrator.live?.ssh_ok && props.arbitrator.live?.garbd_running)
)
</script>

<template>
  <article class="arb-card anim-fade-in">
    <div class="arb-stripe" :class="isReachable ? 'arb-stripe--ok' : 'arb-stripe--fail'" />
    <div class="arb-body">
      <div class="arb-header">
        <div class="arb-title-group">
          <span class="arb-name">{{ arbitrator.name }}</span>
          <span v-if="arbitrator.dc_name" class="arb-dc">{{ arbitrator.dc_name }}</span>
        </div>
        <div :class="['arb-badge', isReachable ? 'arb-badge--ok' : 'arb-badge--fail']">
          <span class="arb-dot" />
          {{ isReachable ? 'Reachable' : 'Unreachable' }}
        </div>
      </div>
      <div class="arb-host">
        <span>{{ arbitrator.host }}:{{ arbitrator.ssh_port ?? 22 }}</span>
        <span class="arb-tag">arbitrator</span>
      </div>
      <div v-if="arbitrator.live?.ssh_latency_ms != null" class="arb-latency">
        <span class="arb-latency-label">SSH latency</span>
        <span class="arb-latency-val">{{ arbitrator.live.ssh_latency_ms }} ms</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.arb-card {
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.arb-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-sm);
}

.arb-stripe {
  width: 3px;
  flex-shrink: 0;
}

.arb-stripe--ok   { background: var(--color-synced); }
.arb-stripe--fail { background: var(--color-offline); }

.arb-body {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.arb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-2);
}

.arb-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.arb-name {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arb-dc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 500;
}

.arb-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 1px solid transparent;
  flex-shrink: 0;
  white-space: nowrap;
}

.arb-badge--ok   { background: var(--color-synced-dim);  color: var(--color-synced);  border-color: rgba(74,222,128,0.20); }
.arb-badge--fail { background: var(--color-offline-dim); color: var(--color-offline); border-color: rgba(248,113,113,0.20); }

.arb-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.arb-host {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.arb-tag {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-faint);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}

.arb-latency {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.arb-latency-label {
  color: var(--color-text-faint);
}

.arb-latency-val {
  color: var(--color-text-muted);
}
</style>
