<script setup lang="ts">
/**
 * #9 Full Cluster Recovery
 * Поочерёдный rejoin всех нод кластера через единую операцию на бэкенде.
 * Бэкенд сам определяет порядок (bootstrap-нода → остальные) и транслирует
 * прогресс через WS operation_progress / operation_finished events.
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import Button  from 'primevue/button'
import Message from 'primevue/message'
import Tag     from 'primevue/tag'
import { useClusterStore } from '@/stores/cluster'
import { useWsStore, type WsEvent } from '@/stores/ws'
import { recoveryAdvancedApi, type FullClusterRecoveryResponse } from '@/api/recovery-advanced'

/* ─────── types ─────── */
type Phase = 'idle' | 'running' | 'done' | 'error'

interface ProgressEntry {
  ts: string
  msg: string
  level: 'info' | 'warn' | 'error' | 'success'
}

/* ─────── state ─────── */
const clusterStore = useClusterStore()
const wsStore      = useWsStore()

const phase       = ref<Phase>('idle')
const operationId = ref<string | null>(null)
const progress    = ref<ProgressEntry[]>([])
const resultData  = ref<FullClusterRecoveryResponse | null>(null)
const errorMsg    = ref<string | null>(null)
const confirmed   = ref(false)

/* ─────── WS listener ─────── */
let unsubWs: (() => void) | null = null

function subscribeWs() {
  unsubWs = wsStore.on((event: WsEvent) => {
    if (event.event === 'operation_progress') {
      const p = event.payload as Record<string, unknown>
      if (operationId.value && p['operation_id'] !== operationId.value) return
      progress.value.push({
        ts:    event.ts,
        msg:   String(p['message'] ?? ''),
        level: (p['level'] as ProgressEntry['level']) ?? 'info',
      })
      scrollLog()
    }
    if (event.event === 'operation_finished') {
      const p = event.payload as Record<string, unknown>
      if (operationId.value && p['operation_id'] !== operationId.value) return
      const ok = p['success'] === true
      phase.value = ok ? 'done' : 'error'
      if (!ok) errorMsg.value = String(p['error'] ?? 'Unknown error')
      progress.value.push({
        ts:    event.ts,
        msg:   ok ? '✓ Full cluster recovery completed successfully' : `✗ ${errorMsg.value}`,
        level: ok ? 'success' : 'error',
      })
      scrollLog()
    }
  })
}

onMounted(() => {
  subscribeWs()
  restorePhase()
})
onUnmounted(() => { if (unsubWs) unsubWs() })

/**
 * Restore running phase after page reload.
 * Queries active_operation on the selected cluster: if it's a full-cluster
 * recovery still running, show the progress log instead of idle form.
 */
async function restorePhase() {
  const clusterId = clusterStore.selectedClusterId
  if (!clusterId) return
  try {
    const { data } = await import('@/api/client').then(m => m.api.get(`/api/clusters/${clusterId}/operations/active`))
    const op = data?.operation
    if (
      op &&
      op.type === 'recovery_full_cluster' &&
      ['pending', 'running', 'cancel_requested'].includes(op.status)
    ) {
      phase.value       = 'running'
      operationId.value = String(op.id)
      progress.value    = [{
        ts:    new Date().toISOString(),
        msg:   `↺ Session restored — operation #${op.id} is still running. Waiting for completion…`,
        level: 'warn',
      }]
    }
  } catch {
    // Ignore — if we can't check, just show idle
  }
}

// Also restore phase when cluster changes
watch(() => clusterStore.selectedClusterId, () => {
  if (phase.value === 'idle') restorePhase()
})

/* ─────── actions ─────── */
async function startRecovery() {
  if (!clusterStore.selectedClusterId) return
  phase.value     = 'running'
  errorMsg.value  = null
  operationId.value = null
  progress.value  = []
  progress.value.push({
    ts:    new Date().toISOString(),
    msg:   '→ Initiating full cluster recovery sequence…',
    level: 'info',
  })
  try {
    const res = await recoveryAdvancedApi.startFullClusterRecovery(clusterStore.selectedClusterId)
    operationId.value = String(res.operation_id)
    resultData.value  = res as FullClusterRecoveryResponse
    const orderStr = res.node_order ? `order: [${res.node_order.join(' → ')}]` : ''
    progress.value.push({
      ts:    new Date().toISOString(),
      msg:   `Operation #${res.operation_id} started. Bootstrap: ${res.bootstrap_node ?? 'auto'} ${orderStr}`,
      level: 'info',
    })
  } catch (e: unknown) {
    phase.value    = 'error'
    errorMsg.value = (e as Error)?.message ?? 'Request failed'
    progress.value.push({
      ts:    new Date().toISOString(),
      msg:   `✗ ${errorMsg.value}`,
      level: 'error',
    })
  }
}

