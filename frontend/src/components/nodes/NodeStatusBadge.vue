<!-- src/components/nodes/NodeStatusBadge.vue -->
<!-- ТЗ п.7.3: 5 цветовых состояний нод -->
<template>
  <span class="node-status-badge" :class="badgeClass">
    <span class="status-dot" />
    <span class="status-label">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NodeListItem } from '@/api/nodes'

const props = defineProps<{ node: NodeListItem }>()

// ТЗ п.7.3: 5 состояний
type StatusKey =
    | 'synced'        // SYNCED, RW           → #22c55e
    | 'synced-ro'     // SYNCED + readonly=1  → #eab308
    | 'transitioning' // DONOR / JOINER / DESYNCED → #38bdf8
    | 'not-ready'     // wsrep_ready=OFF      → #f97316
    | 'offline'       // SSH/MariaDB down     → #ef4444

// BLOCKER fix: uppercase ключи — именно так MariaDB отдаёт wsrep_local_state_comment
const STATE_MAP: Record<string, StatusKey> = {
  SYNCED:   'synced',
  DONOR:    'transitioning',
  JOINER:   'transitioning',
  DESYNCED: 'transitioning', // BLOCKER fix: DESYNCED был не обработан
}

const status = computed((): StatusKey => {
  const n = props.node

  // OFFLINE: нет данных или нода не отвечает (ТЗ п.7.3: SSH/MariaDB down)
  // BLOCKER fix: last_check_ts вместо last_seen
  if (!n.last_check_ts || !n.wsrep_local_state_comment) return 'offline'

  const stateKey = STATE_MAP[n.wsrep_local_state_comment]

  // wsrep_ready=OFF → orange (ТЗ п.7.3, MAJOR fix)
  if (n.wsrep_ready === false) return 'not-ready'

  if (!stateKey) return 'offline'

  // SYNCED + readonly → yellow (ТЗ п.7.3, MAJOR fix)
  if (stateKey === 'synced' && n.read_only) return 'synced-ro'

  return stateKey
})

const label = computed((): string => {
  if (status.value === 'offline') return 'Offline'
  if (status.value === 'synced-ro') return 'Read-only'
  if (status.value === 'not-ready') return 'Not ready'
  // Возвращаем оригинальное значение из MariaDB
  return props.node.wsrep_local_state_comment ?? 'Unknown'
})

const badgeClass = computed(() => ({
  'badge--synced':       status.value === 'synced',
  'badge--synced-ro':    status.value === 'synced-ro',
  'badge--transitioning': status.value === 'transitioning',
  'badge--not-ready':    status.value === 'not-ready',
  'badge--offline':      status.value === 'offline',
}))
</script>

<style scoped>
/*
  Цвета строго по ТЗ п.7.3:
  SYNCED           → #22c55e  (≈ --color-success)
  DONOR/JOINER/DESYNCED → #38bdf8  (sky — нет в Nexus-токенах → локальная переменная)
  SYNCED + RO      → #eab308  (≈ --color-gold в light / dark)
  wsrep_ready=OFF  → #f97316  (≈ --color-orange)
  OFFLINE          → #ef4444  (≈ --color-notification)
*/

:host, .node-status-badge {
  /* Локальные цвета статусов по ТЗ — не переопределяют дизайн-систему,
     используются только внутри этого компонента */
  --status-synced:       var(--color-success);
  --status-synced-ro:    var(--color-gold);
  --status-transitioning: #38bdf8; /* sky — ТЗ п.7.3 хардкод */
  --status-not-ready:    var(--color-orange);
  --status-offline:      var(--color-notification);
}

.node-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: var(--text-xs);
  font-weight: 500;
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── SYNCED ─────────────────────────────── #22c55e */
.badge--synced {
  background: color-mix(in oklch, var(--status-synced) 15%, transparent);
  color: var(--status-synced);
}
.badge--synced .status-dot {
  background: var(--status-synced);
}

/* ── SYNCED + Read-only ─────────────────── #eab308 */
.badge--synced-ro {
  background: color-mix(in oklch, var(--status-synced-ro) 15%, transparent);
  color: var(--status-synced-ro);
}
.badge--synced-ro .status-dot {
  background: var(--status-synced-ro);
}

/* ── DONOR / JOINER / DESYNCED ─────────── #38bdf8 */
.badge--transitioning {
  background: color-mix(in oklch, var(--status-transitioning) 15%, transparent);
  color: var(--status-transitioning);
}
.badge--transitioning .status-dot {
  background: var(--status-transitioning);
  animation: pulse 1.2s ease-in-out infinite;
}

/* ── wsrep_ready = OFF ──────────────────── #f97316 */
.badge--not-ready {
  background: color-mix(in oklch, var(--status-not-ready) 15%, transparent);
  color: var(--status-not-ready);
}
.badge--not-ready .status-dot {
  background: var(--status-not-ready);
  animation: pulse 1.2s ease-in-out infinite;
}

/* ── OFFLINE ────────────────────────────── #ef4444 */
.badge--offline {
  background: color-mix(in oklch, var(--status-offline) 15%, transparent);
  color: var(--status-offline);
}
.badge--offline .status-dot {
  background: var(--status-offline);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
</style>