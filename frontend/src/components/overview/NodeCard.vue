<script setup lang="ts">
import { computed, ref } from 'vue'
import { nodesApi } from '@/api/nodes'
import type { NodeAction } from '@/api/nodes'
import { useQueryClient } from '@tanstack/vue-query'
import { useOperationsStore } from '@/stores/operations'
import { useConfirm } from 'primevue/useconfirm'

interface NodeLive {
  id: number
  name: string
  host: string
  port: number
  dc?: { name: string } | null
  wsrep_local_state_comment: string | null | undefined
  wsrep_cluster_status: string | null | undefined
  wsrep_cluster_size: number | null | undefined
  wsrep_flow_control_paused: number | null | undefined
  wsrep_local_recv_queue: number | null | undefined
  wsrep_ready: string | null | undefined
  ssh_ok: boolean
  readonly: boolean
}

const props    = defineProps<{ node: NodeLive; clusterId: number }>()
const qc       = useQueryClient()
const opsStore = useOperationsStore()
const confirm  = useConfirm()

const actionLoading = ref<NodeAction | null>(null)
const actionsOpen   = ref(false)

const isLocked = computed(() => {
  const op = opsStore.activeOperation
  return op && ['pending', 'running', 'cancel_requested'].includes(op.status)
})

const nodeState = computed(() => {
  const n   = props.node
  const raw = (n.wsrep_local_state_comment ?? '').toUpperCase()
  if (!n.ssh_ok || raw === 'OFFLINE') return 'OFFLINE'
  if (n.wsrep_ready === 'OFF')        return 'NOT_READY'
  if (raw === 'SYNCED' && n.readonly) return 'SYNCED_RO'
  return raw || 'UNKNOWN'
})

const STATE_MAP: Record<string, { label: string; cls: string; severity: string }> = {
  SYNCED:    { label: 'Synced',    cls: 'synced',   severity: 'success'   },
  SYNCED_RO: { label: 'Synced RO', cls: 'readonly', severity: 'warn'      },
  DONOR:     { label: 'Donor',     cls: 'donor',    severity: 'info'      },
  JOINER:    { label: 'Joiner',    cls: 'donor',    severity: 'info'      },
  DESYNCED:  { label: 'Desynced',  cls: 'donor',    severity: 'info'      },
  NOT_READY: { label: 'Not Ready', cls: 'degraded', severity: 'warn'      },
  OFFLINE:   { label: 'Offline',   cls: 'offline',  severity: 'danger'    },
  UNKNOWN:   { label: 'Unknown',   cls: 'unknown',  severity: 'secondary' },
}

const stateInfo = computed(() => STATE_MAP[nodeState.value] ?? STATE_MAP.UNKNOWN)

const flowControlDisplay = computed(() => {
  const v = props.node.wsrep_flow_control_paused
  if (v == null) return '\u2014'
  return v.toFixed(3)
})

const recvQueueDisplay = computed(() => {
  const v = props.node.wsrep_local_recv_queue
  if (v == null) return '\u2014'
  return String(v)
})

const recvQueueWarn = computed(() => (props.node.wsrep_local_recv_queue ?? 0) > 0)
const flowWarn      = computed(() => (props.node.wsrep_flow_control_paused ?? 0) > 0)

async function execAction(action: NodeAction) {
  actionLoading.value = action
  try {
    await nodesApi.action(props.clusterId, props.node.id, action)
    qc.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'status'] })
  } finally {
    actionLoading.value = null
  }
}

function ping() { execAction('ping' as NodeAction) }

function confirmDestructive(action: NodeAction, label: string) {
  if (isLocked.value) return
  actionsOpen.value = false
  confirm.require({
    message:     `Run "${label}" on node ${props.node.name}?`,
    header:      'Confirm action',
    icon:        'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: label,
    acceptClass: 'p-button-danger',
    accept:      () => execAction(action),
  })
}
</script>

