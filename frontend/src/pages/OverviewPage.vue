<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import { useClusterLog } from '@/composables/useClusterLog'
import ClusterSummaryBar from '@/components/overview/ClusterSummaryBar.vue'
import AdvisorWidget from '@/components/overview/AdvisorWidget.vue'
import NodeCard from '@/components/overview/NodeCard.vue'
import NodeCardSkeleton from '@/components/overview/NodeCardSkeleton.vue'
import ArbitratorCard from '@/components/overview/ArbitratorCard.vue'
import EventLog from '@/components/overview/EventLog.vue'
import ReplicationLagAlert from '@/components/overview/ReplicationLagAlert.vue'
import QuorumHealthWidget  from '@/components/overview/QuorumHealthWidget.vue'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

const { data, isLoading, isError }               = useClusterStatus(clusterId)
const { data: logData, isLoading: isLogLoading } = useClusterLog(clusterId)

const nodes       = computed(() => data.value?.nodes       ?? [])
const arbitrators = computed(() => data.value?.arbitrators ?? [])
const events      = computed(() => logData.value           ?? [])

const syncedCount = computed(() =>
  nodes.value.filter((n) =>
    (n.live?.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED'
  ).length
)

const maintenanceCount = computed(() =>
  nodes.value.filter((n) => n.maintenance).length
)

const firstLive = computed(() =>
  nodes.value.find((n) => n.live?.ssh_ok)?.live ?? null
)

const maxRecvQueue = computed(() => {
  const values = nodes.value
    .map((n) => n.live?.wsrep_local_recv_queue ?? null)
    .filter((v): v is number => v !== null)
  return values.length ? Math.max(...values) : null
})
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

      <ClusterSummaryBar
        :total-nodes="nodes.length"
        :synced-nodes="syncedCount"
        :cluster-status="data?.status ?? null"
        :cluster-size="firstLive?.wsrep_cluster_size ?? null"
        :flow-control-paused="firstLive?.wsrep_flow_control_paused ?? null"
        :maintenance-nodes="maintenanceCount"
        :max-recv-queue="maxRecvQueue"
        :cluster-id="clusterId!"
        :is-loading="isLoading"
      />

      <AdvisorWidget />

      <QuorumHealthWidget :cluster-id="clusterId" />

      <ReplicationLagAlert :nodes="nodes" />

      <section class="overview-section anim-fade-in">
        <div class="section-header">
          <span class="section-title">Nodes</span>
          <span class="section-count">{{ nodes.length }}</span>
        </div>
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

      <section v-if="arbitrators.length" class="overview-section anim-fade-in">
        <div class="section-header">
          <span class="section-title">Arbitrators</span>
          <span class="section-count">{{ arbitrators.length }}</span>
        </div>
        <div class="arb-grid">
          <ArbitratorCard
            v-for="arb in arbitrators"
            :key="arb.id"
            :arbitrator="arb"
          />
        </div>
      </section>

      <section class="overview-section anim-fade-in">
        <EventLog :events="events" :is-loading="isLogLoading" :cluster-id="clusterId!"/>
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

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.section-count {
  font-size: var(--text-xs);
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 3px 10px;
  line-height: 1.6;
  min-width: 22px;
  text-align: center;
}

.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-4);
}

.arb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-4);
}
</style>
