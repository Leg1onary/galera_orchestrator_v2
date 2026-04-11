<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import { useClusterLog } from '@/composables/useClusterLog'
import ClusterSummaryBar from '@/components/overview/ClusterSummaryBar.vue'
import NodeCard from '@/components/overview/NodeCard.vue'
import NodeCardSkeleton from '@/components/overview/NodeCardSkeleton.vue'
import ArbitratorCard from '@/components/overview/ArbitratorCard.vue'
import EventLog from '@/components/overview/EventLog.vue'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

// ТЗ п.10.1: два отдельных запроса — status и log
const { data, isLoading, isError }           = useClusterStatus(clusterId)
const { data: logData, isLoading: isLogLoading } = useClusterLog(clusterId)

const nodes       = computed(() => data.value?.nodes ?? [])
const arbitrators = computed(() => data.value?.arbitrators ?? [])
const events      = computed(() => logData.value ?? [])

const syncedCount = computed(() =>
  nodes.value.filter((n) =>
    (n.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED'
  ).length
)
</script>

<template>
  <div class="overview-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" />
      <span>No cluster selected</span>
    </div>

    <template v-else>

      <!-- Error -->
      <Message v-if="isError" severity="error" :closable="false">
        Failed to load cluster data. Check backend connection.
      </Message>

      <!-- Summary bar (shows inline skeletons while loading) -->
      <ClusterSummaryBar
        :total-nodes="nodes.length"
        :synced-nodes="syncedCount"
        :cluster-status="data?.status ?? null"
        :cluster-size="nodes[0]?.wsrep_cluster_size ?? null"
        :flow-control-paused="nodes[0]?.wsrep_flow_control_paused ?? null"
        :is-loading="isLoading"
      />

      <!-- Nodes -->
      <section class="overview-section">
        <div class="section-title">Nodes</div>
        <div class="nodes-grid">
          <template v-if="isLoading">
            <NodeCardSkeleton v-for="i in 3" :key="'sk-' + i" />
          </template>
          <NodeCard
            v-else
            v-for="node in nodes"
            :key="node.id"
            :node="node"
            :cluster-id="clusterId!"
          />
        </div>
      </section>

      <!-- Arbitrators -->
      <section v-if="arbitrators.length" class="overview-section">
        <div class="section-title">Arbitrators</div>
        <div class="arb-grid">
          <ArbitratorCard
            v-for="arb in arbitrators"
            :key="arb.id"
            :arbitrator="arb"
          />
        </div>
      </section>

      <!-- Event log — отдельный запрос GET /api/clusters/{id}/log (ТЗ п.10.1) -->
      <section class="overview-section">
        <EventLog :events="events" :is-loading="isLogLoading" />
      </section>

    </template>
  </div>
</template>

<style scoped>
.overview-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
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
.overview-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}
.arb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-4);
}
</style>
