<script setup lang="ts">
/**
 * #6 Split-Brain Recovery Wizard
 * Guides user through selecting a trusted node and executing pc.bootstrap=YES recovery.
 */
import { ref, computed, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useWsStore } from '@/stores/ws'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Skeleton from 'primevue/skeleton'
import { recoveryAdvancedApi, type QuorumStatusResponse } from '@/api/recovery-advanced'
import { recoveryApi } from '@/api/recovery'
import { api } from '@/api/client'
import type { NodeListItem } from '@/api/nodes'

const props = defineProps<{ clusterId: number | null }>()

type WizardStep = 'detect' | 'select' | 'running' | 'done'

const clusterStore = useClusterStore()
const wsStore      = useWsStore()

const step          = ref<WizardStep>('detect')
const quorum        = ref<QuorumStatusResponse | null>(null)
const nodes         = ref<NodeListItem[]>([])
const loading       = ref(false)
const error         = ref<string | null>(null)
const selectedNode  = ref<number | null>(null)
const operationId   = ref<number | null>(null)
const progressMsgs  = ref<string[]>([])
const opSuccess     = ref<boolean | null>(null)
const opFinalMsg    = ref<string | null>(null)
const confirming    = ref(false)

// Load quorum status + node list
async function detect() {
  if (!props.clusterId) return
  loading.value = true; error.value = null
  try {
    const [q, nodesRes] = await Promise.all([
      recoveryAdvancedApi.getQuorumStatus(props.clusterId),
      api.get<NodeListItem[]>(`/api/clusters/${props.clusterId}/nodes`).then(r => r.data),
    ])
    quorum.value = q
    nodes.value  = nodesRes
    step.value   = 'select'
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

// WS subscription for operation progress
let wsUnsub: (() => void) | null = null
function subscribeWs() {
  if (!props.clusterId || !operationId.value) return
  wsUnsub = wsStore.on('operation_progress', (payload: any) => {
    if (payload.operation_id === operationId.value) {
      progressMsgs.value.push(payload.message ?? '')
    }
  })
  wsStore.on('operation_finished', (payload: any) => {
    if (payload.operation_id === operationId.value) {
      opSuccess.value  = payload.success
      opFinalMsg.value = payload.message
      step.value = 'done'
      wsUnsub?.(); wsUnsub = null
    }
  })
}

async function startRecovery() {
  if (!props.clusterId || selectedNode.value === null) return
  confirming.value = false
  loading.value = true; error.value = null; progressMsgs.value = []
  try {
    const res = await recoveryAdvancedApi.startSplitBrainRecovery(props.clusterId, {
      trusted_node_id: selectedNode.value,
    })
    operationId.value = res.operation_id
    step.value = 'running'
    subscribeWs()
    pollStatus()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to start recovery'
  } finally {
    loading.value = false
  }
}

let _pollHandle: ReturnType<typeof setInterval> | null = null
function pollStatus() {
  if (!props.clusterId || !operationId.value) return
  _pollHandle = setInterval(async () => {
    try {
      const statusRes = await recoveryApi.getStatus(props.clusterId!)
      const op = statusRes.active_operation
      if (op?.operation_id === operationId.value) {
        if (['success', 'failed', 'cancelled'].includes(op.state)) {
          opSuccess.value  = op.state === 'success'
          opFinalMsg.value = op.message ?? null
          step.value = 'done'
          clearInterval(_pollHandle!); _pollHandle = null
        }
      }
    } catch { /* poll errors ignored */ }
  }, 3000)
}

watch(() => props.clusterId, () => { step.value = 'detect'; quorum.value = null; nodes.value = [] })

const nonPrimaryNodes = computed(() =>
  quorum.value?.nodes.filter(n =>
    (n.wsrep_cluster_status ?? '').toUpperCase() !== 'PRIMARY' && !n.error
  ) ?? []
)

function nodeStateClass(n: any): string {
  const s = (n.wsrep_cluster_status ?? '').toUpperCase()
  if (s === 'PRIMARY')     return 'state--primary'
  if (s === 'NON-PRIMARY') return 'state--nonprimary'
  return 'state--offline'
}

function reset() {
  step.value = 'detect'; quorum.value = null; nodes.value = []
  selectedNode.value = null; operationId.value = null
  progressMsgs.value = []; opSuccess.value = null; opFinalMsg.value = null
  wsUnsub?.(); wsUnsub = null
  if (_pollHandle) { clearInterval(_pollHandle); _pollHandle = null }
}
</script>

<template>
  <div class="sbw">
    <div class="sbw-header">
      <h3 class="sbw-title">Split-Brain Recovery</h3>
      <p class="sbw-desc">
        Use when all nodes are stuck in <strong>Non-Primary</strong> state and cannot form quorum.
        Selects one trusted node and forces it to become a new Primary Component via
        <code>SET GLOBAL wsrep_provider_options='pc.bootstrap=YES'</code>.
      </p>
    </div>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <!-- Step: detect -->
    <div v-if="step === 'detect'" class="sbw-step sbw-step--detect">
      <div class="detect-icon"><i class="pi pi-search" /></div>
      <p class="detect-hint">Scan current cluster quorum state to identify Non-Primary nodes.</p>
      <Button icon="pi pi-search" label="Scan cluster state" :loading="loading" @click="detect()" />
    </div>

    <!-- Step: select -->
    <template v-if="step === 'select' && quorum">
      <!-- Summary -->
      <div class="sbw-summary">
        <div class="sbw-stat" :class="quorum.quorum_ok ? 'sbw-stat--ok' : 'sbw-stat--err'">
          <span class="sbw-stat-label">Quorum</span>
          <Tag :value="quorum.quorum_ok ? 'OK' : 'BROKEN'" :severity="quorum.quorum_ok ? 'success' : 'danger'" />
        </div>
        <div class="sbw-stat-sep" />
        <div class="sbw-stat">
          <span class="sbw-stat-label">Primary</span>
          <span class="sbw-stat-val">{{ quorum.primary_count }}/{{ quorum.total_configured }}</span>
        </div>
        <div class="sbw-stat-sep" />
        <div class="sbw-stat" :class="quorum.non_primary_count > 0 ? 'sbw-stat--warn' : ''">
          <span class="sbw-stat-label">Non-Primary</span>
          <span class="sbw-stat-val">{{ quorum.non_primary_count }}</span>
        </div>
      </div>

      <Message v-if="quorum.quorum_ok" severity="success" :closable="false">
        Quorum is OK — Split-Brain Recovery is not needed. If the cluster appears healthy, use the regular Bootstrap or Rejoin wizard instead.
      </Message>

      <div v-else>
        <p class="select-label">Select the <strong>most recent / trusted node</strong> to bootstrap from:</p>

        <DataTable
          :value="quorum.nodes"
          dataKey="node_id"
          size="small"
          class="settings-table sbw-table"
          v-model:selection="selectedNode"
          selectionMode="single"
          :pt="{
            bodyRow: ({ context }: any) => ({
              class: selectedNode === context.data.node_id ? 'sbw-row--selected' : ''
            })
          }"
          @row-click="(e) => selectedNode = e.data.node_id"
        >
          <Column style="width: 48px">
            <template #body="{ data: row }">
              <div class="sbw-radio" :class="{ 'sbw-radio--selected': selectedNode === row.node_id }">
                <div class="sbw-radio-inner" v-if="selectedNode === row.node_id" />
              </div>
            </template>
          </Column>

          <Column field="node_name" header="Node">
            <template #body="{ data: row }">
              <div class="cell-node">
                <span class="cell-node-name">{{ row.node_name }}</span>
                <span class="cell-node-host">{{ row.host }}</span>
              </div>
            </template>
          </Column>

          <Column header="Cluster Status" style="width: 150px">
            <template #body="{ data: row }">
              <span class="node-state" :class="nodeStateClass(row)">
                {{ row.error ? 'OFFLINE' : (row.wsrep_cluster_status ?? '—') }}
              </span>
            </template>
          </Column>

          <Column header="Node State" style="width: 130px">
            <template #body="{ data: row }">
              <span class="cell-mono">{{ row.wsrep_local_state_comment ?? '—' }}</span>
            </template>
          </Column>
        </DataTable>

        <div class="sbw-actions">
          <Button icon="pi pi-refresh" label="Re-scan" outlined size="small" @click="detect()" />
          <Button
            icon="pi pi-replay"
            label="Start Recovery"
            severity="danger"
            :disabled="selectedNode === null"
            size="small"
            @click="confirming = true"
          />
        </div>

        <!-- Confirm dialog -->
        <div v-if="confirming" class="sbw-confirm">
          <i class="pi pi-exclamation-triangle sbw-confirm-icon" />
          <div class="sbw-confirm-body">
            <strong>Are you sure?</strong>
            <p>This will execute <code>SET GLOBAL wsrep_provider_options='pc.bootstrap=YES'</code> on
              <strong>{{ quorum.nodes.find(n => n.node_id === selectedNode)?.node_name }}</strong>.
              Transactions on non-trusted nodes since the split may be lost.</p>
          </div>
          <div class="sbw-confirm-btns">
            <Button label="Cancel" outlined size="small" @click="confirming = false" />
            <Button label="Confirm — Start" severity="danger" size="small" @click="startRecovery()" />
          </div>
        </div>
      </div>
    </template>

    <!-- Step: running -->
    <div v-if="step === 'running'" class="sbw-running">
      <div class="sbw-running-header">
        <i class="pi pi-spin pi-spinner" />
        <span>Split-Brain Recovery in progress…</span>
      </div>
      <div class="sbw-log">
        <div v-for="(msg, i) in progressMsgs" :key="i" class="sbw-log-line">
          <span class="sbw-log-idx">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="sbw-log-msg">{{ msg }}</span>
        </div>
        <div v-if="!progressMsgs.length" class="sbw-log-waiting">
          <i class="pi pi-circle" />Waiting for backend events…
        </div>
      </div>
    </div>

    <!-- Step: done -->
    <div v-if="step === 'done'" class="sbw-done">
      <div class="sbw-done-icon" :class="opSuccess ? 'sbw-done--ok' : 'sbw-done--err'">
        <i :class="opSuccess ? 'pi pi-check-circle' : 'pi pi-times-circle'" />
      </div>
      <p class="sbw-done-msg">{{ opFinalMsg }}</p>
      <div v-if="progressMsgs.length" class="sbw-log sbw-log--done">
        <div v-for="(msg, i) in progressMsgs" :key="i" class="sbw-log-line">
          <span class="sbw-log-idx">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="sbw-log-msg">{{ msg }}</span>
        </div>
      </div>
      <Button label="Start over" outlined size="small" icon="pi pi-refresh" @click="reset()" />
    </div>
  </div>
</template>

<style scoped>
.sbw { display: flex; flex-direction: column; gap: var(--space-4); }
.sbw-header { display: flex; flex-direction: column; gap: var(--space-1); }
.sbw-title  { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: -0.02em; }
.sbw-desc   { font-size: var(--text-xs); color: var(--color-text-muted); margin: 0; line-height: 1.6; }
.sbw-desc strong { color: var(--color-text); font-weight: 600; }
.sbw-desc code {
  font-family: var(--font-mono); font-size: 0.85em;
  background: var(--color-surface-3); border-radius: 3px; padding: 1px 4px; color: var(--color-primary);
}

/* Detect */
.sbw-step--detect { display: flex; flex-direction: column; align-items: center; gap: var(--space-4); padding: var(--space-10) 0; }
.detect-icon { width: 64px; height: 64px; border-radius: var(--radius-full); background: var(--color-surface-2); border: 1px solid var(--color-border); display: flex; align-items: center; justify-content: center; font-size: 1.6rem; color: var(--color-text-faint); }
.detect-hint { font-size: var(--text-sm); color: var(--color-text-muted); }

/* Summary */
.sbw-summary {
  display: flex; align-items: center;
  background: var(--color-surface-2); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-3) var(--space-5);
}
.sbw-stat        { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; }
.sbw-stat-sep    { width: 1px; height: 30px; background: var(--color-border); }
.sbw-stat-label  { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-faint); font-weight: 600; }
.sbw-stat-val    { font-size: var(--text-md); font-weight: 800; color: var(--color-text-muted); font-family: var(--font-mono); }
.sbw-stat--ok   .sbw-stat-val { color: var(--color-synced); }
.sbw-stat--err  .sbw-stat-val { color: var(--color-error); }
.sbw-stat--warn .sbw-stat-val { color: var(--color-warning); }

