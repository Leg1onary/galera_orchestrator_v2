<template>
  <div class="topology-page">

    <!-- Toolbar -->
    <div class="page-toolbar">
      <h1 class="page-title">Topology</h1>
      <div class="toolbar-right">
        <Button
            icon="pi pi-refresh"
            text rounded size="small"
            :loading="isFetching"
            aria-label="Refresh"
            @click="refetch"
        />
      </div>
    </div>

    <!-- Legend (ТЗ п.12.6) -->
    <div class="legend">
      <span v-for="item in LEGEND" :key="item.label" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }" />
        {{ item.label }}
      </span>
      <span class="legend-item">
        <span class="legend-arb-icon">◇</span>
        Arbitrator
      </span>
    </div>

    <!-- Canvas -->
    <div class="canvas-area">
      <div v-if="isLoading" class="state-message">Loading topology…</div>
      <div v-else-if="!topology" class="state-message">No data.</div>
      <TopologyCanvas
          v-else
          :topology="topology"
          @node-click="handleNodeClick"
      />
    </div>

    <!-- Node detail drawer -->
    <NodeDetailDrawer
        v-if="selectedNode"
        :node="selectedNode"
        :cluster-id="clusterId"
        @close="selectedNode = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import Button from 'primevue/button'
import TopologyCanvas from '@/components/topology/TopologyCanvas.vue'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import { topologyApi } from '@/api/topology'
import type { TopoNode } from '@/api/topology'
import type { NodeListItem } from '@/api/nodes'
import { useClusterStore } from '@/stores/cluster'
import { onWsEvent } from '@/stores/ws'
import { useSettingsStore } from '@/stores/settings'

const clusterStore   = useClusterStore()
const queryClient    = useQueryClient()
const settingsStore  = useSettingsStore()

// BLOCKER fix: clusterId объявлен
const clusterId = computed(() => clusterStore.clusterId)

const selectedNode = ref<NodeListItem | null>(null)

// BLOCKER fix: один LEGEND без дубля.
// Цвета по ТЗ п.7.3 + легенда по ТЗ п.12.6
const LEGEND = [
  { label: 'Synced (RW)', color: '#437a22' },   // --color-success
  { label: 'Synced (RO)', color: '#eab308' },   // yellow по ТЗ п.7.3
  { label: 'Donor/Joiner', color: '#38bdf8' },  // sky по ТЗ п.7.3 — MAJOR fix
  { label: 'Offline',      color: '#7a7974' },  // muted
] as const

const { data: topology, isLoading, isFetching, refetch } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'topology']),
  queryFn: () => {
    if (!clusterId.value) return Promise.resolve(null)
    return topologyApi.get(clusterId.value)
  },
  enabled: computed(() => !!clusterId.value),
  refetchInterval: computed(() => settingsStore.pollingIntervalSec * 1000),
})

// MAJOR fix: имена событий по ТЗ п.5.2 — без underscore
const unsubWs = onWsEvent((event) => {
  if (
      (event.event === 'nodestatechanged' || event.event === 'arbitratorstatechanged') &&
      event.cluster_id === clusterId.value
  ) {
    queryClient.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'topology'] })
  }
})

onUnmounted(() => unsubWs())

// TopoNode → NodeListItem: добавляем поля которых нет в TopoNode
function handleNodeClick(topoNode: TopoNode) {
  selectedNode.value = {
    ...topoNode,
    wsrep_flow_control_paused:   null,
    wsrep_local_recv_queue_avg:  null,
    last_error:                  null,
  } as NodeListItem
}
</script>

<style scoped>
.topology-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.page-title { font-size: var(--text-lg); font-weight: 600; }
.toolbar-right { display: flex; align-items: center; gap: var(--space-2); }

.legend {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-2) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-arb-icon { font-size: 12px; color: var(--color-text-muted); }

.canvas-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}
.state-message {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>