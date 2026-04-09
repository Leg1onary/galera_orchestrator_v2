<template>
  <div class="nodes-page">
    <!-- Toolbar -->
    <div class="page-toolbar">
      <h1 class="page-title">Nodes</h1>
      <div class="toolbar-right">
        <Button
            icon="pi pi-refresh"
            text
            rounded
            size="small"
            :loading="isFetching"
            aria-label="Refresh"
            @click="refetch"
        />
      </div>
    </div>

    <!-- Lock banner: active operation in progress -->
    <div v-if="opsStore.isLocked(clusterId)" class="lock-banner">
      <i class="pi pi-lock" />
      <span>An operation is in progress — node actions are disabled until it completes.</span>
    </div>

    <!-- Table -->
    <div class="table-wrapper">
      <NodeTable
          :nodes="nodes"
          :loading="isLoading"
          :cluster-id="clusterId"
          @select="openDrawer"
          @refresh="refetch"
      />
    </div>

    <!-- Detail drawer -->
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
import NodeTable from '@/components/nodes/NodeTable.vue'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import { nodesApi, type NodeListItem } from '@/api/nodes'
import { useClusterStore } from '@/stores/cluster'
import { useOperationsStore } from '@/stores/operations'
import { onWsEvent } from '@/stores/ws'
import { useQueryClient } from '@tanstack/vue-query'

const clusterStore = useClusterStore()
const opsStore = useOperationsStore()
const queryClient = useQueryClient()

const clusterId = computed(() => clusterStore.selectedClusterId!)
const selectedNode = ref<NodeListItem | null>(null)

const { data, isLoading, isFetching, refetch } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'nodes']),
  queryFn: () => nodesApi.list(clusterId.value),
  enabled: computed(() => !!clusterId.value),
  refetchInterval: 15_000,
})

const nodes = computed(() => data.value ?? [])

function openDrawer(node: NodeListItem) {
  selectedNode.value = node
}

// Обновляем таблицу при WS событии node_state_changed (ТЗ раздел 5.2)
onWsEvent((event) => {
  if (event.event === 'node_state_changed' && event.cluster_id === clusterId.value) {
    queryClient.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes'] })
  }
})
</script>

<style scoped>
.nodes-page {
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
.page-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}
.toolbar-right { display: flex; align-items: center; gap: var(--space-2); }
.table-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.lock-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: color-mix(in oklch, var(--color-warning) 12%, transparent);
  color: var(--color-warning);
  font-size: var(--text-sm);
  border-bottom: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
  flex-shrink: 0;
}
</style>