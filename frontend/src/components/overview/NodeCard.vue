<script setup lang="ts">
import { computed } from 'vue'
import { nodesApi } from '@/api/nodes'
import type { NodeAction } from '@/api/nodes'
import { useQueryClient } from '@tanstack/vue-query'
import { useOperationsStore } from '@/stores/operations'

interface NodeLive {
  id: number
  name: string
  host: string
  port: number
  dc?: { name: string } | null
  wsrep_local_state_comment: string | null
  wsrep_cluster_status: string | null
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

const isLocked = computed(() => {
  const op = opsStore.activeOperation
  return op && ['pending', 'running', 'cancel_requested'].includes(op.status)
})

// ── State derivation (ТЗ 7.3) ──────────────────────────────────────────────
const nodeState = computed(() => {
  const n = props.node
  const raw = (n.wsrep_local_state_comment ?? '').toUpperCase()
  if (!n.ssh_ok || raw === 'OFFLINE') return 'OFFLINE'
  if (n.wsrep_ready === 'OFF')        return 'NOT_READY'
  if (raw === 'SYNCED' && n.readonly) return 'SYNCED_RO'
  return raw || 'UNKNOWN'
})

const stateConfig = computed(() => {
  const configs: Record<string, { label: string; color: string; dim: string; glowColor: string }> = {
    SYNCED:     { label: 'Synced',    color: '#22c55e', dim: 'rgba(34,197,94,0.12)',   glowColor: 'rgba(34,197,94,0.4)' },
    SYNCED_RO:  { label: 'Synced RO', color: '#eab308', dim: 'rgba(234,179,8,0.12)',   glowColor: 'rgba(234,179,8,0.4)' },
    DONOR:      { label: 'Donor',     color: '#38bdf8', dim: 'rgba(56,189,248,0.12)',  glowColor: 'rgba(56,189,248,0.4)' },
    JOINER:     { label: 'Joiner',    color: '#38bdf8', dim: 'rgba(56,189,248,0.12)',  glowColor: 'rgba(56,189,248,0.4)' },
    DESYNCED:   { label: 'Desynced',  color: '#38bdf8', dim: 'rgba(56,189,248,0.12)',  glowColor: 'rgba(56,189,248,0.4)' },
    NOT_READY:  { label: 'Not Ready', color: '#f97316', dim: 'rgba(249,115,22,0.12)', glowColor: 'rgba(249,115,22,0.4)' },
    OFFLINE:    { label: 'Offline',   color: '#ef4444', dim: 'rgba(239,68,68,0.12)',   glowColor: 'rgba(239,68,68,0.4)' },
    UNKNOWN:    { label: 'Unknown',   color: '#64748b', dim: 'rgba(100,116,139,0.12)', glowColor: 'rgba(100,116,139,0.4)' },
  }
  return configs[nodeState.value] ?? configs.UNKNOWN
})

// ── Actions ────────────────────────────────────────────────────────────────
const DESTRUCTIVE = new Set<NodeAction>(['stop', 'restart', 'rejoin-force'])

async function runAction(action: NodeAction) {
  if (isLocked.value && DESTRUCTIVE.has(action)) return
  await nodesApi.action(props.clusterId, props.node.id, action)
  queryClient.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'status'] })
}

async function ping() {
  await nodesApi.testConnection(props.clusterId, props.node.id)
}
</script>

<template>
  <div
      class="node-card anim-fade-in"
      :style="{ '--state-color': stateConfig.color, '--state-dim': stateConfig.dim, '--state-glow': stateConfig.glowColor }"
  >
    <!-- Header -->
    <div class="nc-header">
      <div class="nc-state-bar" />
      <div class="nc-title">
        <span class="nc-name">{{ node.name }}</span>
        <span v-if="node.dc?.name" class="nc-dc">{{ node.dc.name }}</span>
      </div>
      <div class="nc-state-badge">
        <span class="nc-state-dot" />
        <span class="nc-state-label">{{ stateConfig.label }}</span>
      </div>
    </div>

    <!-- Host -->
    <div class="nc-host">
      <i class="pi pi-server" style="font-size: 0.7rem; opacity: 0.4" />
      <span>{{ node.host }}:{{ node.port }}</span>
      <span class="nc-mode" :class="node.readonly ? 'nc-mode--ro' : 'nc-mode--rw'">
        {{ node.readonly ? 'RO' : 'RW' }}
      </span>
    </div>

    <!-- Metrics grid -->
    <div class="nc-metrics">
      <div class="nc-metric">
        <span class="nc-mk">wsrep_size</span>
        <span class="nc-mv">{{ node.wsrep_cluster_size ?? '—' }}</span>
      </div>
      <div class="nc-metric">
        <span class="nc-mk">cluster_status</span>
        <span class="nc-mv">{{ node.wsrep_cluster_status ?? '—' }}</span>
      </div>
      <div class="nc-metric">
        <span class="nc-mk">flow_ctrl</span>
        <span class="nc-mv" :class="(node.wsrep_flow_control_paused ?? 0) > 0 ? 'nc-mv--warn' : ''">
          {{ node.wsrep_flow_control_paused !== null ? node.wsrep_flow_control_paused.toFixed(3) : '—' }}
        </span>
      </div>
      <div class="nc-metric">
        <span class="nc-mk">recv_queue</span>
        <span class="nc-mv" :class="(node.wsrep_local_recv_queue ?? 0) > 0 ? 'nc-mv--warn' : ''">
          {{ node.wsrep_local_recv_queue ?? '—' }}
        </span>
      </div>
    </div>

    <!-- SSH status -->
    <div class="nc-ssh" :class="node.ssh_ok ? 'nc-ssh--ok' : 'nc-ssh--fail'">
      <i :class="node.ssh_ok ? 'pi pi-check-circle' : 'pi pi-times-circle'" />
      <span>SSH {{ node.ssh_ok ? 'OK' : 'FAIL' }}</span>
    </div>

    <!-- Actions -->
    <div class="nc-actions">
      <button class="nc-btn nc-btn--default" @click="runAction('start')" title="Start">Start</button>
      <button class="nc-btn nc-btn--danger" :disabled="!!isLocked" @click="runAction('stop')" title="Stop">Stop</button>
      <button class="nc-btn nc-btn--warn" :disabled="!!isLocked" @click="runAction('restart')" title="Restart">Restart</button>
      <button class="nc-btn nc-btn--warn" :disabled="!!isLocked" @click="runAction('rejoin-force')" title="Rejoin">Rejoin</button>
      <button class="nc-btn nc-btn--subtle" @click="runAction('set-readonly')" title="Set Read Only">RO</button>
      <button class="nc-btn nc-btn--subtle" @click="runAction('set-readwrite')" title="Set Read Write">RW</button>
      <button class="nc-btn nc-btn--subtle" @click="ping()" title="Ping">Ping</button>
    </div>
  </div>
