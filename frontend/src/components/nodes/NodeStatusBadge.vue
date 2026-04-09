<!-- ТЗ раздел 9.3: 5 цветовых состояний нод -->
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

type StatusKey = 'synced' | 'donor' | 'joining' | 'error' | 'offline'

const statusMap: Record<string, StatusKey> = {
  Synced: 'synced',
  'Donor/Desynced': 'donor',
  Joining: 'joining',
  'Joined': 'joining',
}

const status = computed((): StatusKey => {
  if (!props.node.wsrep_connected || !props.node.last_seen) return 'offline'
  const s = props.node.wsrep_local_state_comment
  if (!s) return 'offline'
  return statusMap[s] ?? 'error'
})

const label = computed(() => {
  if (status.value === 'offline') return 'Offline'
  return props.node.wsrep_local_state_comment ?? 'Unknown'
})

const badgeClass = computed(() => ({
  'badge--synced': status.value === 'synced',
  'badge--donor':  status.value === 'donor',
  'badge--joining': status.value === 'joining',
  'badge--error':  status.value === 'error',
  'badge--offline': status.value === 'offline',
}))
</script>

<style scoped>
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
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.badge--synced  { background: color-mix(in oklch, var(--color-success) 15%, transparent); color: var(--color-success); }
.badge--synced .status-dot { background: var(--color-success); }

.badge--donor   { background: color-mix(in oklch, var(--color-blue) 15%, transparent); color: var(--color-blue); }
.badge--donor .status-dot { background: var(--color-blue); }

.badge--joining { background: color-mix(in oklch, var(--color-gold) 15%, transparent); color: var(--color-gold); }
.badge--joining .status-dot { background: var(--color-gold); animation: pulse 1.2s ease-in-out infinite; }

.badge--error   { background: color-mix(in oklch, var(--color-error) 15%, transparent); color: var(--color-error); }
.badge--error .status-dot { background: var(--color-error); }

.badge--offline { background: color-mix(in oklch, var(--color-text-faint) 20%, transparent); color: var(--color-text-muted); }
.badge--offline .status-dot { background: var(--color-text-faint); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>