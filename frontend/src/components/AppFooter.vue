<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useOperationsStore } from '@/stores/operations'
import { useClusterStore }    from '@/stores/cluster'
import { useVersionStore }    from '@/stores/version'

const opsStore     = useOperationsStore()
const clusterStore = useClusterStore()
const versionStore = useVersionStore()

const clusterId = computed(() => clusterStore.selectedCluster?.id ?? 0)

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

// ── Auto-dismiss finished op after 10s ───────────────────────────────────────────────
const finishedVisible = ref(false)
let dismissTimer: ReturnType<typeof setTimeout> | null = null

watch(isFinished, (val) => {
  if (val) {
    finishedVisible.value = true
    dismissTimer = setTimeout(() => { finishedVisible.value = false }, 10_000)
  }
})
watch(isRunning, (val) => {
  if (val) {
    finishedVisible.value = false
    if (dismissTimer) { clearTimeout(dismissTimer); dismissTimer = null }
  }
})
onUnmounted(() => { if (dismissTimer) clearTimeout(dismissTimer) })

// ── Live local clock ───────────────────────────────────────────────────────────────────
const nowStr = ref('')
let clockTimer: ReturnType<typeof setInterval> | null = null

function tick() {
  const d = new Date()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  nowStr.value = `${hh}:${mm}:${ss}`
}
onMounted(() => { tick(); clockTimer = setInterval(tick, 1000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

// ── Op labels ──────────────────────────────────────────────────────────────────────────
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

const opTypeLabel   = computed(() => OP_LABELS[activeOp.value?.type ?? ''] ?? activeOp.value?.type ?? '')
const opStatusLabel = computed(() => STATUS_LABEL[activeOp.value?.status ?? ''] ?? activeOp.value?.status ?? '')

// ── Elapsed timer ──────────────────────────────────────────────────────────────────────
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

// ── Version & update check ────────────────────────────────────────────────────────────
onMounted(async () => {
  await versionStore.loadVersion()
  // Fire-and-forget, runs in background, never blocks UI
  versionStore.checkUpdate()
})

const showUpdateBadge = computed(() => versionStore.updateAvailable)
</script>

<template>
  <footer class="app-footer">

    <!-- LEFT: current version + update badge -->
    <div class="footer-left">
      <span class="footer-version">{{ versionStore.currentVersion }}</span>
      <Transition name="fade-badge">
        <span
          v-if="showUpdateBadge"
          class="update-badge"
          title="New version available — pull the latest image to update"
        >
          ↑ update
        </span>
      </Transition>
    </div>

    <!-- CENTER: op status -->
    <div class="footer-center">

      <!-- Running op -->
      <template v-if="isRunning && activeOp">
        <span class="op-dot op-dot--running" />
        <span class="op-type">{{ opTypeLabel }}</span>
        <span class="op-sep">/</span>
        <span class="op-status">{{ opStatusLabel }}</span>
        <span v-if="elapsedStr" class="op-elapsed">{{ elapsedStr }}</span>
      </template>

      <!-- Finished op (auto-dismiss in 10s) -->
      <Transition name="fade-op">
        <template v-if="isFinished && activeOp && finishedVisible">
          <div class="finished-row">
            <span :class="['op-dot', activeOp.status === 'success' ? 'op-dot--success' : 'op-dot--error']" />
            <span class="op-type">{{ opTypeLabel }}</span>
            <span class="op-sep">/</span>
            <span :class="['op-status', activeOp.status === 'success' ? 'op-status--ok' : 'op-status--err']">
              {{ opStatusLabel }}
            </span>
          </div>
        </template>
      </Transition>

      <!-- Idle -->
      <template v-if="!isRunning && !finishedVisible">
        <span class="idle-dot" />
        <span class="idle-text">idle</span>
      </template>

    </div>

    <!-- RIGHT: clock -->
    <div class="footer-right">
      <span class="footer-clock">{{ nowStr }}</span>
    </div>

  </footer>
</template>

<style scoped>
.app-footer {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  border-top: 1px solid rgba(255,255,255,0.05);
  flex-shrink: 0;
  background: #0a0b0e;
  gap: var(--space-4);
  user-select: none;
}

/* ── Left ── */
.footer-left {
  flex-shrink: 0;
  min-width: 80px;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.footer-version {
  font-size: 0.72rem;
  font-family: var(--font-mono, monospace);
  color: #3f3f46;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  transition: color 300ms ease;
}
.footer-version:hover { color: #71717a; }

.update-badge {
  font-size: 0.68rem;
  font-family: var(--font-mono, monospace);
  font-weight: 600;
  color: #2dd4bf;
  background: rgba(45, 212, 191, 0.1);
  border: 1px solid rgba(45, 212, 191, 0.25);
  border-radius: 4px;
  padding: 1px 6px;
  letter-spacing: 0.04em;
  cursor: default;
  white-space: nowrap;
  animation: badge-glow 3s ease-in-out infinite;
}

@keyframes badge-glow {
  0%, 100% { box-shadow: 0 0 4px rgba(45,212,191,0.2); }
  50%       { box-shadow: 0 0 8px rgba(45,212,191,0.5); }
}

.fade-badge-enter-active { transition: opacity 500ms ease, transform 500ms ease; }
.fade-badge-leave-active { transition: opacity 300ms ease; }
.fade-badge-enter-from   { opacity: 0; transform: translateY(4px); }
.fade-badge-leave-to     { opacity: 0; }

/* ── Center ── */
.footer-center {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  justify-content: center;
  min-width: 0;
  position: relative;
}

.finished-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.op-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.op-dot--running {
  background: #2dd4bf;
  box-shadow: 0 0 7px rgba(45,212,191,0.75);
  animation: blink 2.4s ease-in-out infinite;
}
.op-dot--success {
  background: #4ade80;
  box-shadow: 0 0 6px rgba(74,222,128,0.55);
}
.op-dot--error {
  background: #f87171;
  box-shadow: 0 0 6px rgba(248,113,113,0.55);
}
@keyframes blink {
  0%, 100% { opacity: 1;    box-shadow: 0 0 7px rgba(45,212,191,0.75); }
  50%       { opacity: 0.35; box-shadow: 0 0 2px rgba(45,212,191,0.2);  }
}

.op-type   { font-size: 0.78rem; color: #71717a; font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-sep    { font-size: 0.78rem; color: #3f3f46; }
.op-status { font-size: 0.78rem; color: #2dd4bf; font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-status--ok  { color: #4ade80; }
.op-status--err { color: #f87171; }

.op-elapsed {
  font-size: 0.72rem;
  color: #71717a;
  font-family: var(--font-mono, monospace);
  background: rgba(255,255,255,0.05);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.idle-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #27272a;
  box-shadow: 0 0 0 1.5px #3f3f46;
  opacity: 0.6;
}
.idle-text {
  font-size: 0.78rem;
  color: #3f3f46;
  letter-spacing: 0.06em;
  font-family: var(--font-mono, monospace);
}

.fade-op-enter-active { transition: opacity 400ms ease; }
.fade-op-leave-active { transition: opacity 600ms ease; }
.fade-op-enter-from, .fade-op-leave-to { opacity: 0; }

/* ── Right ── */
.footer-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  min-width: 80px;
  justify-content: flex-end;
}

.footer-clock {
  font-size: 0.82rem;
  font-family: var(--font-mono, monospace);
  font-weight: 500;
  color: #52525b;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  transition: color 300ms ease;
}
.footer-clock:hover { color: #a1a1aa; }
</style>