.select-label { font-size: var(--text-sm); color: var(--color-text-muted); margin: 0; }
.select-label strong { color: var(--color-text); }

/* Table */
:deep(.settings-table .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.settings-table .p-datatable-thead > tr > th) {
  padding: var(--space-4) var(--space-6) !important; font-size: var(--text-xs) !important;
  font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--color-text-faint) !important; background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important; vertical-align: middle;
  cursor: pointer;
}
:deep(.settings-table .p-datatable-tbody > tr:hover > td) { background: rgba(45,212,191,0.04) !important; }
:deep(.sbw-row--selected > td) { background: rgba(45,212,191,0.07) !important; }

.sbw-radio {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid var(--color-border); display: flex; align-items: center; justify-content: center;
  transition: border-color 200ms;
}
.sbw-radio--selected { border-color: var(--color-primary); }
.sbw-radio-inner { width: 8px; height: 8px; border-radius: 50%; background: var(--color-primary); }

.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }

.node-state { font-size: 0.68rem; font-weight: 700; font-family: var(--font-mono); letter-spacing: 0.06em; padding: 2px 8px; border-radius: var(--radius-full); }
.state--primary     { background: var(--color-synced-dim); color: var(--color-synced); }
.state--nonprimary  { background: color-mix(in oklch, var(--color-warning) 12%, transparent); color: var(--color-warning); }
.state--offline     { background: var(--color-offline-dim); color: var(--color-error); }

