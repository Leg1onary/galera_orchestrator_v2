<script setup lang="ts">
import { computed, ref } from 'vue'
import { nodesApi } from '@/api/nodes'
import type { NodeAction, NodeStatusItem } from '@/api/nodes'
import { useQueryClient } from '@tanstack/vue-query'
import { useOperationsStore } from '@/stores/operations'
import { useConfirm } from 'primevue/useconfirm'

const props    = defineProps<{ node: NodeStatusItem; clusterId: number }>()
const qc       = useQueryClient()
const opsStore = useOperationsStore()
const confirm  = useConfirm()

const actionLoading  = ref<NodeAction | null>(null)
const pingLoading    = ref(false)
const pingResult     = ref<{ ssh_ok: boolean; db_ok: boolean; ssh_latency_ms: number | null } | null>(null)
const pingVisible    = ref(false)
let   pingTimer: ReturnType<typeof setTimeout> | null = null

const isLocked = computed(() => {
  const op = opsStore.activeOperation
  return op && ['pending', 'running', 'cancel_requested'].includes(op.status)
})

const nodeState = computed(() => {
  const live = props.node.live
  const raw  = (live.wsrep_local_state_comment ?? '').toUpperCase()
  if (!live.ssh_ok || raw === 'OFFLINE') return 'OFFLINE'
  if (live.wsrep_ready === 'OFF')        return 'NOT_READY'
  if (raw === 'SYNCED' && live.readonly)  return 'SYNCED_RO'
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

const isNodeOffline = computed(() => nodeState.value === 'OFFLINE')

const clusterStatus    = computed(() => props.node.live.wsrep_cluster_status ?? null)
const isNonPrimary     = computed(() =>
  clusterStatus.value !== null && clusterStatus.value.toLowerCase() !== 'primary'
)

const isBusy = computed(() => actionLoading.value !== null)

const flowControlDisplay = computed(() => {
  const v = props.node.live.wsrep_flow_control_paused
  if (v == null) return '\u2014'
  return v.toFixed(3)
})

const recvQueueDisplay = computed(() => {
  const v = props.node.live.wsrep_local_recv_queue
  if (v == null) return '\u2014'
  return String(v)
})

const recvQueueWarn = computed(() => (props.node.live.wsrep_local_recv_queue ?? 0) > 0)
const flowWarn      = computed(() => (props.node.live.wsrep_flow_control_paused ?? 0) > 0)

const pingResultText = computed(() => {
  if (!pingResult.value) return ''
  const r = pingResult.value
  const lat = r.ssh_latency_ms != null ? `${r.ssh_latency_ms}ms` : '—'
  return `SSH: ${r.ssh_ok ? 'OK' : 'FAIL'} | DB: ${r.db_ok ? 'OK' : 'FAIL'} | ${lat}`
})

const pingResultOk = computed(() =>
  !!pingResult.value?.ssh_ok && !!pingResult.value?.db_ok
)

// ── Last check timestamp ──────────────────────────────────────────────────
const lastCheckLabel = computed(() => {
  const ts = props.node.live.last_check_ts
  if (!ts) return null
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
})

async function execAction(action: NodeAction) {
  actionLoading.value = action
  try {
    await nodesApi.action(props.clusterId, props.node.id, action)
    qc.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'status'] })
  } finally {
    actionLoading.value = null
  }
}

async function ping() {
  if (pingTimer) clearTimeout(pingTimer)
  pingLoading.value = true
  pingVisible.value = false
  pingResult.value  = null
  try {
    const res = await nodesApi.testConnection(props.clusterId, props.node.id)
    pingResult.value  = res
    pingVisible.value = true
    pingTimer = setTimeout(() => { pingVisible.value = false }, 4000)
  } finally {
    pingLoading.value = false
  }
}

