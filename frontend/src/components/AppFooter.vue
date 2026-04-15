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

// ── Auto-dismiss finished op after 10s ────────────────────────────────────────
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

// ── Live local clock ──────────────────────────────────────────────────────────
const nowStr    = ref('')
const nowUTCStr = ref('')
let clockTimer: ReturnType<typeof setInterval> | null = null

function tick() {
  const d  = new Date()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  nowStr.value = `${hh}:${mm}:${ss}`
  // UTC для tooltip
  const uh = String(d.getUTCHours()).padStart(2, '0')
  const um = String(d.getUTCMinutes()).padStart(2, '0')
  const us = String(d.getUTCSeconds()).padStart(2, '0')
  nowUTCStr.value = `UTC ${uh}:${um}:${us}`
}
onMounted(() => { tick(); clockTimer = setInterval(tick, 1000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

// ── Op labels ─────────────────────────────────────────────────────────────────
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

// ── Elapsed timer ─────────────────────────────────────────────────────────────
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

// version loadVersion вызываем здесь — один раз для всего приложения
onMounted(() => versionStore.loadVersion())
</script>

<template>
  <footer class="app-footer">

    <!-- LEFT: idle / пустое место (версия переехала в sidebar) -->
    <div class="footer-left">
      <!-- зарезервировано для будущих элементов (event-log shortcut и т.п.) -->
    </div>

    <!-- CENTER: op status -->
    <div class="footer-center">

      <template v-if="isRunning && activeOp">
        <span class="op-dot op-dot--running" />
        <span class="op-type">{{ opTypeLabel }}</span>
        <span class="op-sep">/</span>
        <span class="op-status">{{ opStatusLabel }}</span>
        <span v-if="elapsedStr" class="op-elapsed">{{ elapsedStr }}</span>
      </template>

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

      <template v-if="!isRunning && !finishedVisible">
        <span class="idle-dot" />
        <span class="idle-text">idle</span>
      </template>

    </div>

    <!-- RIGHT: clock (local + UTC tooltip) -->
    <div class="footer-right">
      <span
        class="footer-clock"
        v-tooltip.top="nowUTCStr"
      >{{ nowStr }}</span>
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
  background: var(--color-bg);
  gap: var(--space-4);
  user-select: none;
}

/* ── Left ── */
.footer-left {
  flex-shrink: 0;
  min-width: 80px;
}

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

.finished-row { display: flex; align-items: center; gap: var(--space-2); }

.op-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.op-dot--running {
  background: var(--color-synced);
  box-shadow: 0 0 7px color-mix(in oklch, var(--color-synced) 75%, transparent);
  animation: blink 2.4s ease-in-out infinite;
}
.op-dot--success { background: var(--color-success); box-shadow: 0 0 6px color-mix(in oklch, var(--color-success) 55%, transparent); }
.op-dot--error   { background: var(--color-offline);  box-shadow: 0 0 6px color-mix(in oklch, var(--color-offline) 55%, transparent); }

@keyframes blink {
  0%, 100% { opacity: 1;    box-shadow: 0 0 7px color-mix(in oklch, var(--color-synced) 75%, transparent); }
  50%       { opacity: 0.35; box-shadow: 0 0 2px color-mix(in oklch, var(--color-synced) 20%, transparent); }
}

.op-type   { font-size: 0.78rem; color: var(--color-text-muted); font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-sep    { font-size: 0.78rem; color: var(--color-text-faint); }
.op-status { font-size: 0.78rem; color: var(--color-synced); font-family: var(--font-mono, monospace); white-space: nowrap; }
.op-status--ok  { color: var(--color-success); }
.op-status--err { color: var(--color-offline); }

.op-elapsed {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-family: var(--font-mono, monospace);
  background: rgba(255,255,255,0.05);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.idle-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--color-surface-3);
  box-shadow: 0 0 0 1.5px var(--color-text-faint);
  opacity: 0.6;
}
.idle-text {
  font-size: 0.78rem;
  color: var(--color-text-faint);
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
  color: var(--color-text-faint);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  transition: color 300ms ease;
  cursor: default;
}
.footer-clock:hover { color: var(--color-text-muted); }
</style>