.sbw-actions { display: flex; gap: var(--space-3); margin-top: var(--space-3); }

/* Confirm */
.sbw-confirm {
  display: flex; flex-direction: column; gap: var(--space-3);
  padding: var(--space-4);
  background: color-mix(in oklch, var(--color-error) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 30%, transparent);
  border-radius: var(--radius-md);
  margin-top: var(--space-3);
}
.sbw-confirm-icon { font-size: 1.2rem; color: var(--color-error); }
.sbw-confirm-body strong { font-weight: 700; color: var(--color-text); }
.sbw-confirm-body p { font-size: var(--text-xs); color: var(--color-text-muted); margin: var(--space-1) 0 0; line-height: 1.5; }
.sbw-confirm-body code { font-family: var(--font-mono); font-size: 0.85em; background: var(--color-surface-3); border-radius: 3px; padding: 1px 4px; color: var(--color-primary); }
.sbw-confirm-btns { display: flex; gap: var(--space-2); }

/* Running */
.sbw-running { display: flex; flex-direction: column; gap: var(--space-3); }
.sbw-running-header { display: flex; align-items: center; gap: var(--space-3); font-size: var(--text-sm); font-weight: 600; color: var(--color-primary); }
.sbw-running-header .pi-spinner { font-size: 1rem; }

/* Log */
.sbw-log {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  max-height: 300px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 4px;
}
.sbw-log--done { max-height: 200px; }
.sbw-log-line { display: flex; gap: var(--space-3); }
.sbw-log-idx  { color: var(--color-text-faint); min-width: 28px; }
.sbw-log-msg  { color: var(--color-text-muted); word-break: break-word; }
.sbw-log-waiting { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-faint); }
.sbw-log-waiting .pi { font-size: 0.6rem; }

/* Done */
.sbw-done { display: flex; flex-direction: column; align-items: center; gap: var(--space-4); padding: var(--space-6) 0; }
.sbw-done-icon { width: 72px; height: 72px; border-radius: var(--radius-full); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; }
.sbw-done--ok { background: var(--color-synced-dim); color: var(--color-synced); }
.sbw-done--err { background: var(--color-offline-dim); color: var(--color-error); }
.sbw-done-msg { font-size: var(--text-sm); color: var(--color-text-muted); text-align: center; }
</style>