function confirmDestructive(action: NodeAction, label: string) {
  if (isLocked.value) return
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
    <div class="nc-stripe" aria-hidden="true" />

    <div class="nc-body" :class="{ 'nc-body--busy': isBusy }">

      <!-- HEADER -->
      <div class="nc-header">
        <div class="nc-title-group">
          <span class="nc-name">{{ node.name }}</span>
          <span v-if="node.dc_name" class="nc-dc">{{ node.dc_name }}</span>
        </div>
        <Tag
          :value="stateInfo.label"
          :severity="stateInfo.severity"
          class="nc-state-tag"
        />
      </div>

      <!-- HOST + MODE -->
      <div class="nc-host-row">
        <i class="pi pi-server nc-host-icon" />
        <span class="nc-host-addr">{{ node.host }}:{{ node.port }}</span>
        <span class="nc-mode-badge" :class="node.live.readonly ? 'mode-ro' : 'mode-rw'">
          {{ node.live.readonly ? 'RO' : 'RW' }}
        </span>
      </div>

      <!-- METRICS -->
      <div class="nc-metrics">
        <div class="nc-metric">
          <span class="nc-mk">Cluster Size</span>
          <span class="nc-mv">{{ node.live.wsrep_cluster_size ?? '\u2014' }}</span>
        </div>

        <div class="nc-metric">
          <span class="nc-mk">Component</span>
          <span
            class="nc-mv nc-mv--mono"
            :class="isNonPrimary ? 'nc-mv--critical' : ''"
          >
            <i
              v-if="isNonPrimary"
              class="pi pi-exclamation-triangle nc-critical-icon"
              v-tooltip.top="'Split-brain risk: node is not part of Primary Component'"
            />
            {{ clusterStatus ?? '\u2014' }}
          </span>
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

      <!-- SSH -->
      <div class="nc-ssh" :class="node.live.ssh_ok ? 'nc-ssh--ok' : 'nc-ssh--fail'">
        <i :class="node.live.ssh_ok ? 'pi pi-lock' : 'pi pi-lock-open'" />
        <span>SSH {{ node.live.ssh_ok ? 'OK' : 'FAIL' }}</span>
      </div>

      <!-- PING RESULT -->
      <Transition name="ping-result">
        <div
          v-if="pingVisible && pingResult"
          class="nc-ping-result"
          :class="pingResultOk ? 'nc-ping-result--ok' : 'nc-ping-result--fail'"
        >
          <i :class="pingResultOk ? 'pi pi-check-circle' : 'pi pi-times-circle'" />
          <span>{{ pingResultText }}</span>
        </div>
      </Transition>

      <!-- ACTION BAR -->
      <div class="nc-actions">
        <button
          class="nc-btn nc-btn--primary"
          :disabled="!!isLocked || pingLoading"
          title="Check node reachability"
          @click.stop="ping"
        >
          <i :class="pingLoading ? 'pi pi-spin pi-spinner' : 'pi pi-wifi'" />
          <span>Ping</span>
        </button>

        <button
          class="nc-btn nc-btn--default"
          :disabled="!!isLocked || actionLoading === 'restart'"
          title="Restart MySQL"
          @click.stop="confirmDestructive('restart', 'Restart')"
        >
          <i :class="actionLoading === 'restart' ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'" />
          <span>Restart</span>
        </button>

        <button
          v-if="!isNodeOffline"
          class="nc-btn nc-btn--danger"
          :disabled="!!isLocked || actionLoading === 'stop'"
          title="Stop MySQL"
          @click.stop="confirmDestructive('stop', 'Stop')"
        >
          <i :class="actionLoading === 'stop' ? 'pi pi-spin pi-spinner' : 'pi pi-stop-circle'" />
          <span>Stop</span>
        </button>
        <button
          v-else
          class="nc-btn nc-btn--success"
          :disabled="!!isLocked || actionLoading === 'start'"
          title="Start MySQL"
          @click.stop="confirmDestructive('start', 'Start')"
        >
          <i :class="actionLoading === 'start' ? 'pi pi-spin pi-spinner' : 'pi pi-play'" />
          <span>Start</span>
        </button>

        <button
          class="nc-btn nc-btn--danger"
          :disabled="!!isLocked || actionLoading === 'rejoin-force'"
          title="Force Rejoin (wsrep_sst)"
          @click.stop="confirmDestructive('rejoin-force', 'Force Rejoin')"
        >
          <i :class="actionLoading === 'rejoin-force' ? 'pi pi-spin pi-spinner' : 'pi pi-replay'" />
          <span>Rejoin</span>
        </button>
      </div>

      <!-- LAST CHECK -->
      <div v-if="lastCheckLabel" class="nc-last-check">
        <i class="pi pi-clock nc-last-check-icon" />
        <span>{{ lastCheckLabel }}</span>
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
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: opacity 200ms ease;
}
.nc-body--busy {
  opacity: 0.55;
  pointer-events: none;
}

/* ═══════════════════════════════════════
   HEADER
═══════════════════════════════════════ */
.nc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-1);
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

/* ═══════════════════════════════════════
   STATE TAG
═══════════════════════════════════════ */
.nc-state-tag { flex-shrink: 0; }

:deep(.nc-state-tag.p-tag) {
  padding: 5px 10px !important;
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid transparent !important;
  position: relative;
  overflow: hidden;
}
:deep(.nc-state-tag.p-tag)::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, oklch(1 0 0 / 0.12) 0%, transparent 60%);
  pointer-events: none;
}

.node-card--offline  :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-offline) 22%, transparent) !important; border-color: color-mix(in oklch, var(--color-offline) 45%, transparent) !important; color: var(--color-offline) !important; }
.node-card--synced   :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-synced) 18%, transparent) !important; border-color: color-mix(in oklch, var(--color-synced) 40%, transparent) !important; color: var(--color-synced) !important; }
.node-card--readonly :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-readonly) 18%, transparent) !important; border-color: color-mix(in oklch, var(--color-readonly) 40%, transparent) !important; color: var(--color-readonly) !important; }
.node-card--donor    :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-synced) 18%, transparent) !important; border-color: color-mix(in oklch, var(--color-donor) 40%, transparent) !important; color: var(--color-donor) !important; }
.node-card--degraded :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-degraded) 18%, transparent) !important; border-color: color-mix(in oklch, var(--color-degraded) 40%, transparent) !important; color: var(--color-degraded) !important; }
.node-card--unknown  :deep(.nc-state-tag.p-tag) { background: color-mix(in oklch, var(--color-text-faint) 15%, transparent) !important; border-color: color-mix(in oklch, var(--color-text-faint) 30%, transparent) !important; color: var(--color-text-muted) !important; }