function reset() {
  phase.value       = 'idle'
  operationId.value = null
  progress.value    = []
  resultData.value  = null
  errorMsg.value    = null
  confirmed.value   = false
}

/* ─────── log scroll ─────── */
const logEl = ref<HTMLElement | null>(null)
function scrollLog() {
  setTimeout(() => {
    if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
  }, 40)
}

/* ─────── helpers ─────── */
function levelClass(level: ProgressEntry['level']) {
  return {
    info:    'log-info',
    warn:    'log-warn',
    error:   'log-error',
    success: 'log-success',
  }[level]
}

function formatTs(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString('en-GB', { hour12: false })
  } catch { return iso }
}
</script>

<template>
  <div class="fcr-panel">

    <!-- Header -->
    <div class="fcr-header">
      <div class="fcr-header-icon">
        <i class="pi pi-refresh" />
      </div>
      <div class="fcr-header-meta">
        <span class="fcr-title">Full Cluster Recovery</span>
        <span class="fcr-subtitle">
          Автоматически определяет bootstrap-ноду по seqno, поднимает её первой,
          затем поочерёдно подключает все остальные ноды.
        </span>
      </div>
      <Tag
        v-if="phase !== 'idle'"
        :value="phase === 'running' ? 'Running' : phase === 'done' ? 'Done' : 'Failed'"
        :severity="phase === 'running' ? 'warn' : phase === 'done' ? 'success' : 'danger'"
        class="fcr-phase-tag"
      />
    </div>

    <!-- Warning banner (idle only) -->
    <div v-if="phase === 'idle'" class="fcr-warning">
      <div class="fcr-warn-icon"><i class="pi pi-exclamation-triangle" /></div>
      <div class="fcr-warn-body">
        <strong>Destructive operation</strong>
        <p>
          Full Cluster Recovery restarts the entire cluster.
          Make sure <em>all nodes</em> are stopped.
        </p>
      </div>
    </div>

    <!-- Idle: confirm + launch -->
    <div v-if="phase === 'idle'" class="fcr-idle">

      <!-- Checklist -->
      <div class="fcr-checklist">
        <div class="fcr-cl-title">Pre-flight check</div>
        <label class="fcr-check-item">
          <input type="checkbox" v-model="confirmed" />
          <span>I understand that this operation will restart the entire cluster and may lead to data loss if misconfigured</span>
        </label>
      </div>

      <div class="fcr-idle-actions">
        <Button
          label="Start Full Cluster Recovery"
          icon="pi pi-refresh"
          severity="danger"
          :disabled="!clusterStore.selectedClusterId || !confirmed"
          @click="startRecovery"
        />
      </div>
    </div>

    <!-- Running / Done / Error: log -->
    <div v-if="phase !== 'idle'" class="fcr-log-wrap">

      <!-- Operation ID badge -->
      <div v-if="operationId" class="fcr-op-id">
        <i class="pi pi-hashtag" />
        <span>{{ operationId }}</span>
      </div>

      <!-- Log terminal -->
      <div ref="logEl" class="fcr-log">
        <div
          v-for="(entry, i) in progress"
          :key="i"
          class="fcr-log-line"
          :class="levelClass(entry.level)"
        >
          <span class="log-ts">{{ formatTs(entry.ts) }}</span>
          <span class="log-msg">{{ entry.msg }}</span>
        </div>
        <div v-if="phase === 'running'" class="fcr-log-line log-info fcr-cursor">
          <span class="log-ts">—</span>
          <span class="log-msg">Waiting for progress events…<span class="blink">_</span></span>
        </div>
      </div>

      <!-- Success result -->
      <div v-if="phase === 'done'" class="fcr-result fcr-result--success">
        <i class="pi pi-check-circle" />
        <div class="fcr-result-body">
          <strong>Cluster fully recovered</strong>
          <span v-if="resultData?.bootstrap_node">
            Bootstrap node: <code>{{ resultData.bootstrap_node }}</code>
          </span>
        </div>
      </div>

      <!-- Error result -->
      <Message v-if="phase === 'error' && errorMsg" severity="error" :closable="false" class="fcr-err-msg">
        {{ errorMsg }}
      </Message>

      <!-- Actions after finish -->
      <div v-if="phase === 'done' || phase === 'error'" class="fcr-finish-actions">
        <Button
          label="Reset"
          icon="pi pi-refresh"
          severity="secondary"
          outlined
          @click="reset"
        />
      </div>
    </div>

  </div>
