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

    <!-- Legend -->
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
      <div v-else-if="!topology" class="state-message text-muted-color">No data.</div>
      <TopologyCanvas
          v-else
          :topology="topology"
          @node-click="selectedNode = $event"
      />
    </div>

    <!-- Node detail mini-drawer (reuse NodeDetailDrawer) -->
    <NodeDetailDrawer
        :node="selectedNode"
        :cluster-id="clusterId"
        @close="selectedNode = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Button } from 'primevue'
import TopologyCanvas from '@/components/topology/TopologyCanvas.vue'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import { topologyApi } from '@/api/topology'
import type { TopoNode } from '@/api/topology'
import { useClusterStore } from '@/stores/cluster'
import { onWsEvent } from '@/stores/ws'
import { useQueryClient } from '@tanstack/vue-query'

const clusterStore = useClusterStore()
const queryClient = useQueryClient()
const clusterId = computed(() => clusterStore.selectedClusterId!)
const selectedNode = ref<TopoNode | null>(null)

const { data: topology, isLoading, isFetching, refetch } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'topology']),
  queryFn: () => topologyApi.get(clusterId.value),
  enabled: computed(() => !!clusterId.value),
  refetchInterval: 15_000,
})

// WS инвалидация — те же события что и Nodes
onWsEvent((event) => {
  if (
      (event.event === 'node_state_changed' || event.event === 'arbitrator_state_changed') &&
      event.cluster_id === clusterId.value
  ) {
    queryClient.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'topology'] })
  }
})

const LEGEND = [
  { label: 'Synced',         color: '#437a22' },
  { label: 'Donor/Desynced', color: '#006494' },
  { label: 'Joining',        color: '#d19900' },
  { label: 'Error',          color: '#a12c7b' },
  { label: 'Offline',        color: '#7a7974' },
]
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
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.legend-dot {
  width: 8px; height: 8px;
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