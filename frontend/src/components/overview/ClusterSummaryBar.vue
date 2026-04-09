<!-- src/components/overview/ClusterSummaryBar.vue -->
<script setup lang="ts">
defineProps<{ status: any }>()
</script>
<template>
  <div class="summary-bar">
    <div class="summary-item">
      <span class="label">Статус</span>
      <Tag :severity="status.status === 'healthy' ? 'success' : status.status === 'degraded' ? 'warning' : 'danger'"
           :value="status.status" />
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
      <Tag :severity="status.primary ? 'success' : 'danger'" :value="status.primary ? 'Yes' : 'No'" />
    </div>
    <div class="summary-item">
      <span class="label">Арбитраторы</span>
      <span class="value">{{ status.online_arbitrators }} / {{ status.total_arbitrators }}</span>
    </div>
    <div class="summary-item label-ts">
      <span class="label">Обновлено</span>
      <span class="value ts">{{ new Date(status.last_update_ts).toLocaleTimeString() }}</span>
    </div>
  </div>
</template>
<style scoped>
.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  padding: 1rem 1.25rem;
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
}
.summary-item { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-color-secondary); }
.value { font-size: 0.95rem; font-weight: 600; color: var(--text-color); font-variant-numeric: tabular-nums; }
.ts { font-size: 0.8rem; font-weight: 400; }
</style>