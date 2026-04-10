<script setup lang="ts">
import Tag from 'primevue/tag'
import { formatTime } from '@/utils/time'

interface ClusterStatus {
  status: 'healthy' | 'degraded' | 'critical'
  online_nodes: number
  total_nodes: number
  wsrep_cluster_size: number
  primary: boolean
  online_arbitrators: number
  total_arbitrators: number
  last_update_ts: string | null
}

const props = defineProps<{
  status: ClusterStatus | null
}>()

function severityForStatus(s: ClusterStatus['status']) {
  if (s === 'healthy') return 'success'
  if (s === 'degraded') return 'warn'   // PrimeVue v4: 'warn' вместо 'warning'
  return 'danger'
}
</script>

<template>
  <div v-if="status" class="summary-bar">
    <div class="summary-item">
      <span class="label">Статус</span>
      <Tag :severity="severityForStatus(status.status)" :value="status.status" />
    </div>
    <div class="summary-item">
      <span class="label">Ноды</span>
      <span class="value">{{ status.online_nodes }} / {{ status.total_nodes }}</span>
    </div>
    <div class="summary-item">
      <span class="label">wsrep_cluster_size</span>
      <span class="value">{{ status.wsrep_cluster_size }}</span>
    </div>
    <div class="summary-item">
      <span class="label">Primary Component</span>
      <Tag
          :severity="status.primary ? 'success' : 'danger'"
          :value="status.primary ? 'Yes' : 'No'"
      />
    </div>
    <div class="summary-item">
      <span class="label">Арбитраторы</span>
      <span class="value">{{ status.online_arbitrators }} / {{ status.total_arbitrators }}</span>
    </div>
    <div class="summary-item">
      <span class="label">Обновлено</span>
      <span class="value ts">{{ status.last_update_ts ? formatTime(status.last_update_ts) : '—' }}</span>
    </div>
  </div>
</template>

<style scoped>
.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.summary-item { display: flex; flex-direction: column; gap: var(--space-1); }
.label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}
.value {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}
.ts { font-size: var(--text-sm); font-weight: 400; }
</style>