<template>
  <article class="node-card" :class="'node-card--' + stateInfo.cls">
    <!-- State stripe with glow -->
    <div class="nc-stripe" aria-hidden="true" />

    <div class="nc-body">
      <!-- ── HEADER ───────────────────────────────────────────── -->
      <div class="nc-header">
        <div class="nc-title-group">
          <span class="nc-name">{{ node.name }}</span>
          <span v-if="node.dc?.name" class="nc-dc">{{ node.dc.name }}</span>
        </div>
        <Tag
          :value="stateInfo.label"
          :severity="stateInfo.severity"
          class="nc-state-tag"
        />
      </div>

      <!-- ── HOST + MODE ──────────────────────────────────── -->
      <div class="nc-host-row">
        <i class="pi pi-server nc-host-icon" />
        <span class="nc-host-addr">{{ node.host }}:{{ node.port }}</span>
        <span class="nc-mode-badge" :class="node.readonly ? 'mode-ro' : 'mode-rw'">
          {{ node.readonly ? 'RO' : 'RW' }}
        </span>
      </div>

      <!-- ── METRICS GRID ─────────────────────────────────── -->
      <div class="nc-metrics">
        <div class="nc-metric">
          <span class="nc-mk">Cluster Size</span>
          <span class="nc-mv">{{ node.wsrep_cluster_size ?? '\u2014' }}</span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">Component</span>
          <span class="nc-mv nc-mv--mono">{{ node.wsrep_cluster_status ?? '\u2014' }}</span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">Flow Ctrl</span>
          <span class="nc-mv nc-mv--mono" :class="flowWarn ? 'nc-mv--warn' : ''">
            {{ flowControlDisplay }}
          </span>
        </div>
        <div class="nc-metric">
          <span class="nc-mk">Recv Queue</span>
          <span class="nc-mv nc-mv--mono" :class="recvQueueWarn ? 'nc-mv--warn' : ''">
            {{ recvQueueDisplay }}
          </span>
        </div>
      </div>

      <!-- ── SSH + SPACER ──────────────────────────────────── -->
      <div class="nc-ssh" :class="node.ssh_ok ? 'nc-ssh--ok' : 'nc-ssh--fail'">
        <i :class="node.ssh_ok ? 'pi pi-lock' : 'pi pi-lock-open'" />
        <span>SSH {{ node.ssh_ok ? 'OK' : 'FAIL' }}</span>
      </div>

      <!-- ── ACTION BAR ───────────────────────────────────── -->
      <div class="nc-actions">
        <Button
          class="nc-action-ping"
          icon="pi pi-wifi"
          label="Ping"
          size="small"
          :loading="actionLoading === 'ping'"
          :disabled="!!isLocked"
          v-tooltip.top="'Check node reachability'"
          @click.stop="ping"
        />
        <Button
          v-tooltip.top="'Restart MySQL'"
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          class="nc-action-icon"
          :loading="actionLoading === 'restart'"
          :disabled="!!isLocked"
          aria-label="Restart"
          @click.stop="confirmDestructive('restart', 'Restart')"
        />
        <Button
          v-tooltip.top="'Stop MySQL'"
          icon="pi pi-stop-circle"
          text
          rounded
          size="small"
          class="nc-action-icon nc-action-danger"
          :loading="actionLoading === 'stop'"
          :disabled="!!isLocked"
          aria-label="Stop"
          @click.stop="confirmDestructive('stop', 'Stop')"
        />
        <Button
          v-tooltip.top="'Force Rejoin (wsrep_sst)'"
          icon="pi pi-replay"
          text
          rounded
          size="small"
          class="nc-action-icon nc-action-danger"
          :loading="actionLoading === 'rejoin-force'"
          :disabled="!!isLocked"
          aria-label="Force Rejoin"
          @click.stop="confirmDestructive('rejoin-force', 'Force Rejoin')"
        />
      </div>
    </div>
  </article>
</template>

<style scoped>
/* ═══════════════════════════════════════
   CARD BASE
═══════════════════════════════════════ */
.node-card {
  position: relative;
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition:
    box-shadow 200ms ease,
    border-color 200ms ease,
    transform 200ms ease;
}
.node-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-1px);
}

/* ═══════════════════════════════════════
   STATE STRIPE + GLOW
═══════════════════════════════════════ */
.nc-stripe {
  width: 4px;
  flex-shrink: 0;
  background: var(--node-stripe, var(--color-border));
  box-shadow: 0 0 12px 2px var(--node-glow, transparent);
  transition: box-shadow 300ms ease;
}