</template>

<style scoped>
.fcr-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* Header */
.fcr-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
}
.fcr-header-icon {
  width: 40px; height: 40px; flex-shrink: 0;
  border-radius: var(--radius-md);
  background: rgba(248, 113, 113, 0.12);
  border: 1px solid rgba(248, 113, 113, 0.22);
  display: flex; align-items: center; justify-content: center;
  color: var(--color-error);
  font-size: 1rem;
}
.fcr-header-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.fcr-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}
.fcr-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
}
.fcr-phase-tag { flex-shrink: 0; }

/* Warning */
.fcr-warning {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: rgba(251, 191, 36, 0.06);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: var(--radius-lg);
}
.fcr-warn-icon {
  color: var(--color-warning);
  font-size: 1rem;
  margin-top: 2px;
  flex-shrink: 0;
}
.fcr-warn-body {
  display: flex; flex-direction: column; gap: var(--space-2);
}
.fcr-warn-body strong {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-warning);
}
.fcr-warn-body p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
}
.fcr-warn-body em { font-style: normal; font-weight: 600; color: var(--color-text); }
.fcr-warn-body strong:last-of-type { color: var(--color-error); }

/* Idle */
.fcr-idle {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.fcr-checklist {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.fcr-cl-title {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
}
.fcr-check-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}
.fcr-check-item input[type=checkbox] {
  margin-top: 2px;
  flex-shrink: 0;
  accent-color: var(--color-error);
  width: 15px; height: 15px;
  cursor: pointer;
}
.fcr-idle-actions {
  display: flex;
  gap: var(--space-3);
}

/* Log */
.fcr-log-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.fcr-op-id {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-family: var(--font-mono, monospace);
}
.fcr-op-id .pi { font-size: 0.65rem; }

.fcr-log {
  background: #0a0b0e;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  font-family: var(--font-mono, 'Fira Mono', monospace);
  font-size: 0.75rem;
  line-height: 1.6;
  min-height: 200px;
  max-height: 340px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fcr-log-line {
  display: flex;
  gap: var(--space-3);
  align-items: baseline;
}
.log-ts {
  flex-shrink: 0;
  color: #4a5568;
  font-size: 0.7rem;
  width: 7ch;
}
.log-msg { word-break: break-word; }

/* Log level colours */
.log-info    .log-msg { color: #8b949e; }
.log-warn    .log-msg { color: #fbbf24; }
.log-error   .log-msg { color: #f87171; }
.log-success .log-msg { color: #4ade80; }

.blink {
  animation: fcr-blink 1s step-end infinite;
}
@keyframes fcr-blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* Result */
.fcr-result {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
}
.fcr-result--success {
  background: rgba(74, 222, 128, 0.07);
  border: 1px solid rgba(74, 222, 128, 0.22);
  color: var(--color-synced);
}
.fcr-result .pi { font-size: 1.1rem; margin-top: 1px; flex-shrink: 0; }
.fcr-result-body {
  display: flex; flex-direction: column; gap: 4px;
}
.fcr-result-body strong { font-size: var(--text-sm); font-weight: 700; }
.fcr-result-body span   { font-size: var(--text-xs); color: var(--color-text-muted); }
.fcr-result-body code {
  font-family: var(--font-mono, monospace);
  font-size: 0.75em;
  background: rgba(45,212,191,0.1);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  color: var(--color-primary);
}

.fcr-err-msg { width: 100%; }

.fcr-finish-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
}

/* Scrollbar */
.fcr-log::-webkit-scrollbar        { width: 5px; }
.fcr-log::-webkit-scrollbar-track  { background: transparent; }
.fcr-log::-webkit-scrollbar-thumb  { background: var(--color-border); border-radius: 3px; }
</style>
