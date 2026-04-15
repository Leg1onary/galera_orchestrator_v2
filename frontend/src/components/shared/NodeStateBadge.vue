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
  border: 1px solid transparent;
}

.node-state-badge--synced  {
  background: var(--color-synced-dim);
  color: var(--color-synced);
  border-color: rgba(74, 222, 128, 0.2);
}
.node-state-badge--donor   {
  background: var(--color-donor-dim);
  color: var(--color-donor);
  border-color: rgba(96, 165, 250, 0.2);
}
.node-state-badge--joining {
  background: var(--color-donor-dim);
  color: var(--color-donor);
  border-color: rgba(96, 165, 250, 0.2);
}
.node-state-badge--offline {
  background: var(--color-offline-dim);
  color: var(--color-offline);
  border-color: rgba(248, 113, 113, 0.2);
}
.node-state-badge--unknown {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-faint);
  border-color: rgba(255, 255, 255, 0.07);
}
</style>
