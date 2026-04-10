<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import ClusterSummaryBar from '@/components/overview/ClusterSummaryBar.vue'
import NodeCard from '@/components/overview/NodeCard.vue'
import ArbitratorCard from '@/components/overview/ArbitratorCard.vue'
import EventLog from '@/components/overview/EventLog.vue'

const clusterStore = useClusterStore()
const clusterId = computed(() => clusterStore.selectedClusterId!)
const { data, isLoading } = useClusterStatus(clusterId)

const nodes       = computed(() => data.value?.nodes ?? [])
const arbitrators = computed(() => data.value?.arbitrators ?? [])
const events      = computed(() => data.value?.recent_events ?? [])

const syncedCount = computed(() =>
  nodes.value.filter(n => (n.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED').length
)
</script>

<template>
  <div class="overview-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" />
      <span>No cluster selected</span>
    </div>

    <template v-else>
      <!-- Summary bar -->
      <ClusterSummaryBar
        :total-nodes="nodes.length"
        :synced-nodes="syncedCount"
        :cluster-status="data?.cluster_status ?? null"
        :cluster-size="nodes[0]?.wsrep_cluster_size ?? null"
        :flow-control-paused="nodes[0]?.wsrep_flow_control_paused ?? null"
        :is-loading="isLoading"
      />

      <!-- Nodes grid -->
      <section class="overview-section">
        <div class="section-title">Nodes</div>
        <div v-if="isLoading" class="loading-state">
          <i class="pi pi-spin pi-spinner" /><span>Loading&hellip;</span>
        </div>
        <div v-else class="nodes-grid">
          <NodeCard
            v-for="node in nodes"
            :key="node.id"
            :node="node"
            :cluster-id="clusterId"
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

      <!-- Event log -->
      <section class="overview-section">
        <EventLog :events="events" :is-loading="isLoading" />
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