</template>

<style scoped>
.node-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.node-card:hover {
  border-color: var(--state-color);
  box-shadow: 0 0 20px rgba(from var(--state-color) r g b / 0.08), inset 0 0 0 1px rgba(from var(--state-color) r g b / 0.05);
}

/* ── State bar (top color strip) ── */
.nc-state-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--state-color);
  box-shadow: 0 0 8px var(--state-glow);
  opacity: 0.85;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

/* ── Header ── */
.nc-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-4) var(--space-2);
  padding-top: calc(var(--space-4) + 4px); /* account for state bar */
  position: relative;
}

.nc-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.nc-name {
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nc-dc {
  font-size: var(--text-xs);
  color: var(--color-primary);
  background: var(--color-primary-dim);
  border: 1px solid rgba(45,212,191,0.2);
  border-radius: var(--radius-sm);
  padding: 1px 6px;
  font-weight: 500;
  flex-shrink: 0;
}

/* ── State badge ── */
.nc-state-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: var(--radius-xl);
  background: var(--state-dim);
  border: 1px solid color-mix(in srgb, var(--state-color) 30%, transparent);
  flex-shrink: 0;
}

.nc-state-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--state-color);
  box-shadow: 0 0 6px var(--state-glow);
  animation: pulse-dot 2.5s ease-in-out infinite;
}

.nc-state-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--state-color);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Host ── */
.nc-host {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0 var(--space-4) var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.nc-mode {
  margin-left: auto;
  font-family: var(--font-body);
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 1px 7px;
  border-radius: var(--radius-xl);
  letter-spacing: 0.05em;
}

.nc-mode--rw {
  background: rgba(45,212,191,0.12);
  color: var(--color-primary);
  border: 1px solid rgba(45,212,191,0.25);
}

.nc-mode--ro {
  background: rgba(234,179,8,0.12);
  color: var(--color-readonly);
  border: 1px solid rgba(234,179,8,0.25);
}

/* ── Metrics ── */
.nc-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  padding: 0 var(--space-4) var(--space-3);
  row-gap: var(--space-2);
  column-gap: var(--space-4);
}

.nc-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nc-mk {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-family: var(--font-mono);
}

.nc-mv {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}

.nc-mv--warn { color: var(--color-degraded); }

/* ── SSH status ── */
.nc-ssh {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 500;
  border-top: 1px solid var(--color-border-muted);
}

.nc-ssh--ok   { color: var(--color-synced); }
.nc-ssh--fail { color: var(--color-error); }

/* ── Actions ── */
.nc-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border);
}

.nc-btn {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-body);
  letter-spacing: 0.03em;
}

.nc-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.nc-btn--default {
  background: rgba(45,212,191,0.08);
  color: var(--color-primary);
  border-color: rgba(45,212,191,0.2);
}
.nc-btn--default:hover:not(:disabled) {
  background: rgba(45,212,191,0.15);
  border-color: rgba(45,212,191,0.4);
}

.nc-btn--danger {
  background: rgba(239,68,68,0.08);
  color: var(--color-error);
  border-color: rgba(239,68,68,0.2);
}
.nc-btn--danger:hover:not(:disabled) {
  background: rgba(239,68,68,0.15);
  border-color: rgba(239,68,68,0.4);
}

.nc-btn--warn {
  background: rgba(249,115,22,0.08);
  color: var(--color-degraded);
  border-color: rgba(249,115,22,0.2);
}
.nc-btn--warn:hover:not(:disabled) {
  background: rgba(249,115,22,0.15);
  border-color: rgba(249,115,22,0.4);
}

.nc-btn--subtle {
  background: transparent;
  color: var(--color-text-muted);
  border-color: var(--color-border-muted);
}
.nc-btn--subtle:hover:not(:disabled) {
  background: var(--color-surface-4);
  color: var(--color-text);
  border-color: var(--color-border-hover);
}
</style>
