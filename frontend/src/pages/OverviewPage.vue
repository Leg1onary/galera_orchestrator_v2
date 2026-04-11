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

const { data, isLoading, isError }               = useClusterStatus(clusterId)
const { data: logData, isLoading: isLogLoading } = useClusterLog(clusterId)

const nodes       = computed(() => data.value?.nodes       ?? [])
const arbitrators = computed(() => data.value?.arbitrators ?? [])
const events      = computed(() => logData.value           ?? [])

// fix: wsrep-поля лежат в node.live.*, не в корне NodeStatusItem
const syncedCount = computed(() =>
  nodes.value.filter((n) =>
    (n.live?.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED'
  ).length
)

// wsrep_cluster_size и flow_control — из live первой живой ноды
const firstLive = computed(() =>
  nodes.value.find((n) => n.live?.ssh_ok)?.live ?? null
)
</script>

<template>
  <div class="overview-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" />
      <span>No cluster selected</span>
    </div>

    <template v-else>

      <Message v-if="isError" severity="error" :closable="false">
        Failed to load cluster data. Check backend connection.
      </Message>

      <!-- fix: wsrep_cluster_size и flow_control_paused берём из live первой живой ноды -->
      <ClusterSummaryBar
        :total-nodes="nodes.length"
        :synced-nodes="syncedCount"
        :cluster-status="data?.status ?? null"
        :cluster-size="firstLive?.wsrep_cluster_size ?? null"
        :flow-control-paused="firstLive?.wsrep_flow_control_paused ?? null"
        :is-loading="isLoading"
      />

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

      <section class="overview-section">
        <EventLog :events="events" :is-loading="isLogLoading" :cluster-id="clusterId"/>
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
