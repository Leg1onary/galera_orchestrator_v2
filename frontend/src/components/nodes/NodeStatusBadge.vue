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
    | 'synced'
    | 'synced-ro'
    | 'transitioning'
    | 'not-ready'
    | 'offline'

// Бэкенд возвращает wsrep_local_state_comment как "Synced", "Donor", "Joiner", "Desynced" —
// нормализуем к uppercase перед поиском, чтобы не зависеть от регистра.
const STATE_MAP: Record<string, StatusKey> = {
  SYNCED:   'synced',
  DONOR:    'transitioning',
  JOINER:   'transitioning',
  DESYNCED: 'transitioning',
}

const status = computed((): StatusKey => {
  const n = props.node
  const live = n.live

  // Нет live-данных → offline
  if (!live || !live.last_check_ts || !live.wsrep_local_state_comment) return 'offline'

  // ssh/db недоступны → offline
  if (!live.ssh_ok || !live.db_ok) return 'offline'

  // wsrep_ready = OFF → not-ready (orange)
  if (live.wsrep_ready === 'OFF') return 'not-ready'

  // Нормализация: "Synced" → "SYNCED", "Donor/STD" → "DONOR"
  const stateRaw = live.wsrep_local_state_comment.toUpperCase().split('/')[0].trim()
  const stateKey = STATE_MAP[stateRaw]
  if (!stateKey) return 'offline'

  // SYNCED + readonly → synced-ro (yellow)
  if (stateKey === 'synced' && live.readonly) return 'synced-ro'

  return stateKey
})

const label = computed((): string => {
  const live = props.node.live
  if (status.value === 'offline')      return 'Offline'
  if (status.value === 'synced-ro')    return 'Read-only'
  if (status.value === 'not-ready')    return 'Not ready'
  return live?.wsrep_local_state_comment ?? 'Unknown'
})

const badgeClass = computed(() => ({
  'badge--synced':        status.value === 'synced',
  'badge--synced-ro':     status.value === 'synced-ro',
  'badge--transitioning': status.value === 'transitioning',
  'badge--not-ready':     status.value === 'not-ready',
  'badge--offline':       status.value === 'offline',
}))
</script>

<style scoped>
:host, .node-status-badge {
  --status-synced:        var(--color-success);
  --status-synced-ro:     var(--color-gold);
  --status-transitioning: #38bdf8;
  --status-not-ready:     var(--color-orange);
  --status-offline:       var(--color-notification);
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

.badge--synced {
  background: color-mix(in oklch, var(--status-synced) 15%, transparent);
  color: var(--status-synced);
}
.badge--synced .status-dot { background: var(--status-synced); }

.badge--synced-ro {
  background: color-mix(in oklch, var(--status-synced-ro) 15%, transparent);
  color: var(--status-synced-ro);
}
.badge--synced-ro .status-dot { background: var(--status-synced-ro); }

.badge--transitioning {
  background: color-mix(in oklch, var(--status-transitioning) 15%, transparent);
  color: var(--status-transitioning);
}
.badge--transitioning .status-dot {
  background: var(--status-transitioning);
  animation: pulse 1.2s ease-in-out infinite;
}

.badge--not-ready {
  background: color-mix(in oklch, var(--status-not-ready) 15%, transparent);
  color: var(--status-not-ready);
}
.badge--not-ready .status-dot {
  background: var(--status-not-ready);
  animation: pulse 1.2s ease-in-out infinite;
}

.badge--offline {
  background: color-mix(in oklch, var(--status-offline) 15%, transparent);
  color: var(--status-offline);
}
.badge--offline .status-dot { background: var(--status-offline); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
</style>