/* ═══════════════════════════════════════
   HOST ROW
═══════════════════════════════════════ */
.nc-host-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.nc-host-icon { font-size: 0.7rem; color: var(--color-text-faint); flex-shrink: 0; }
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
.mode-rw { background: color-mix(in oklch, var(--color-synced) 18%, transparent); color: var(--color-synced); border: 1px solid color-mix(in oklch, var(--color-synced) 35%, transparent); }
.mode-ro { background: color-mix(in oklch, var(--color-readonly) 18%, transparent); color: var(--color-readonly); border: 1px solid color-mix(in oklch, var(--color-readonly) 35%, transparent); }

/* ═══════════════════════════════════════
   METRICS
═══════════════════════════════════════ */
.nc-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3) var(--space-4);
  padding: var(--space-3);
  background: var(--color-surface-offset);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  margin-top: var(--space-1);
}
.nc-metric   { display: flex; flex-direction: column; gap: var(--space-2); }
.nc-mk       { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.09em; color: var(--color-text-faint); font-weight: 600; }
.nc-mv       { font-size: var(--text-base); font-weight: 700; color: var(--color-text); }
.nc-mv--mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.nc-mv--warn { color: var(--color-degraded); }

.nc-mv--critical {
  color: var(--color-offline);
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}
.nc-critical-icon {
  font-size: 0.72rem;
  flex-shrink: 0;
  animation: nc-pulse 1.8s ease-in-out infinite;
}
@keyframes nc-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.45; }
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
.nc-ssh--ok   { background: color-mix(in oklch, var(--color-text-faint) 12%, transparent); color: var(--color-text-faint); }
.nc-ssh--fail { background: color-mix(in oklch, var(--color-offline) 15%, transparent); color: var(--color-offline); border: 1px solid color-mix(in oklch, var(--color-offline) 30%, transparent); }

/* ═══════════════════════════════════════
   PING RESULT
═══════════════════════════════════════ */
.nc-ping-result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  align-self: flex-start;
  border: 1px solid transparent;
}
.nc-ping-result i { font-size: 0.7rem; flex-shrink: 0; }
.nc-ping-result--ok   { background: color-mix(in oklch, var(--color-synced) 12%, transparent); color: var(--color-synced); border-color: color-mix(in oklch, var(--color-synced) 30%, transparent); }
.nc-ping-result--fail { background: color-mix(in oklch, var(--color-offline) 12%, transparent); color: var(--color-offline); border-color: color-mix(in oklch, var(--color-offline) 30%, transparent); }

.ping-result-enter-active { transition: opacity 200ms ease, transform 200ms ease; }
.ping-result-leave-active  { transition: opacity 600ms ease, transform 600ms ease; }
.ping-result-enter-from,
.ping-result-leave-to     { opacity: 0; transform: translateY(-4px); }

/* ═══════════════════════════════════════
   ACTION BAR
═══════════════════════════════════════ */
.nc-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-3);
  margin-top: var(--space-1);
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.nc-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: 0 var(--space-3);
  height: 34px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  font-family: inherit;
  letter-spacing: 0.04em;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 150ms ease, border-color 150ms ease, color 150ms ease, opacity 150ms ease;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.nc-btn i { font-size: 0.78rem; flex-shrink: 0; }
.nc-btn:disabled { opacity: 0.38; cursor: not-allowed; pointer-events: none; }

.nc-btn--primary {
  background: color-mix(in oklch, var(--color-primary) 14%, transparent);
  border-color: color-mix(in oklch, var(--color-primary) 38%, transparent);
  color: var(--color-primary);
}
.nc-btn--primary:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-primary) 24%, transparent);
  border-color: var(--color-primary);
}

.nc-btn--default {
  background: color-mix(in oklch, var(--color-text-faint) 8%, transparent);
  border-color: color-mix(in oklch, var(--color-text-faint) 22%, transparent);
  color: var(--color-text-muted);
}
.nc-btn--default:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-text-faint) 16%, transparent);
  border-color: color-mix(in oklch, var(--color-text-faint) 40%, transparent);
  color: var(--color-text);
}

.nc-btn--danger {
  background: color-mix(in oklch, var(--color-offline) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-offline) 28%, transparent);
  color: var(--color-offline);
}
.nc-btn--danger:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-offline) 20%, transparent);
  border-color: color-mix(in oklch, var(--color-offline) 55%, transparent);
}

.nc-btn--success {
  background: color-mix(in oklch, var(--color-synced) 12%, transparent);
  border-color: color-mix(in oklch, var(--color-synced) 35%, transparent);
  color: var(--color-synced);
}
.nc-btn--success:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-synced) 22%, transparent);
  border-color: color-mix(in oklch, var(--color-synced) 60%, transparent);
}

/* ═══════════════════════════════════════
   LAST CHECK
═══════════════════════════════════════ */
.nc-last-check {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-divider);
}
.nc-last-check-icon { font-size: 0.65rem; }
</style>
