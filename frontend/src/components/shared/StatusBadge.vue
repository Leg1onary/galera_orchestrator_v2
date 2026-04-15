<!--
  StatusBadge — универсальный бэдж статуса кластера/ноды.
  Используется в Recovery Step1Scan и других местах.
-->
<template>
  <span class="status-badge" :class="`status-badge--${variant}`">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type StatusVariant = 'healthy' | 'degraded' | 'critical' | 'unknown' | 'synced' | 'offline' | 'donor' | 'joining'

const props = defineProps<{
  status: string | null | undefined
}>()

// Маппинг строки статуса на визуальный вариант
const VARIANT_MAP: Record<string, StatusVariant> = {
  healthy:      'healthy',
  SYNCED:       'synced',
  Synced:       'synced',
  degraded:     'degraded',
  DONOR:        'donor',
  Donor:        'donor',
  JOINING:      'joining',
  Joining:      'joining',
  JOINER:       'joining',
  critical:     'critical',
  OFFLINE:      'offline',
  Offline:      'offline',
  unknown:      'unknown',
}

const variant = computed((): StatusVariant => {
  if (!props.status) return 'unknown'
  return VARIANT_MAP[props.status] ?? 'unknown'
})

const label = computed(() => props.status ?? '—')
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
  border: 1px solid transparent;
}

.status-badge--healthy,
.status-badge--synced   {
  background: var(--color-synced-dim);
  color: var(--color-synced);
  border-color: rgba(74, 222, 128, 0.2);
}
.status-badge--degraded,
.status-badge--donor    {
  background: var(--color-readonly-dim);
  color: var(--color-readonly);
  border-color: rgba(251, 191, 36, 0.2);
}
.status-badge--joining  {
  background: var(--color-donor-dim);
  color: var(--color-donor);
  border-color: rgba(96, 165, 250, 0.2);
}
.status-badge--critical,
.status-badge--offline  {
  background: var(--color-offline-dim);
  color: var(--color-offline);
  border-color: rgba(248, 113, 113, 0.2);
}
.status-badge--unknown  {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-faint);
  border-color: rgba(255, 255, 255, 0.07);
}
</style>