.node-card--synced   { --node-stripe: var(--color-synced);   --node-glow: color-mix(in oklch, var(--color-synced) 50%, transparent); }
.node-card--readonly { --node-stripe: var(--color-readonly); --node-glow: color-mix(in oklch, var(--color-readonly) 45%, transparent); }
.node-card--donor    { --node-stripe: var(--color-donor);    --node-glow: color-mix(in oklch, var(--color-donor) 45%, transparent); }
.node-card--degraded { --node-stripe: var(--color-degraded); --node-glow: color-mix(in oklch, var(--color-degraded) 45%, transparent); }
.node-card--offline  { --node-stripe: var(--color-offline);  --node-glow: color-mix(in oklch, var(--color-offline) 50%, transparent); }
.node-card--unknown  { --node-stripe: var(--color-text-faint); }

/* ═══════════════════════════════════════
   BODY
═══════════════════════════════════════ */
.nc-body {
  flex: 1;
  min-width: 0;
  /* увеличены внутренние отступы */
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ═══════════════════════════════════════
   HEADER
═══════════════════════════════════════ */
.nc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}
.nc-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.nc-name {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}
.nc-dc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}
.nc-state-tag {
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  flex-shrink: 0;
}

/* ═══════════════════════════════════════
   HOST ROW
═══════════════════════════════════════ */
.nc-host-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.nc-host-icon {
  font-size: 0.7rem;
  color: var(--color-text-faint);
  flex-shrink: 0;
}
.nc-host-addr {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nc-mode-badge {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  padding: 2px 7px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
.mode-rw {
  background: color-mix(in oklch, var(--color-synced) 18%, transparent);
  color: var(--color-synced);
  border: 1px solid color-mix(in oklch, var(--color-synced) 35%, transparent);
}
.mode-ro {
  background: color-mix(in oklch, var(--color-readonly) 18%, transparent);
  color: var(--color-readonly);
  border: 1px solid color-mix(in oklch, var(--color-readonly) 35%, transparent);
}

/* ═══════════════════════════════════════
   METRICS
═══════════════════════════════════════ */
.nc-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  /* увеличены отступы внутри блока метрик */
  gap: var(--space-4) var(--space-5);
  padding: var(--space-4) var(--space-4);
  background: var(--color-surface-offset);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.nc-metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.nc-mk {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--color-text-faint);
  font-weight: 600;
}
.nc-mv {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
}
.nc-mv--mono {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
.nc-mv--warn {
  color: var(--color-degraded);
}

/* ═══════════════════════════════════════
   SSH BADGE
═══════════════════════════════════════ */
.nc-ssh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  align-self: flex-start;
}
.nc-ssh i { font-size: 0.65rem; }
.nc-ssh--ok {
  background: color-mix(in oklch, var(--color-text-faint) 12%, transparent);
  color: var(--color-text-faint);
}
.nc-ssh--fail {
  background: color-mix(in oklch, var(--color-offline) 15%, transparent);
  color: var(--color-offline);
  border: 1px solid color-mix(in oklch, var(--color-offline) 30%, transparent);
}

/* ═══════════════════════════════════════
   ACTION BAR
═══════════════════════════════════════ */
.nc-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}

.nc-action-ping {
  flex: 1;
  justify-content: center;
  font-weight: 600 !important;
  font-size: var(--text-sm) !important;
  border-radius: var(--radius-md) !important;
}
:deep(.nc-action-ping.p-button) {
  background: color-mix(in oklch, var(--color-primary) 12%, transparent) !important;
  border: 1px solid color-mix(in oklch, var(--color-primary) 40%, transparent) !important;
  color: var(--color-primary) !important;
}
:deep(.nc-action-ping.p-button:hover:not(:disabled)) {
  background: color-mix(in oklch, var(--color-primary) 22%, transparent) !important;
  border-color: var(--color-primary) !important;
}

.nc-action-icon {
  width: 32px !important;
  height: 32px !important;
  padding: 0 !important;
  flex-shrink: 0;
}
:deep(.nc-action-icon.p-button) {
  color: var(--color-text-muted) !important;
}
:deep(.nc-action-icon.p-button:hover:not(:disabled)) {
  color: var(--color-text) !important;
  background: var(--color-surface-offset) !important;
}
:deep(.nc-action-danger.p-button:hover:not(:disabled)) {
  color: var(--color-offline) !important;
  background: color-mix(in oklch, var(--color-offline) 12%, transparent) !important;
}
:deep(.nc-action-icon .p-button-icon) {
  font-size: 0.9rem !important;
}
</style>
