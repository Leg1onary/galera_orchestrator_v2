<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useOperationsStore } from '@/stores/operations'
import { useClusterStore }    from '@/stores/cluster'

const opsStore     = useOperationsStore()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.currentCluster?.id ?? 0)

const activeOp = computed(() =>
  clusterId.value ? opsStore.activeOperation(clusterId.value) : null
)

const isRunning = computed(() =>
  activeOp.value != null &&
  ['pending', 'running', 'cancel_requested'].includes(activeOp.value.status)
)

const isFinished = computed(() =>
  activeOp.value != null &&
  ['success', 'failed', 'cancelled'].includes(activeOp.value.status)
)

// ── Live UTC clock ────────────────────────────────────────────────────
const nowStr = ref('')
let clockTimer: ReturnType<typeof setInterval> | null = null

function tick() {
  const d = new Date()
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  const ss = String(d.getUTCSeconds()).padStart(2, '0')
  nowStr.value = `${hh}:${mm}:${ss}`
}

onMounted(() => { tick(); clockTimer = setInterval(tick, 1000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

// ── Op label ─────────────────────────────────────────────────────────
const OP_LABELS: Record<string, string> = {
  'recovery-bootstrap': 'Bootstrap',
  'recovery-rejoin':    'Rejoin',
  'rolling-restart':    'Rolling restart',
  'node-action':        'Node action',
}

const STATUS_LABEL: Record<string, string> = {
  pending:          'queued',
  running:          'running',
  cancel_requested: 'cancelling',
  success:          'done',
  failed:           'failed',
  cancelled:        'cancelled',
}

const opTypeLabel  = computed(() => OP_LABELS[activeOp.value?.type ?? ''] ?? activeOp.value?.type ?? '')
const opStatusLabel = computed(() => STATUS_LABEL[activeOp.value?.status ?? ''] ?? activeOp.value?.status ?? '')

// ── Op elapsed timer ─────────────────────────────────────────────────
const elapsedStr = ref('')
let elapsedTimer: ReturnType<typeof setInterval> | null = null

function updateElapsed() {
  const op = activeOp.value
  if (!op?.started_at || !isRunning.value) { elapsedStr.value = ''; return }
  const sec = Math.floor((Date.now() - new Date(op.started_at).getTime()) / 1000)
  const m = Math.floor(sec / 60)
  const s = sec % 60
  elapsedStr.value = m > 0 ? `${m}m ${s}s` : `${s}s`
}

onMounted(() => { updateElapsed(); elapsedTimer = setInterval(updateElapsed, 1000) })
onUnmounted(() => { if (elapsedTimer) clearInterval(elapsedTimer) })
</script>

<template>
  <footer class="app-footer">

    <!-- LEFT: build info -->
    <div class="footer-left">
      <svg width="13" height="13" viewBox="0 0 22 22" fill="none" aria-hidden="true" class="footer-logo">
        <circle cx="11" cy="11" r="10" stroke="#2dd4bf" stroke-width="1.5" opacity="0.3"/>
        <circle cx="11" cy="11" r="6"  stroke="#2dd4bf" stroke-width="1.5" opacity="0.55"/>
        <circle cx="11" cy="11" r="2.5" fill="#2dd4bf" opacity="0.8"/>
      </svg>
      <span class="footer-brand">Galera Orchestrator</span>
      <span class="footer-version">v2</span>
    </div>

    <!-- CENTER: active operation or idle pulse -->
    <div class="footer-center">

      <!-- Running operation -->
      <template v-if="isRunning && activeOp">
        <span class="op-dot op-dot--running" />
        <span class="op-type">{{ opTypeLabel }}</span>
        <span class="op-sep">/</span>
        <span class="op-status">{{ opStatusLabel }}</span>
        <span v-if="elapsedStr" class="op-elapsed">{{ elapsedStr }}</span>
      </template>

      <!-- Finished operation flash -->
      <template v-else-if="isFinished && activeOp">
        <span :class="['op-dot', activeOp.status === 'success' ? 'op-dot--success' : 'op-dot--error']" />
        <span class="op-type">{{ opTypeLabel }}</span>
        <span class="op-sep">/</span>
        <span :class="['op-status', activeOp.status === 'success' ? 'op-status--ok' : 'op-status--err']">
          {{ opStatusLabel }}
        </span>
      </template>

      <!-- Idle: subtle system heartbeat -->
      <template v-else>
        <span class="idle-dot" />
        <span class="idle-text">system idle</span>
      </template>

    </div>

    <!-- RIGHT: live UTC clock -->
    <div class="footer-right">
      <span class="footer-clock-label">UTC</span>
      <span class="footer-clock">{{ nowStr }}</span>
    </div>

  </footer>
</template>

<style scoped>
/* ── Shell ── */
.app-footer {
  height: var(--footer-height, 32px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  border-top: 1px solid rgba(255,255,255,0.04);
  flex-shrink: 0;
  background: #0a0b0e;
  gap: var(--space-4);
  user-select: none;
}

/* ── Left ── */
.footer-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.footer-logo { opacity: 0.7; flex-shrink: 0; }

.footer-brand {
  font-size: 0.65rem;
  font-weight: 500;
  color: #3f3f46;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.footer-version {
  font-size: 0.6rem;
  font-weight: 700;
  color: #2dd4bf;
  background: rgba(45,212,191,0.08);
  border: 1px solid rgba(45,212,191,0.15);
  border-radius: 3px;
  padding: 1px 4px;
  letter-spacing: 0.04em;
  line-height: 1;
}

/* ── Center ── */
.footer-center {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  justify-content: center;
  min-width: 0;
}

/* Op indicator dot */
.op-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.op-dot--running {
  background: #2dd4bf;
  box-shadow: 0 0 6px rgba(45,212,191,0.7);
  animation: blink 1.2s ease-in-out infinite;
}
.op-dot--success {
  background: #4ade80;
  box-shadow: 0 0 5px rgba(74,222,128,0.5);
}
.op-dot--error {
  background: #f87171;
  box-shadow: 0 0 5px rgba(248,113,113,0.5);
}
@keyframes blink {
  0%, 100% { opacity: 1;   box-shadow: 0 0 6px rgba(45,212,191,0.7); }
  50%       { opacity: 0.4; box-shadow: 0 0 2px rgba(45,212,191,0.2); }
}

.op-type    { font-size: 0.7rem; color: #71717a; font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-sep     { font-size: 0.7rem; color: #3f3f46; }
.op-status  { font-size: 0.7rem; color: #2dd4bf; font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-status--ok  { color: #4ade80; }
.op-status--err { color: #f87171; }
.op-elapsed {
  font-size: 0.65rem;
  color: #52525b;
  font-family: var(--font-mono, monospace);
  background: rgba(255,255,255,0.04);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
}

/* Idle state */
.idle-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #27272a;
  box-shadow: 0 0 0 1px #3f3f46;
  animation: idle-pulse 3s ease-in-out infinite;
}
@keyframes idle-pulse {
  0%, 100% { opacity: 0.5; }
  50%       { opacity: 1; }
}
.idle-text {
  font-size: 0.65rem;
  color: #3f3f46;
  letter-spacing: 0.05em;
  font-family: var(--font-mono, monospace);
}

/* ── Right ── */
.footer-right {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;
}

.footer-clock-label {
  font-size: 0.6rem;
  font-weight: 600;
  color: #3f3f46;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.footer-clock {
  font-size: 0.7rem;
  font-family: var(--font-mono, monospace);
  font-weight: 500;
  color: #52525b;
  letter-spacing: 0.05em;
  /* моноширинные цифры — не скачут при смене секунд */
  font-variant-numeric: tabular-nums;
  transition: color 300ms ease;
}
.footer-clock:hover { color: #71717a; }
</style>
