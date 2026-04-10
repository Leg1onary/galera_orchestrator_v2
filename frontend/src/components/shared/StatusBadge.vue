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
}

.status-badge--healthy  { background: var(--color-success-highlight); color: var(--color-success); }
.status-badge--synced   { background: var(--color-success-highlight); color: var(--color-success); }
.status-badge--degraded { background: var(--color-gold-highlight);    color: var(--color-gold); }
.status-badge--donor    { background: var(--color-gold-highlight);    color: var(--color-gold); }
.status-badge--joining  { background: var(--color-blue-highlight);    color: var(--color-blue); }
.status-badge--critical { background: var(--color-error-highlight);   color: var(--color-error); }
.status-badge--offline  { background: var(--color-error-highlight);   color: var(--color-error); }
.status-badge--unknown  { background: var(--color-surface-offset);    color: var(--color-text-muted); }
</style>
