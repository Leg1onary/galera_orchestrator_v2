<!--
  NodeStateBadge — бэдж wsrep_local_state_comment ноды.
  Отличается от StatusBadge тем что специфичен для wsrep-состояний.
-->
<template>
  <span class="node-state-badge" :class="`node-state-badge--${variant}`">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type StateVariant = 'synced' | 'donor' | 'joining' | 'offline' | 'unknown'

const props = defineProps<{
  state: string | null | undefined
}>()

const VARIANT_MAP: Record<string, StateVariant> = {
  SYNCED:  'synced',
  Synced:  'synced',
  DONOR:   'donor',
  Donor:   'donor',
  JOINING: 'joining',
  Joining: 'joining',
  JOINER:  'joining',
  OFFLINE: 'offline',
  Offline: 'offline',
}

const variant = computed((): StateVariant => {
  if (!props.state) return 'unknown'
  return VARIANT_MAP[props.state] ?? 'unknown'
})

const label = computed(() => props.state ?? '—')
</script>

<style scoped>
.node-state-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
}

.node-state-badge--synced  { background: var(--color-success-highlight); color: var(--color-success); }
.node-state-badge--donor   { background: var(--color-gold-highlight);    color: var(--color-gold); }
.node-state-badge--joining { background: var(--color-blue-highlight);    color: var(--color-blue); }
.node-state-badge--offline { background: var(--color-error-highlight);   color: var(--color-error); }
.node-state-badge--unknown { background: var(--color-surface-offset);    color: var(--color-text-muted); }
</style>
