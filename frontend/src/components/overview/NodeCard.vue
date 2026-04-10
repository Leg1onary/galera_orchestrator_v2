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

const nodeState = computed(() => {
  const n = props.node
  const raw = (n.wsrep_local_state_comment ?? '').toUpperCase()
  if (!n.ssh_ok || raw === 'OFFLINE') return 'OFFLINE'
  if (n.wsrep_ready === 'OFF')        return 'NOT_READY'
  if (raw === 'SYNCED' && n.readonly) return 'SYNCED_RO'
  return raw || 'UNKNOWN'
})

const STATE_MAP: Record<string, { label: string; cls: string; cssVar: string }> = {
  SYNCED:     { label: 'Synced',    cls: 'synced',   cssVar: '--color-synced' },
  SYNCED_RO:  { label: 'Synced RO', cls: 'readonly', cssVar: '--color-readonly' },
  DONOR:      { label: 'Donor',     cls: 'donor',    cssVar: '--color-donor' },
  JOINER:     { label: 'Joiner',    cls: 'donor',    cssVar: '--color-donor' },
  DESYNCED:   { label: 'Desynced',  cls: 'donor',    cssVar: '--color-donor' },
  NOT_READY:  { label: 'Not Ready', cls: 'degraded', cssVar: '--color-degraded' },
  OFFLINE:    { label: 'Offline',   cls: 'offline',  cssVar: '--color-offline' },
  UNKNOWN:    { label: 'Unknown',   cls: 'unknown',  cssVar: '--color-text-muted' },
}

const stateInfo = computed(() => STATE_MAP[nodeState.value] ?? STATE_MAP.UNKNOWN)

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
  <article
    class="node-card anim-fade-in"
    :class="'node-card--' + stateInfo.cls"
  >
    <!-- Left state stripe -->
    <div class="nc-stripe" aria-hidden="true" />

    <div class="nc-body">
      <!-- Header row -->
      <div class="nc-header">
        <div class="nc-title-group">
          <span class="nc-name">{{ node.name }}</span>
          <span v-if="node.dc?.name" class="nc-dc">{{ node.dc.name }}</span>
        </div>
        <div :class="['nc-badge', 'nc-badge--' + stateInfo.cls]">
          <span class="nc-dot" />
          {{ stateInfo.label }}
        </div>
      </div>

      <!-- Host row -->
      <div class="nc-host">
        <span class="nc-host-addr">{{ node.host }}:{{ node.port }}</span>
        <span class="nc-mode" :class="node.readonly ? 'nc-mode--ro' : 'nc-mode--rw'">
          {{ node.readonly ? 'RO' : 'RW' }}
        </span>
      </div>

      <!-- Metrics grid -->
      <div class="nc-metrics">
        <div class="nc-metric">
          <span class="nc-mk">cluster size</span>
          <span class="nc-mv">{{ node.wsrep_cluster_size ?? '—' }}</span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">status</span>
          <span class="nc-mv">{{ node.wsrep_cluster_status ?? '—' }}</span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">flow ctrl</span>
          <span
            class="nc-mv"
            :class="(node.wsrep_flow_control_paused ?? 0) > 0 ? 'nc-mv--warn' : ''"
          >
            {{ node.wsrep_flow_control_paused !== null
              ? node.wsrep_flow_control_paused.toFixed(3)
              : '—' }}
          </span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">recv queue</span>
          <span
            class="nc-mv"
            :class="(node.wsrep_local_recv_queue ?? 0) > 0 ? 'nc-mv--warn' : ''"
          >
            {{ node.wsrep_local_recv_queue ?? '—' }}
          </span>
        </div>
      </div>

      <!-- SSH indicator -->
      <div class="nc-ssh" :class="node.ssh_ok ? 'nc-ssh--ok' : 'nc-ssh--fail'">
        <i :class="node.ssh_ok ? 'pi pi-lock' : 'pi pi-lock-open'" />
        <span>SSH {{ node.ssh_ok ? 'OK' : 'FAIL' }}</span>
      </div>

      <!-- Actions -->
      <div class="nc-actions">
        <button
          class="nc-action"
          v-tooltip.top="'Ping'"
          @click.stop="ping"
          aria-label="Ping node"
        >
          <i class="pi pi-wifi" />
        </button>
        <button
          class="nc-action"
          v-tooltip.top="'Restart'"
          :disabled="!!(isLocked)"
          @click.stop="runAction('restart')"
          aria-label="Restart node"
        >
          <i class="pi pi-refresh" />
        </button>
        <button
          class="nc-action nc-action--danger"
          v-tooltip.top="'Stop'"
          :disabled="!!(isLocked)"
          @click.stop="runAction('stop')"
          aria-label="Stop node"
        >
          <i class="pi pi-stop" />
        </button>
        <button
          class="nc-action"
          v-tooltip.top="'Force rejoin'"
          :disabled="!!(isLocked)"
          @click.stop="runAction('rejoin-force')"
          aria-label="Force rejoin"
        >
          <i class="pi pi-sign-in" />
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.node-card {
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
  position: relative;
}

