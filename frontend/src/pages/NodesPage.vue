<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import NodeTable from '@/components/nodes/NodeTable.vue'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import type { NodeListItem } from '@/api/nodes'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId!)
const { data, isLoading, refetch } = useClusterStatus(clusterId)

const nodes = computed(() => data.value?.nodes ?? [])

const selectedNode = ref<NodeListItem | null>(null)

function onSelect(node: NodeListItem) {
  selectedNode.value = node
}
function onDrawerClose() {
  selectedNode.value = null
}
</script>

<template>
  <div class="nodes-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" />
      <span>No cluster selected</span>
    </div>

    <template v-else>
      <div class="pg-header">
        <div class="section-title">Nodes
          <span class="pg-count">{{ nodes.length }}</span>
        </div>
        <Button
          icon="pi pi-refresh"
          severity="secondary"
          text
          size="small"
          :loading="isLoading"
          @click="refetch()"
          v-tooltip.left="'Refresh'"
          aria-label="Refresh nodes"
        />
      </div>

      <div v-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner" /><span>Loading nodes&hellip;</span>
      </div>

      <div v-else-if="nodes.length === 0" class="pg-empty">
        <i class="pi pi-inbox" />
        <span>No nodes registered for this cluster</span>
      </div>

      <NodeTable
        v-else
        :nodes="nodes"
        :loading="isLoading"
        :cluster-id="clusterId"
        @select="onSelect"
        @refresh="refetch()"
      />
    </template>

    <NodeDetailDrawer
      :node="selectedNode"
      :cluster-id="clusterId"
      @close="onDrawerClose"
    />
  </div>
</template>

<style scoped>
.nodes-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.pg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pg-count {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-weight: 500;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 1px 7px;
  margin-left: var(--space-2);
}

.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}

.loading-state {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-8);
  font-size: var(--text-sm);
}
</style>
