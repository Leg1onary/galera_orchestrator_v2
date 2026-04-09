<!-- src/components/overview/NodeCard.vue -->
<!-- ТЗ 7.3: цвет по состоянию. ТЗ 10.4: кнопки действий -->
<script setup lang="ts">
import { computed } from 'vue'
import { api } from '@/api/client'
import { useQueryClient } from '@tanstack/vue-query'

const props = defineProps<{ node: any; clusterId: number }>()
const queryClient = useQueryClient()

// ТЗ 7.3: цветовая индикация
const stateColor = computed(() => {
  const s = props.node
  if (!s.ssh_ok || s.wsrep_local_state_comment === 'OFFLINE') return '#ef4444'
  if (s.wsrep_ready === 'OFF') return '#f97316'
  if (s.wsrep_local_state_comment === 'Synced' && s.readonly) return '#eab308'
  if (['Donor/Desynced', 'Joiner'].includes(s.wsrep_local_state_comment)) return '#38bdf8'
  if (s.wsrep_local_state_comment === 'Synced') return '#22c55e'
  return '#94a3b8'
})

async function runAction(action: string) {
  await api.post(`/api/clusters/${props.clusterId}/nodes/${props.node.id}/actions`, { action })
  queryClient.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'status'] })
}
</script>
<template>
  <div class="node-card" :style="{ '--state-color': stateColor }">
    <div class="node-header">
      <span class="state-dot" />
      <span class="node-name">{{ node.name }}</span>
      <span class="node-host">{{ node.host }}:{{ node.port }}</span>
    </div>
    <div class="node-metrics">
      <div class="metric"><span class="mk">State</span><span class="mv">{{ node.wsrep_local_state_comment ?? '—' }}</span></div>
      <div class="metric"><span class="mk">Cluster size</span><span class="mv">{{ node.wsrep_cluster_size ?? '—' }}</span></div>
      <div class="metric"><span class="mk">Flow ctrl</span><span class="mv">{{ node.wsrep_flow_control_paused ?? '—' }}</span></div>
      <div class="metric"><span class="mk">Recv queue</span><span class="mv">{{ node.wsrep_local_recv_queue ?? '—' }}</span></div>
      <div class="metric"><span class="mk">Mode</span><span class="mv">{{ node.readonly ? 'RO' : 'RW' }}</span></div>
    </div>
    <div class="node-actions">
      <Button size="small" text label="Start"   @click="runAction('start')" />
      <Button size="small" text label="Stop"    @click="runAction('stop')" severity="danger" />
      <Button size="small" text label="Restart" @click="runAction('restart')" severity="warning" />
      <Button size="small" text label="RO"      @click="runAction('set-readonly')" />
      <Button size="small" text label="RW"      @click="runAction('set-readwrite')" />
    </div>
  </div>
</template>
<style scoped>
.node-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-left: 3px solid var(--state-color);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.node-header { display: flex; align-items: center; gap: 0.5rem; }
.state-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--state-color); flex-shrink: 0; }
.node-name { font-weight: 600; font-size: 0.9rem; }
.node-host { font-size: 0.75rem; color: var(--text-color-secondary); margin-left: auto; }
.node-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }
.metric { display: flex; justify-content: space-between; font-size: 0.78rem; }
.mk { color: var(--text-color-secondary); }
.mv { font-variant-numeric: tabular-nums; font-weight: 500; }
.node-actions { display: flex; flex-wrap: wrap; gap: 4px; border-top: 1px solid var(--surface-border); padding-top: 0.5rem; }
</style>