.node-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-md);
}

/* State stripe (left border) */
.nc-stripe {
  width: 3px;
  flex-shrink: 0;
  background: var(--color-text-faint);
  transition: background var(--transition-normal);
}

.node-card--synced   .nc-stripe { background: var(--color-synced); }
.node-card--readonly .nc-stripe { background: var(--color-readonly); }
.node-card--donor    .nc-stripe { background: var(--color-donor); }
.node-card--degraded .nc-stripe { background: var(--color-degraded); }
.node-card--offline  .nc-stripe { background: var(--color-offline); }
.node-card--unknown  .nc-stripe { background: var(--color-text-muted); }

.nc-body {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  min-width: 0;
}

/* Header */
.nc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.nc-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nc-name {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nc-dc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 500;
}

/* Status badge */
.nc-badge {
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

.nc-badge--synced   { background: var(--color-synced-dim);    color: var(--color-synced);   border-color: rgba(74,222,128,0.20); }
.nc-badge--readonly { background: var(--color-readonly-dim);  color: var(--color-readonly); border-color: rgba(251,191,36,0.20); }
.nc-badge--donor    { background: var(--color-donor-dim);     color: var(--color-donor);    border-color: rgba(96,165,250,0.20); }
.nc-badge--degraded { background: var(--color-degraded-dim);  color: var(--color-degraded); border-color: rgba(251,146,60,0.20); }
.nc-badge--offline  { background: var(--color-offline-dim);   color: var(--color-offline);  border-color: rgba(248,113,113,0.20); }
.nc-badge--unknown  { background: rgba(100,116,139,0.10); color: var(--color-text-muted); border-color: rgba(100,116,139,0.20); }

.nc-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* Host row */
.nc-host {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.nc-host-addr {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nc-mode {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  flex-shrink: 0;
}

.nc-mode--rw { background: rgba(74,222,128,0.10); color: var(--color-synced); }
.nc-mode--ro { background: rgba(251,191,36,0.10); color: var(--color-readonly); }

/* Metrics grid */
.nc-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2) var(--space-3);
}

.nc-metric {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nc-mk {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-faint);
  font-weight: 500;
}

.nc-mv {
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.nc-mv--warn { color: var(--color-degraded); }

/* SSH indicator */
.nc-ssh {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 500;
}

.nc-ssh i { font-size: 0.6rem; }
.nc-ssh--ok   { color: var(--color-text-faint); }
.nc-ssh--fail { color: var(--color-offline); }

/* Actions */
.nc-actions {
  display: flex;
  gap: var(--space-1);
  padding-top: var(--space-1);
  border-top: 1px solid var(--color-border-muted);
}

.nc-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  transition: all var(--transition-normal);
  font-size: 0.75rem;
}

.nc-action:hover:not(:disabled) {
  color: var(--color-text);
  background: var(--color-surface-3);
}

.nc-action--danger:hover:not(:disabled) {
  color: var(--color-error);
  background: var(--color-offline-dim);
}

.nc-action:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
</style>
