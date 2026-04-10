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
  wsrep_local_state_comment: string | null
  wsrep_cluster_status: string | null
  wsrep_cluster_size: number | null
  wsrep_flow_control_paused: number | null
  wsrep_local_recv_queue: number | null
  wsrep_ready: string | null
  ssh_ok: boolean
  readonly: boolean
}

const props   = defineProps<{ node: NodeLive; clusterId: number }>()
const qc      = useQueryClient()
const opsStore = useOperationsStore()
const confirm = useConfirm()

const actionLoading = ref<NodeAction | null>(null)

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

const STATE_MAP: Record<string, { label: string; cls: string; severity: string }> = {
  SYNCED:    { label: 'Synced',    cls: 'synced',   severity: 'success' },
  SYNCED_RO: { label: 'Synced RO', cls: 'readonly', severity: 'warn' },
  DONOR:     { label: 'Donor',     cls: 'donor',    severity: 'info' },
  JOINER:    { label: 'Joiner',    cls: 'donor',    severity: 'info' },
  DESYNCED:  { label: 'Desynced',  cls: 'donor',    severity: 'info' },
  NOT_READY: { label: 'Not Ready', cls: 'degraded', severity: 'warn' },
  OFFLINE:   { label: 'Offline',   cls: 'offline',  severity: 'danger' },
  UNKNOWN:   { label: 'Unknown',   cls: 'unknown',  severity: 'secondary' },
}

const stateInfo = computed(() => STATE_MAP[nodeState.value] ?? STATE_MAP.UNKNOWN)

