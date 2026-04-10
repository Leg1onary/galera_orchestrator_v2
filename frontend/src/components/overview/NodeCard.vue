<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import { nodeAction, testConnection } from '@/api/nodes'
import { useQueryClient } from '@tanstack/vue-query'
import { useOperationsStore } from '@/stores/operations'

// ── Types ──────────────────────────────────────────────────────────────────
interface NodeLive {
  id: number
  name: string
  host: string
  port: number
  wsrep_local_state_comment: string | null
  wsrep_cluster_size: number | null
  wsrep_flow_control_paused: number | null
  wsrep_local_recv_queue: number | null
  wsrep_ready: string | null
  ssh_ok: boolean
  readonly: boolean
}

const props = defineProps<{ node: NodeLive; clusterId: number }>()

const queryClient = useQueryClient()
const opsStore = useOperationsStore()

// Блокируем destructive actions если идёт операция (ТЗ 19.1)
const isLocked = computed(() => {
  const op = opsStore.activeOperation
  return op && ['pending', 'running', 'cancel_requested'].includes(op.status)
})

// ── State color (ТЗ 7.3) ──────────────────────────────────────────────────
const STATE_COLORS: Record<string, string> = {
  SYNCED:    '#22c55e',
  DONOR:     '#38bdf8',
  JOINER:    '#38bdf8',
  DESYNCED:  '#38bdf8',
  OFFLINE:   '#ef4444',
}

const stateColor = computed(() => {
  const n = props.node
  const state = (n.wsrep_local_state_comment ?? '').toUpperCase()

  if (!n.ssh_ok || state === 'OFFLINE')       return '#ef4444'
  if (n.wsrep_ready === 'OFF')                return '#f97316'
  if (state === 'SYNCED' && n.readonly)       return '#eab308'
  return STATE_COLORS[state] ?? '#94a3b8'
})

// ── Actions ────────────────────────────────────────────────────────────────
const DESTRUCTIVE = new Set(['stop', 'restart', 'rejoin-force'])

async function runAction(action: string) {
  if (isLocked.value && DESTRUCTIVE.has(action)) return
  await nodeAction(props.clusterId, props.node.id, action)
  queryClient.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'status'] })
}

async function ping() {
  await testConnection(props.clusterId, props.node.id)
}
</script>

<template>
  <div class="node-card" :style="{ '--state-color': stateColor }">
    <div class="node-header">
      <span class="state-dot" />
      <span class="node-name">{{ node.name }}</span>
      <span class="node-host">{{ node.host }}:{{ node.port }}</span>
    </div>

    <div class="node-metrics">
      <div class="metric">
        <span class="mk">State</span>
        <span class="mv">{{ node.wsrep_local_state_comment ?? '—' }}</span>
      </div>
      <div class="metric">
        <span class="mk">Cluster size</span>
        <span class="mv">{{ node.wsrep_cluster_size ?? '—' }}</span>
      </div>
      <div class="metric">
        <span class="mk">Flow ctrl</span>
        <span class="mv">{{ node.wsrep_flow_control_paused ?? '—' }}</span>
      </div>
      <div class="metric">
        <span class="mk">Recv queue</span>
        <span class="mv">{{ node.wsrep_local_recv_queue ?? '—' }}</span>
      </div>
      <div class="metric">
        <span class="mk">Mode</span>
        <span class="mv">{{ node.readonly ? 'RO' : 'RW' }}</span>
      </div>
    </div>

    <div class="node-actions">
      <Button size="small" text label="Start"   @click="runAction('start')" />
      <Button size="small" text label="Stop"    @click="runAction('stop')"
              severity="danger"  :disabled="!!isLocked" />
      <Button size="small" text label="Restart" @click="runAction('restart')"
              severity="warn"    :disabled="!!isLocked" />
      <Button size="small" text label="Rejoin"  @click="runAction('rejoin-force')"
              severity="warn"    :disabled="!!isLocked" />
      <Button size="small" text label="RO"      @click="runAction('set-readonly')" />
      <Button size="small" text label="RW"      @click="runAction('set-readwrite')" />
      <Button size="small" text label="Ping"    @click="ping()" />
    </div>
  </div>
</template>

<style scoped>
.node-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.node-header { display: flex; align-items: center; gap: var(--space-2); }
.state-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--state-color);
  flex-shrink: 0;
}
.node-name { font-weight: 600; font-size: var(--text-sm); }
.node-host { font-size: var(--text-xs); color: var(--color-text-muted); margin-left: auto; }
.node-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-1) var(--space-3); }
.metric { display: flex; justify-content: space-between; font-size: var(--text-xs); }
.mk { color: var(--color-text-muted); }
.mv { font-variant-numeric: tabular-nums; font-weight: 500; }
.node-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-2);
}
</style>