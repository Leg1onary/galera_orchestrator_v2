<!-- ТЗ раздел 10: ClusterSummaryBar + NodeCard × N + ArbitratorCard × N + EventLog -->
<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { useClusterStore } from '@/stores/cluster'
import { useEventsStore } from '@/stores/events'
import { onWsEvent } from '@/stores/ws'
import { useQueryClient } from '@tanstack/vue-query'
import ClusterSummaryBar from '@/components/overview/ClusterSummaryBar.vue'
import NodeCard from '@/components/overview/NodeCard.vue'
import ArbitratorCard from '@/components/overview/ArbitratorCard.vue'
import EventLog from '@/components/overview/EventLog.vue'

const clusterStore = useClusterStore()
const eventsStore = useEventsStore()
const queryClient = useQueryClient()

const clusterId = computed(() => clusterStore.selectedClusterId!)

// Главный запрос страницы — GET /api/clusters/{id}/status
const { data: status, isLoading, isError } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'status']),
  queryFn: () =>
      api.get(`/api/clusters/${clusterId.value}/status`).then((r) => r.data),
  refetchInterval: 10_000,
  staleTime: 5_000,
  enabled: computed(() => !!clusterId.value),
})

// WS node_state_changed → немедленная инвалидация без ожидания polling-интервала
// (глобальный handler в AppLayout.vue уже инвалидирует — этот для локального реакта)
onWsEvent((event) => {
  if (
      event.cluster_id === clusterId.value &&
      (event.event === 'node_state_changed' || event.event === 'arbitrator_state_changed')
  ) {
    queryClient.invalidateQueries({
      queryKey: ['cluster', clusterId.value, 'status'],
    })
  }
})
</script>

<template>
  <div class="overview-page">
    <!-- Загрузка -->
    <template v-if="isLoading && !status">
      <div class="loading-state">
        <ProgressSpinner style="width: 40px; height: 40px" />
        <span>Загрузка данных кластера…</span>
      </div>
    </template>

    <!-- Ошибка -->
    <template v-else-if="isError">
      <Message severity="error" :closable="false">
        Не удалось получить данные кластера. Проверьте подключение к backend.
      </Message>
    </template>

    <template v-else-if="status">
      <!-- ТЗ 10.3: ClusterSummaryBar -->
      <ClusterSummaryBar :status="status" />

      <!-- ТЗ 10.4: NodeCard × N -->
      <section class="nodes-section">
        <h2 class="section-title">Ноды</h2>
        <div class="node-grid">
          <NodeCard
              v-for="node in status.nodes"
              :key="node.id"
              :node="node"
              :cluster-id="clusterId"
          />
        </div>
      </section>

      <!-- Арбитраторы -->
      <section v-if="status.arbitrators?.length" class="arbitrators-section">
        <h2 class="section-title">Арбитраторы</h2>
        <div class="arbitrator-grid">
          <ArbitratorCard
              v-for="arb in status.arbitrators"
              :key="arb.id"
              :arbitrator="arb"
          />
        </div>
      </section>

      <!-- ТЗ 10.5: EventLog -->
      <section class="events-section">
        <div class="section-header">
          <h2 class="section-title">Event Log</h2>
          <Button
              label="Очистить"
              severity="secondary"
              size="small"
              text
              icon="pi pi-trash"
              @click="eventsStore.clear(clusterId)"
          />
        </div>
        <EventLog :entries="eventsStore.entries" :loading="eventsStore.loading" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.overview-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 4rem 0;
  color: var(--text-color-secondary);
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-color-secondary);
  margin: 0 0 0.75rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

/* ТЗ 10.4: grid для NodeCard -->
.node-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.arbitrator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}
</style>