// recv queue — 0..100 mapped to knob (cap at 100)
const recvQueuePct = computed(() => {
  const v = props.node.wsrep_local_recv_queue ?? 0
  return Math.min(v, 100)
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

function ping() {
  execAction('ping' as NodeAction)
}

function confirmDestructive(action: NodeAction, label: string) {
  if (isLocked.value) return
  confirm.require({
    message: `Run "${label}" on node ${props.node.name}?`,
    header:  'Confirm action',
    icon:    'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: label,
    acceptClass: 'p-button-danger',
    accept: () => execAction(action),
  })
}

// SplitButton model for destructive actions
const splitItems = computed(() => [
  {
    label: 'Restart',
    icon:  'pi pi-refresh',
    command: () => confirmDestructive('restart', 'Restart'),
    disabled: !!isLocked.value,
  },
  {
    label: 'Stop',
    icon:  'pi pi-stop',
    class: 'danger-item',
    command: () => confirmDestructive('stop', 'Stop'),
    disabled: !!isLocked.value,
  },
  {
    label: 'Force Rejoin',
    icon:  'pi pi-replay',
    class: 'danger-item',
    command: () => confirmDestructive('rejoin-force', 'Force Rejoin'),
    disabled: !!isLocked.value,
  },
])
</script>

<template>
  <article class="node-card anim-fade-in" :class="'node-card--' + stateInfo.cls">
    <div class="nc-stripe" aria-hidden="true" />

    <div class="nc-body">
      <!-- Header -->
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

      <!-- Host row -->
      <div class="nc-host">
        <span class="nc-host-addr">{{ node.host }}:{{ node.port }}</span>
        <Tag
          :value="node.readonly ? 'RO' : 'RW'"
          :severity="node.readonly ? 'warn' : 'success'"
          class="nc-mode-tag"
        />
      </div>

      <!-- Metrics grid + recv queue knob -->
      <div class="nc-metrics-wrap">
        <div class="nc-metrics">
          <div class="nc-metric">
            <span class="nc-mk">cluster size</span>
            <span class="nc-mv">{{ node.wsrep_cluster_size ?? '—' }}</span>
          </div>
          <div class="nc-metric">
            <span class="nc-mk">component</span>
            <span class="nc-mv">{{ node.wsrep_cluster_status ?? '—' }}</span>
          </div>
          <div class="nc-metric">
            <span class="nc-mk">flow ctrl</span>
            <span class="nc-mv" :class="flowWarn ? 'nc-mv--warn' : ''">
              {{ node.wsrep_flow_control_paused !== null
                ? node.wsrep_flow_control_paused.toFixed(3) : '—' }}
            </span>
          </div>
        </div>

        <!-- Knob recv queue -->
        <div class="nc-knob-wrap" v-tooltip.top="'wsrep_local_recv_queue'">
          <Knob
            :model-value="recvQueuePct"
            :size="52"
            :stroke-width="6"
            :min="0"
            :max="100"
            readonly
            :value-color="recvQueueWarn ? 'var(--color-degraded)' : 'var(--color-synced)'"
            range-color="var(--color-surface-3)"
            text-color="var(--color-text-muted)"
            :pt="{ value: { style: 'font-size: 0.6rem; font-family: var(--font-mono)' } }"
          />
          <span class="nc-knob-label">recv q</span>
        </div>
      </div>

      <!-- SSH indicator -->
      <div class="nc-ssh" :class="node.ssh_ok ? 'nc-ssh--ok' : 'nc-ssh--fail'">
        <i :class="node.ssh_ok ? 'pi pi-lock' : 'pi pi-lock-open'" />
        <span>SSH {{ node.ssh_ok ? 'OK' : 'FAIL' }}</span>
      </div>

      <!-- Actions: ping + SplitButton -->
      <div class="nc-actions">
        <Button
          icon="pi pi-wifi"
          text
          rounded
          size="small"
          :loading="actionLoading === 'ping'"
          v-tooltip.top="'Ping'"
          aria-label="Ping node"
          @click.stop="ping"
        />
        <SplitButton
          label="Actions"
          icon="pi pi-bolt"
          :model="splitItems"
          size="small"
          severity="secondary"
          class="nc-split"
          :disabled="!!isLocked"
        />
      </div>
    </div>
  </article>
</template>

<style scoped>
.node-card {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  transition: box-shadow var(--transition-normal), border-color var(--transition-normal);
}
.node-card:hover { box-shadow: var(--shadow-md); }

/* Left state stripe */
.nc-stripe {
  width: 3px;
  flex-shrink: 0;
  background: var(--node-stripe, var(--color-border));
}
.node-card--synced   { --node-stripe: var(--color-synced); }
.node-card--readonly { --node-stripe: var(--color-readonly); }
.node-card--donor    { --node-stripe: var(--color-donor); }
.node-card--degraded { --node-stripe: var(--color-degraded); }
.node-card--offline  { --node-stripe: var(--color-offline); }
.node-card--unknown  { --node-stripe: var(--color-text-faint); }

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
.nc-title-group { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.nc-name  { font-size: var(--text-md); font-weight: 700; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nc-dc    { font-size: var(--text-xs); color: var(--color-text-faint); text-transform: uppercase; letter-spacing: 0.07em; font-weight: 500; }
.nc-state-tag { font-size: 0.65rem !important; }

/* Host */
.nc-host { display: flex; align-items: center; gap: var(--space-2); }
.nc-host-addr { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-text-muted); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nc-mode-tag { font-size: 0.6rem !important; padding: 1px 5px !important; }

/* Metrics + knob */
.nc-metrics-wrap { display: flex; align-items: center; gap: var(--space-3); }
.nc-metrics { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2) var(--space-3); }
.nc-metric  { display: flex; flex-direction: column; gap: 1px; }
.nc-mk { font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-faint); font-weight: 500; }
.nc-mv { font-size: var(--text-sm); font-weight: 600; font-family: var(--font-mono); color: var(--color-text); font-variant-numeric: tabular-nums; }
.nc-mv--warn { color: var(--color-degraded); }

/* Knob */
.nc-knob-wrap { display: flex; flex-direction: column; align-items: center; gap: 2px; flex-shrink: 0; }
.nc-knob-label { font-size: var(--text-xs); color: var(--color-text-faint); text-transform: uppercase; letter-spacing: 0.05em; }

/* SSH */
.nc-ssh { display: flex; align-items: center; gap: var(--space-1); font-size: var(--text-xs); font-weight: 500; }
.nc-ssh i { font-size: 0.6rem; }
.nc-ssh--ok   { color: var(--color-text-faint); }
.nc-ssh--fail { color: var(--color-offline); }

/* Actions */
.nc-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-1);
  border-top: 1px solid var(--color-border-muted);
}
.nc-split { flex: 1; }
:deep(.nc-split .p-splitbutton-defaultbutton) { flex: 1; justify-content: center; }
:deep(.danger-item .p-menuitem-link) { color: var(--color-offline) !important; }
</style>
